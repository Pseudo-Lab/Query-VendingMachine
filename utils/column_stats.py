"""
컬럼 값 분포 분석 에이전트 모듈

각 테이블의 컬럼별 값 분포, 통계 정보를 수집하여 딕셔너리로 저장합니다.
pickle 파일로 저장하여 프롬프트에 활용합니다.
"""
import pickle
import os
from typing import Dict, Any, List
from utils.db_utils import run_query, make_table_desc_dict
from utils.logging_utils import log_step


# ============================================================
# 컬럼 타입 판별 헬퍼
# ============================================================

NUMERIC_TYPES = ["integer", "smallint", "bigint", "numeric", "real", "double precision", "decimal"]
TEXT_TYPES = ["character varying", "text", "character", "varchar", "char"]
DATE_TYPES = ["timestamp", "timestamp without time zone", "timestamp with time zone", "date", "time"]


def is_numeric(data_type: str) -> bool:
    return any(t in data_type.lower() for t in NUMERIC_TYPES)


def is_text(data_type: str) -> bool:
    return any(t in data_type.lower() for t in TEXT_TYPES)


def is_date(data_type: str) -> bool:
    return any(t in data_type.lower() for t in DATE_TYPES)


# ============================================================
# 컬럼 메타정보 수집
# ============================================================

def get_column_meta(table_name: str, column_name: str, data_type: str) -> Dict[str, Any]:
    """
    단일 컬럼의 메타정보 수집

    Args:
        table_name: 테이블명
        column_name: 컬럼명
        data_type: 데이터 타입

    Returns:
        Dict: 컬럼 메타정보
    """
    meta = {
        "column_name": column_name,
        "data_type": data_type,
        "is_likely_id": False,
        "is_categorical": False,
    }

    try:
        # 1. 기본 통계
        basic_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT({column_name}) as non_null_count,
                COUNT(DISTINCT {column_name}) as distinct_count
            FROM {table_name};
        """
        basic_result = run_query(basic_query, dvd=True)
        if basic_result:
            meta["total_count"] = basic_result[0]["total_count"]
            meta["non_null_count"] = basic_result[0]["non_null_count"]
            meta["distinct_count"] = basic_result[0]["distinct_count"]
            meta["null_count"] = meta["total_count"] - meta["non_null_count"]
            
            # ID 컬럼 판별: distinct == total이고 null 없음
            if meta["distinct_count"] == meta["total_count"] and meta["null_count"] == 0:
                meta["is_likely_id"] = True

        # 2. 데이터 타입별 추가 통계
        if is_numeric(data_type):
            meta.update(_get_numeric_stats(table_name, column_name))
            
        elif is_text(data_type):
            meta.update(_get_text_stats(table_name, column_name, meta.get("distinct_count", 0)))
            
        elif is_date(data_type):
            meta.update(_get_date_stats(table_name, column_name))

    except Exception as e:
        meta["error"] = str(e)

    return meta


def _get_numeric_stats(table_name: str, column_name: str) -> Dict[str, Any]:
    """수치형 컬럼 통계"""
    stats = {}
    
    # 기본 통계
    query = f"""
        SELECT 
            MIN({column_name}) as min_value,
            MAX({column_name}) as max_value,
            AVG({column_name})::numeric(15,2) as avg_value,
            STDDEV({column_name})::numeric(15,2) as stddev_value
        FROM {table_name}
        WHERE {column_name} IS NOT NULL;
    """
    result = run_query(query, dvd=True)
    if result and result[0]["min_value"] is not None:
        stats["min"] = result[0]["min_value"]
        stats["max"] = result[0]["max_value"]
        stats["avg"] = float(result[0]["avg_value"]) if result[0]["avg_value"] else None
        stats["stddev"] = float(result[0]["stddev_value"]) if result[0]["stddev_value"] else None
    
    # 최빈값 Top 5
    freq_query = f"""
        SELECT {column_name} as value, COUNT(*) as freq
        FROM {table_name}
        WHERE {column_name} IS NOT NULL
        GROUP BY {column_name}
        ORDER BY freq DESC
        LIMIT 5;
    """
    freq_result = run_query(freq_query, dvd=True)
    if freq_result:
        stats["top_values"] = [
            {"value": r["value"], "freq": r["freq"]} 
            for r in freq_result
        ]
    
    return stats


def _get_text_stats(table_name: str, column_name: str, distinct_count: int) -> Dict[str, Any]:
    """문자형 컬럼 통계"""
    stats = {}
    
    # 문자열 길이 통계
    len_query = f"""
        SELECT 
            MIN(LENGTH({column_name})) as min_length,
            MAX(LENGTH({column_name})) as max_length,
            AVG(LENGTH({column_name}))::numeric(10,1) as avg_length
        FROM {table_name}
        WHERE {column_name} IS NOT NULL;
    """
    len_result = run_query(len_query, dvd=True)
    if len_result and len_result[0]["min_length"] is not None:
        stats["min_length"] = len_result[0]["min_length"]
        stats["max_length"] = len_result[0]["max_length"]
        stats["avg_length"] = float(len_result[0]["avg_length"]) if len_result[0]["avg_length"] else None
    
    # 카디널리티에 따라 다르게 처리
    if distinct_count <= 50:
        # 낮은 카디널리티: 전체 값 나열 (categorical)
        stats["is_categorical"] = True
        all_query = f"""
            SELECT DISTINCT {column_name} as value
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            ORDER BY {column_name}
            LIMIT 100;
        """
        all_result = run_query(all_query, dvd=True)
        stats["all_values"] = [r["value"] for r in all_result]
        
        # 빈도도 함께
        freq_query = f"""
            SELECT {column_name} as value, COUNT(*) as freq
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            GROUP BY {column_name}
            ORDER BY freq DESC;
        """
        freq_result = run_query(freq_query, dvd=True)
        stats["value_counts"] = {r["value"]: r["freq"] for r in freq_result}
        
    else:
        # 높은 카디널리티: 샘플 + 최빈값
        stats["is_categorical"] = False
        
        # 샘플 20개
        sample_query = f"""
            SELECT DISTINCT {column_name} as value
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            ORDER BY {column_name}
            LIMIT 20;
        """
        sample_result = run_query(sample_query, dvd=True)
        stats["sample_values"] = [r["value"] for r in sample_result]
        
        # 최빈값 Top 10
        freq_query = f"""
            SELECT {column_name} as value, COUNT(*) as freq
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            GROUP BY {column_name}
            ORDER BY freq DESC
            LIMIT 10;
        """
        freq_result = run_query(freq_query, dvd=True)
        stats["top_values"] = [
            {"value": r["value"], "freq": r["freq"]} 
            for r in freq_result
        ]
    
    return stats


def _get_date_stats(table_name: str, column_name: str) -> Dict[str, Any]:
    """날짜형 컬럼 통계"""
    stats = {}
    
    query = f"""
        SELECT 
            MIN({column_name}) as min_date,
            MAX({column_name}) as max_date
        FROM {table_name}
        WHERE {column_name} IS NOT NULL;
    """
    result = run_query(query, dvd=True)
    if result and result[0]["min_date"] is not None:
        stats["min_date"] = str(result[0]["min_date"])
        stats["max_date"] = str(result[0]["max_date"])
        
        # 기간 계산 (일 단위)
        if result[0]["min_date"] and result[0]["max_date"]:
            try:
                from datetime import datetime
                min_dt = result[0]["min_date"]
                max_dt = result[0]["max_date"]
                if hasattr(min_dt, 'date'):
                    min_dt = min_dt.date()
                    max_dt = max_dt.date()
                stats["date_range_days"] = (max_dt - min_dt).days
            except:
                pass
    
    return stats


# ============================================================
# 테이블 단위 수집
# ============================================================

def get_table_meta(table_name: str) -> Dict[str, Any]:
    """
    테이블의 모든 컬럼 메타정보 수집

    Args:
        table_name: 테이블명

    Returns:
        Dict: 테이블 메타정보
    """
    log_step(f"📊 테이블 분석: {table_name}")

    # 컬럼 정보 조회
    columns_query = f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = '{table_name}'
        ORDER BY ordinal_position;
    """
    columns = run_query(columns_query, dvd=True)

    table_meta = {
        "table_name": table_name,
        "column_count": len(columns),
        "columns": {}
    }

    for col in columns:
        col_name = col["column_name"]
        data_type = col["data_type"]
        table_meta["columns"][col_name] = get_column_meta(table_name, col_name, data_type)

    # 테이블 전체 행 수
    count_result = run_query(f"SELECT COUNT(*) as cnt FROM {table_name};", dvd=True)
    if count_result:
        table_meta["row_count"] = count_result[0]["cnt"]

    return table_meta


# ============================================================
# 전체 수집 및 저장/로드
# ============================================================

def collect_all_tables_meta() -> Dict[str, Dict]:
    """
    모든 테이블의 메타정보 수집

    Returns:
        Dict: {테이블명: 테이블메타정보} 딕셔너리
    """
    log_step("🚀 전체 테이블 메타정보 수집 시작")

    tables = make_table_desc_dict()
    all_meta = {}

    for table_name in tables.keys():
        all_meta[table_name] = get_table_meta(table_name)

    log_step("✅ 전체 테이블 메타정보 수집 완료", {"테이블_수": len(all_meta)})

    return all_meta


def save_meta_to_pickle(meta: Dict, filepath: str):
    """
    메타정보를 pickle 파일로 저장

    Args:
        meta: 메타정보 딕셔너리
        filepath: 저장 경로
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        pickle.dump(meta, f)
    log_step(f"💾 메타정보 저장 완료: {filepath}")


def load_meta_from_pickle(filepath: str) -> Dict:
    """
    pickle 파일에서 메타정보 로드

    Args:
        filepath: 파일 경로

    Returns:
        Dict: 메타정보 딕셔너리
    """
    with open(filepath, "rb") as f:
        return pickle.load(f)


# ============================================================
# 프롬프트 포맷팅
# ============================================================

def format_table_meta_for_prompt(table_name: str, table_meta: Dict) -> str:
    """
    프롬프트에 사용할 테이블 메타정보 문자열 생성

    Args:
        table_name: 테이블명
        table_meta: 테이블 메타정보

    Returns:
        str: 포맷팅된 메타정보 문자열
    """
    lines = [f"=== {table_name} ({table_meta.get('row_count', '?')} rows) ==="]
    
    for col_name, col_meta in table_meta.get("columns", {}).items():
        dtype = col_meta.get("data_type", "unknown")
        distinct = col_meta.get("distinct_count", "?")
        
        # 기본 정보
        parts = [f"{col_name} ({dtype})"]
        parts.append(f"distinct={distinct}")
        
        # ID 컬럼 표시
        if col_meta.get("is_likely_id"):
            parts.append("[ID]")
        
        # 수치형: 범위
        if "min" in col_meta and "max" in col_meta:
            parts.append(f"range=[{col_meta['min']}~{col_meta['max']}]")
        
        # 날짜형: 기간
        if "min_date" in col_meta:
            parts.append(f"period=[{col_meta['min_date'][:10]}~{col_meta['max_date'][:10]}]")
        
        # 문자형: 값 정보
        if col_meta.get("is_categorical") and "all_values" in col_meta:
            vals = col_meta["all_values"]
            if len(vals) <= 10:
                parts.append(f"values={vals}")
            else:
                parts.append(f"values={vals[:10]}... (+{len(vals)-10} more)")
        elif "top_values" in col_meta:
            top = [v["value"] for v in col_meta["top_values"][:5]]
            parts.append(f"top={top}")
        elif "sample_values" in col_meta:
            parts.append(f"samples={col_meta['sample_values'][:5]}")
        
        lines.append("  - " + ", ".join(parts))
    
    return "\n".join(lines)


def format_tables_meta_for_prompt(table_names: List[str], all_meta: Dict) -> str:
    """
    여러 테이블의 메타정보를 프롬프트용 문자열로 포맷팅

    Args:
        table_names: 테이블명 리스트
        all_meta: 전체 메타정보 딕셔너리

    Returns:
        str: 포맷팅된 메타정보 문자열
    """
    formatted = []
    for table_name in table_names:
        if table_name in all_meta:
            formatted.append(format_table_meta_for_prompt(table_name, all_meta[table_name]))
    return "\n\n".join(formatted)


# ============================================================
# 하위 호환성 (기존 함수명 유지)
# ============================================================

# 기존 함수명 별칭
get_column_stats = get_column_meta
get_table_column_stats = get_table_meta
collect_all_table_stats = collect_all_tables_meta
format_column_stats_for_prompt = format_table_meta_for_prompt


def save_stats_to_json(stats: Dict, filepath: str):
    """JSON 저장 (하위 호환)"""
    import json
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False, default=str)


def load_stats_from_json(filepath: str) -> Dict:
    """JSON 로드 (하위 호환)"""
    import json
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

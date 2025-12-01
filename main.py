import streamlit as st
import pandas as pd
import os
import time

# LangChain 모듈 임포트
from chains.text_to_sql_chain import invoke_text_to_sql_chain
from chains.text_to_sql_chain import create_text_to_sql_chain
from chains.v_mungyu.maple_repair import create_maple_repair_chain
from chains.v_mungyu.epi_sql import create_epi_sql_chain
from chains.v_mungyu.alpha_sql import create_alpha_sql_chain
from experiments.experiment_1.run import run as ex1_run
from utils import run_query, log_step


def main():
    st.title("📝 Text2SQL Demo with LangChain")

    tabs = st.tabs(["Text2SQL", "실험결과 1", "4-Way 비교"])

    with tabs[0]:
        natural_query = st.text_input(
            "Enter your question:",
            "List the title and release year of movies.",
        )

        if st.button("Run", key="run_text2sql"):
            try:
                log_step("🎯 사용자 요청 시작")
                sql = invoke_text_to_sql_chain(natural_query)
                log_step("Step 6: SQL 정리 완료", {"정리된_SQL": sql})
                st.code(sql, language="sql")

                try:
                    log_step("Step 7: SQL 쿼리 실행 중...", {"SQL": sql})
                    rows = run_query(query=sql, dvd=True)
                    df = pd.DataFrame(rows)
                    log_step("Step 8: 쿼리 실행 완료", {
                        "반환된_행_수": len(rows),
                        "컬럼_수": len(df.columns),
                        "컬럼명": list(df.columns),
                    })
                    st.dataframe(df)
                    log_step("✅ 전체 파이프라인 완료", {
                        "최종_결과_행수": len(rows),
                        "처리_상태": "성공",
                    })
                    st.session_state["experiment_result"] = df
                except Exception as e:
                    log_step("❌ 쿼리 실행 오류 발생", {
                        "에러_타입": type(e).__name__,
                        "에러_메시지": str(e),
                    })
                    st.error(f"Error running query: {e}")
            except Exception as e:
                log_step("❌ SQL 생성 오류 발생", {
                    "에러_타입": type(e).__name__,
                    "에러_메시지": str(e),
                })
                st.error(f"Error generating SQL: {e}")

    with tabs[1]:
        st.header("실험결과_1")
        st.write(": 기본 스키마 + 테이블 요약 --> RAG 유사 문서 n개 검색 --> 프롬프트 생성 --> SQL 생성 --> 실행")
        csv_path = "experiments/experiment_1/result.csv"

        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if "experiment_1" not in st.session_state:
                st.session_state["experiment_1"] = df
            st.dataframe(st.session_state["experiment_1"])
        else:
            st.info("아직 실험 결과가 없습니다.")
            if st.button("실험 실행하기"):
                df = ex1_run()
                st.session_state["experiment_1"] = df
                st.dataframe(st.session_state["experiment_1"])

        st.subheader("Base vs MapleRepair 비교")
        testset_csv = "experiments/dvdrental_testset.csv"
        if not os.path.exists(testset_csv):
            st.warning("테스트셋이 없습니다. 터미널에서 'docker exec text2sql-web python /app/testset.py' 실행 후 다시 시도하세요.")
        else:
            if st.button("비교 실행", key="run_compare"):
                df = pd.read_csv(testset_csv)
                base_chain = create_text_to_sql_chain()
                maple_chain = create_maple_repair_chain()
                records = []
                b_ok = 0
                m_ok = 0
                progress = st.progress(0)
                total = len(df)

                def _scalar(rows):
                    if not rows:
                        return None
                    r = rows[0]
                    if isinstance(r, dict):
                        return list(r.values())[0] if r else None
                    return r[0] if len(r) > 0 else None

                def _match(expected, actual):
                    try:
                        # 숫자 비교: 소수점 2자리로 반올림하여 비교
                        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                            return round(float(expected), 2) == round(float(actual), 2)
                        # 문자열을 숫자로 변환 가능한 경우
                        try:
                            exp_num = float(str(expected).strip())
                            act_num = float(str(actual).strip())
                            return round(exp_num, 2) == round(act_num, 2)
                        except (ValueError, TypeError):
                            pass
                        # 문자열 비교
                        return str(expected).strip().lower() == str(actual).strip().lower()
                    except Exception:
                        return str(expected) == str(actual)

                for idx, row in df.iterrows():
                    q = row["question"]
                    label = row["label"]
                    b_sql = base_chain.invoke(q)
                    try:
                        b_rows = run_query(b_sql, dvd=True)
                        b_val = _scalar(b_rows)
                        b_match = _match(label, b_val)
                    except Exception as e:
                        b_val = None
                        b_match = False
                    if b_match:
                        b_ok += 1

                    m_sql = maple_chain.invoke(q)
                    try:
                        m_rows = run_query(m_sql, dvd=True)
                        m_val = _scalar(m_rows)
                        m_match = _match(label, m_val)
                    except Exception as e:
                        m_val = None
                        m_match = False
                    if m_match:
                        m_ok += 1

                    records.append({
                        "question": q,
                        "expected": str(label),
                        "base_sql": b_sql,
                        "base_result": str(b_val) if b_val is not None else "",
                        "base_match": b_match,
                        "maple_sql": m_sql,
                        "maple_result": str(m_val) if m_val is not None else "",
                        "maple_match": m_match,
                    })
                    progress.progress(int((idx + 1) / total * 100))
                    time.sleep(0.1)

                base_acc = b_ok / total * 100 if total else 0
                maple_acc = m_ok / total * 100 if total else 0
                st.metric("Base EX", f"{base_acc:.2f}%", None)
                st.metric("MapleRepair EX", f"{maple_acc:.2f}%", None)
                out_df = pd.DataFrame(records)
                st.dataframe(out_df)
                st.session_state["compare_results"] = out_df

    with tabs[2]:
        st.header("4-Way 비교: Base vs MapleRepair vs EPI-SQL vs Alpha-SQL")
        st.write("""네 가지 방법론의 성능을 비교합니다:
        - **Base**: 기본 RAG 기반 Text2SQL
        - **MapleRepair**: 에러 탐지 및 수정 (사후)
        - **EPI-SQL**: 에러 예방 지침 (사전)
        - **Alpha-SQL**: MCTS 기반 탐색
        """)
        
        testset_csv = "experiments/dvdrental_testset.csv"
        if not os.path.exists(testset_csv):
            st.warning("테스트셋이 없습니다. 터미널에서 'docker exec text2sql-web python /app/testset.py' 실행 후 다시 시도하세요.")
        else:
            if st.button("4-Way 비교 실행", key="run_4way"):
                df = pd.read_csv(testset_csv)
                
                # 체인 생성
                base_chain = create_text_to_sql_chain()
                maple_chain = create_maple_repair_chain()
                epi_chain = create_epi_sql_chain()
                alpha_chain = create_alpha_sql_chain(n_candidates=3)
                
                records = []
                counts = {"base": 0, "maple": 0, "epi": 0, "alpha": 0}
                progress = st.progress(0)
                status_text = st.empty()
                total = len(df)

                def _scalar(rows):
                    if not rows:
                        return None
                    r = rows[0]
                    if isinstance(r, dict):
                        return list(r.values())[0] if r else None
                    return r[0] if len(r) > 0 else None

                def _match(expected, actual):
                    try:
                        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                            return round(float(expected), 2) == round(float(actual), 2)
                        try:
                            exp_num = float(str(expected).strip())
                            act_num = float(str(actual).strip())
                            return round(exp_num, 2) == round(act_num, 2)
                        except (ValueError, TypeError):
                            pass
                        return str(expected).strip().lower() == str(actual).strip().lower()
                    except Exception:
                        return str(expected) == str(actual)

                for idx, row in df.iterrows():
                    q = row["question"]
                    label = row["label"]
                    status_text.text(f"처리 중: {idx+1}/{total} - {q[:50]}...")
                    
                    result = {"question": q, "expected": str(label)}
                    
                    # Base
                    try:
                        b_sql = base_chain.invoke(q)
                        b_rows = run_query(b_sql, dvd=True)
                        b_val = _scalar(b_rows)
                        b_match = _match(label, b_val)
                        if b_match:
                            counts["base"] += 1
                        result["base_sql"] = b_sql
                        result["base_result"] = str(b_val) if b_val is not None else ""
                        result["base_match"] = b_match
                    except Exception as e:
                        result["base_sql"] = "ERROR"
                        result["base_result"] = str(e)[:50]
                        result["base_match"] = False

                    # MapleRepair
                    try:
                        m_sql = maple_chain.invoke(q)
                        m_rows = run_query(m_sql, dvd=True)
                        m_val = _scalar(m_rows)
                        m_match = _match(label, m_val)
                        if m_match:
                            counts["maple"] += 1
                        result["maple_sql"] = m_sql
                        result["maple_result"] = str(m_val) if m_val is not None else ""
                        result["maple_match"] = m_match
                    except Exception as e:
                        result["maple_sql"] = "ERROR"
                        result["maple_result"] = str(e)[:50]
                        result["maple_match"] = False

                    # EPI-SQL
                    try:
                        e_sql = epi_chain.invoke(q)
                        e_rows = run_query(e_sql, dvd=True)
                        e_val = _scalar(e_rows)
                        e_match = _match(label, e_val)
                        if e_match:
                            counts["epi"] += 1
                        result["epi_sql"] = e_sql
                        result["epi_result"] = str(e_val) if e_val is not None else ""
                        result["epi_match"] = e_match
                    except Exception as e:
                        result["epi_sql"] = "ERROR"
                        result["epi_result"] = str(e)[:50]
                        result["epi_match"] = False

                    # Alpha-SQL
                    try:
                        a_sql = alpha_chain.invoke(q)
                        a_rows = run_query(a_sql, dvd=True)
                        a_val = _scalar(a_rows)
                        a_match = _match(label, a_val)
                        if a_match:
                            counts["alpha"] += 1
                        result["alpha_sql"] = a_sql
                        result["alpha_result"] = str(a_val) if a_val is not None else ""
                        result["alpha_match"] = a_match
                    except Exception as e:
                        result["alpha_sql"] = "ERROR"
                        result["alpha_result"] = str(e)[:50]
                        result["alpha_match"] = False

                    records.append(result)
                    progress.progress(int((idx + 1) / total * 100))

                status_text.text("완료!")
                
                # 결과 표시
                st.subheader("📊 Execution Accuracy (EX) 비교")
                cols = st.columns(4)
                
                base_acc = counts["base"] / total * 100 if total else 0
                maple_acc = counts["maple"] / total * 100 if total else 0
                epi_acc = counts["epi"] / total * 100 if total else 0
                alpha_acc = counts["alpha"] / total * 100 if total else 0
                
                with cols[0]:
                    st.metric("Base", f"{base_acc:.2f}%", None)
                with cols[1]:
                    delta_m = f"+{maple_acc - base_acc:.2f}%" if maple_acc > base_acc else f"{maple_acc - base_acc:.2f}%"
                    st.metric("MapleRepair", f"{maple_acc:.2f}%", delta_m)
                with cols[2]:
                    delta_e = f"+{epi_acc - base_acc:.2f}%" if epi_acc > base_acc else f"{epi_acc - base_acc:.2f}%"
                    st.metric("EPI-SQL", f"{epi_acc:.2f}%", delta_e)
                with cols[3]:
                    delta_a = f"+{alpha_acc - base_acc:.2f}%" if alpha_acc > base_acc else f"{alpha_acc - base_acc:.2f}%"
                    st.metric("Alpha-SQL", f"{alpha_acc:.2f}%", delta_a)
                
                # 상세 결과 테이블
                st.subheader("📋 상세 결과")
                out_df = pd.DataFrame(records)
                st.dataframe(out_df)
                
                # CSV 저장
                csv_output = "experiments/4way_comparison_result.csv"
                out_df.to_csv(csv_output, index=False, encoding="utf-8-sig")
                st.success(f"결과가 {csv_output}에 저장되었습니다.")
                
                st.session_state["4way_results"] = out_df


if __name__ == "__main__":
    main()
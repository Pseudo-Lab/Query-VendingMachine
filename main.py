import streamlit as st
import pandas as pd
import os

# LangChain 모듈 임포트
from chains.text_to_sql_chain import invoke_text_to_sql_chain, get_prompt_preview
from experiments.experiment_1.run import run as ex1_run
from experiments.experiment_2.run import run as ex2_run
from experiments.experiment_3.run import run as ex3_run
from experiments.experiment_4.run import run as ex4_run
from utils import run_query, log_step


def calculate_accuracy(df: pd.DataFrame) -> dict:
    """
    실험 결과 DataFrame에서 정확도 계산
    
    Args:
        df: label과 infer 컬럼이 있는 DataFrame
    
    Returns:
        dict: 정확도 정보 (correct, total, accuracy)
    """
    if "label" not in df.columns or "infer" not in df.columns:
        return {"correct": 0, "total": 0, "accuracy": 0.0}
    
    # 문자열로 변환하여 비교 (타입 불일치 방지)
    df = df.copy()
    df["label_str"] = df["label"].astype(str).str.strip()
    df["infer_str"] = df["infer"].astype(str).str.strip()
    
    # 정답 비교
    df["is_correct"] = df["label_str"] == df["infer_str"]
    
    correct = df["is_correct"].sum()
    total = len(df)
    accuracy = (correct / total * 100) if total > 0 else 0.0
    
    return {
        "correct": int(correct),
        "total": int(total),
        "accuracy": round(accuracy, 2)
    }


def get_wrong_answers(df: pd.DataFrame) -> pd.DataFrame:
    """틀린 문제들만 추출"""
    if "label" not in df.columns or "infer" not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df["label_str"] = df["label"].astype(str).str.strip()
    df["infer_str"] = df["infer"].astype(str).str.strip()
    df["is_correct"] = df["label_str"] == df["infer_str"]
    
    wrong_df = df[~df["is_correct"]][["question", "label", "infer", "infer_sql"]].copy()
    wrong_df.columns = ["질문", "정답", "추론값", "생성된 SQL"]
    return wrong_df


def display_accuracy_metrics(df: pd.DataFrame):
    """정확도 메트릭을 Streamlit에 표시"""
    result = calculate_accuracy(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ 정답 수", f"{result['correct']} / {result['total']}")
    with col2:
        st.metric("📊 정확도", f"{result['accuracy']}%")
    with col3:
        st.metric("❌ 오답 수", f"{result['total'] - result['correct']}")


def main():
    st.title("📝 Text2SQL Demo with LangChain")

    tabs = st.tabs(["Text2SQL", "실험결과 1", "실험결과 2", "실험결과 3", "실험결과 4", "📊 결과 비교"])

    with tabs[0]:
        natural_query = st.text_input(
            "Enter your question:",
            "List the title and release year of movies.",
        )

        col1, col2 = st.columns(2)
        
        with col1:
            run_button = st.button("🚀 Run (SQL 생성 및 실행)", key="run_text2sql")
        with col2:
            preview_button = st.button("👁️ 프롬프트 미리보기", key="preview_prompt")

        # 프롬프트 미리보기
        if preview_button:
            with st.spinner("프롬프트 생성 중..."):
                try:
                    prompt_info = get_prompt_preview(natural_query)
                    
                    st.subheader("📋 프롬프트 구성 요소")
                    
                    # 1. 검색된 테이블
                    st.markdown("#### 🔍 벡터 검색 결과 (상위 10개 테이블)")
                    st.dataframe(pd.DataFrame(prompt_info["retrieved_tables"]))
                    
                    # 2. Primary Table
                    st.markdown(f"#### 📌 Primary Table: `{prompt_info['primary_table']}`")
                    
                    # 3. System Prompt
                    with st.expander("🤖 System Prompt", expanded=False):
                        st.code(prompt_info["system_prompt"], language="text")
                    
                    # 4. User Prompt (실제 LLM에 전달되는 내용)
                    with st.expander("👤 User Prompt (실제 LLM 입력)", expanded=True):
                        st.code(prompt_info["user_prompt"], language="text")
                    
                    # 5. Context (검색된 테이블 스키마)
                    with st.expander("📊 Context (검색된 테이블 스키마)", expanded=False):
                        st.code(prompt_info["context"], language="text")
                        
                except Exception as e:
                    st.error(f"프롬프트 생성 오류: {e}")

        # SQL 생성 및 실행
        if run_button:
            try:
                log_step("🎯 사용자 요청 시작")
                sql = invoke_text_to_sql_chain(natural_query)
                log_step("Step 6: SQL 정리 완료", {"정리된_SQL": sql})
                
                st.subheader("🔧 생성된 SQL")
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
                    
                    st.subheader("📊 실행 결과")
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
            
            # 정확도 표시
            display_accuracy_metrics(st.session_state["experiment_1"])
            st.divider()
            
            # DataFrame 표시
            st.dataframe(st.session_state["experiment_1"])
        else:
            st.info("아직 실험 결과가 없습니다.")
            if st.button("실험 실행하기", key="run_exp1"):
                df = ex1_run()
                st.session_state["experiment_1"] = df
                display_accuracy_metrics(df)
                st.divider()
                st.dataframe(st.session_state["experiment_1"])

    with tabs[2]:
        st.header("실험결과_2")
        st.write(": 기본 스키마 + 테이블 요약 + **컬럼별 메타정보** --> RAG 유사 문서 n개 검색 --> 프롬프트 생성 --> SQL 생성 --> 실행")
        st.info("💡 컬럼별 실제 값 분포(distinct count, top values, 범위, categorical 여부 등)를 프롬프트에 포함하여 더 정확한 SQL 생성을 목표로 합니다.")
        
        csv_path_2 = "experiments/experiment_2/result.csv"
        meta_path = "experiments/experiment_2/table_meta.pkl"

        # 테이블 메타정보 미리보기 (pickle)
        if os.path.exists(meta_path):
            with st.expander("📊 테이블 메타정보 미리보기 (pickle)"):
                import pickle
                with open(meta_path, "rb") as f:
                    meta = pickle.load(f)
                # 테이블 선택
                table_name = st.selectbox("테이블 선택", list(meta.keys()))
                if table_name:
                    st.json(meta[table_name])

        if os.path.exists(csv_path_2):
            df = pd.read_csv(csv_path_2)
            if "experiment_2" not in st.session_state:
                st.session_state["experiment_2"] = df
            
            # 정확도 표시
            display_accuracy_metrics(st.session_state["experiment_2"])
            st.divider()
            
            st.dataframe(st.session_state["experiment_2"])
        else:
            st.info("아직 실험 결과가 없습니다.")
            if st.button("실험 실행하기", key="run_exp2"):
                with st.spinner("실험 2 실행 중... (테이블 메타정보 수집 포함)"):
                    df = ex2_run()
                    st.session_state["experiment_2"] = df
                    display_accuracy_metrics(df)
                    st.divider()
                    st.dataframe(st.session_state["experiment_2"])

    with tabs[3]:
        st.header("실험결과_3")
        st.write(": 실험 1과 동일한 방법론 + **모델 업그레이드**")
        st.info("💡 임베딩: text-embedding-3-large, LLM: gpt-5")
        
        csv_path_3 = "experiments/experiment_3/result.csv"

        if os.path.exists(csv_path_3):
            df = pd.read_csv(csv_path_3)
            if "experiment_3" not in st.session_state:
                st.session_state["experiment_3"] = df
            
            # 정확도 표시
            display_accuracy_metrics(st.session_state["experiment_3"])
            st.divider()
            
            st.dataframe(st.session_state["experiment_3"])
        else:
            st.info("아직 실험 결과가 없습니다.")
            if st.button("실험 실행하기", key="run_exp3"):
                with st.spinner("실험 3 실행 중... (gpt-5 사용)"):
                    df = ex3_run()
                    st.session_state["experiment_3"] = df
                    display_accuracy_metrics(df)
                    st.divider()
                    st.dataframe(st.session_state["experiment_3"])

    with tabs[4]:
        st.header("실험결과_4")
        st.write(": **2단계 Text2SQL** (벡터 검색 없이 LLM 기반 테이블 선택)")
        st.info("""💡 **핵심 아이디어**
        
1️⃣ **1단계 - 테이블 선택**: 모든 테이블 스키마 + 조인 관계를 프롬프트에 넣고 LLM이 필요한 테이블 선택
2️⃣ **2단계 - SQL 생성**: 선택된 테이블의 상세 컬럼 정보 + 실제 값들로 SQL 생성

✅ 벡터 검색의 시맨틱 불일치 문제 해결
✅ 대소문자/띄어쓰기 등 정확한 값 매칭 가능
        """)
        
        csv_path_4 = "experiments/experiment_4/result.csv"
        meta_path_4 = "experiments/experiment_4/table_meta.pkl"

        # 테이블 메타정보 미리보기 (pickle)
        if os.path.exists(meta_path_4):
            with st.expander("📊 테이블 메타정보 미리보기 (pickle)"):
                import pickle
                with open(meta_path_4, "rb") as f:
                    meta = pickle.load(f)
                table_name = st.selectbox("테이블 선택", list(meta.keys()), key="exp4_table")
                if table_name:
                    st.json(meta[table_name])

        if os.path.exists(csv_path_4):
            df = pd.read_csv(csv_path_4)
            if "experiment_4" not in st.session_state:
                st.session_state["experiment_4"] = df
            
            # 정확도 표시
            display_accuracy_metrics(st.session_state["experiment_4"])
            st.divider()
            
            st.dataframe(st.session_state["experiment_4"])
        else:
            st.info("아직 실험 결과가 없습니다.")
            if st.button("실험 실행하기", key="run_exp4"):
                with st.spinner("실험 4 실행 중... (2단계 Text2SQL)"):
                    df = ex4_run()
                    st.session_state["experiment_4"] = df
                    display_accuracy_metrics(df)
                    st.divider()
                    st.dataframe(st.session_state["experiment_4"])

    # ========== 결과 비교 탭 ==========
    with tabs[5]:
        st.header("📊 실험 결과 비교")
        
        # 각 실험 결과 로드
        experiments = {}
        exp_paths = {
            "실험 1": "experiments/experiment_1/result.csv",
            "실험 2": "experiments/experiment_2/result.csv",
            "실험 3": "experiments/experiment_3/result.csv",
            "실험 4": "experiments/experiment_4/result.csv",
        }
        
        for exp_name, path in exp_paths.items():
            if os.path.exists(path):
                experiments[exp_name] = pd.read_csv(path)
        
        if not experiments:
            st.warning("아직 실험 결과가 없습니다. 먼저 실험을 실행해주세요.")
        else:
            # 1. 정확도 비교 테이블
            st.subheader("🎯 정확도 비교")
            
            comparison_data = []
            for exp_name, df in experiments.items():
                result = calculate_accuracy(df)
                comparison_data.append({
                    "실험": exp_name,
                    "정답 수": result["correct"],
                    "전체 문항": result["total"],
                    "오답 수": result["total"] - result["correct"],
                    "정확도 (%)": result["accuracy"],
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # 정확도 바 차트
            st.bar_chart(comparison_df.set_index("실험")["정확도 (%)"])
            
            # 비교 테이블
            st.dataframe(comparison_df, use_container_width=True)
            
            st.divider()
            
            # 2. 틀린 문제 분석
            st.subheader("❌ 오답 분석")
            
            # 실험 선택
            selected_exp = st.selectbox(
                "실험 선택",
                list(experiments.keys()),
                key="wrong_answer_exp"
            )
            
            if selected_exp:
                wrong_df = get_wrong_answers(experiments[selected_exp])
                
                if wrong_df.empty:
                    st.success(f"🎉 {selected_exp}에서 모든 문제를 맞췄습니다!")
                else:
                    st.warning(f"📋 {selected_exp}에서 틀린 문제: {len(wrong_df)}개")
                    st.dataframe(wrong_df, use_container_width=True)
                    
                    # 틀린 문제 상세 보기
                    with st.expander("🔍 틀린 문제 상세 보기"):
                        for idx, row in wrong_df.iterrows():
                            st.markdown(f"**질문:** {row['질문']}")
                            st.markdown(f"- 정답: `{row['정답']}`")
                            st.markdown(f"- 추론값: `{row['추론값']}`")
                            st.code(row['생성된 SQL'], language="sql")
                            st.divider()
            
            st.divider()
            
            # 3. 문항별 정답 현황
            st.subheader("📋 문항별 정답 현황")
            
            if len(experiments) > 1:
                # 모든 실험의 정답 여부를 하나의 테이블로
                base_df = list(experiments.values())[0][["question", "label"]].copy()
                base_df.columns = ["질문", "정답"]
                
                for exp_name, df in experiments.items():
                    df_temp = df.copy()
                    df_temp["label_str"] = df_temp["label"].astype(str).str.strip()
                    df_temp["infer_str"] = df_temp["infer"].astype(str).str.strip()
                    df_temp["is_correct"] = df_temp["label_str"] == df_temp["infer_str"]
                    base_df[exp_name] = df_temp["is_correct"].map({True: "✅", False: "❌"})
                
                st.dataframe(base_df, use_container_width=True)
                
                # 다운로드 버튼
                csv = base_df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 비교 결과 CSV 다운로드",
                    data=csv,
                    file_name="experiment_comparison.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()

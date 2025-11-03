import streamlit as st
import pandas as pd
import os

# LangChain 모듈 임포트
from chains.text_to_sql_chain import invoke_text_to_sql_chain
from experiments.experiment_1.run import run as ex1_run
from utils import run_query, log_step


def main():
    st.title("📝 Text2SQL Demo with LangChain")

    tabs = st.tabs(["Text2SQL", "실험결과 1"])

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
            # session_state에 저장 (처음 한 번만)
            if "experiment_1" not in st.session_state:
                st.session_state["experiment_1"] = df
            # DataFrame 표시
            st.dataframe(st.session_state["experiment_1"])
        else:
            st.info("아직 실험 결과가 없습니다.")
            if st.button("실험 실행하기"):
                df = ex1_run()
                st.session_state["experiment_1"] = df
                st.dataframe(st.session_state["experiment_1"])


if __name__ == "__main__":
    main()
"""
Text2SQL 데모 - LangChain 기반 구현

자연어 질문을 SQL 쿼리로 변환하고 실행하는 Streamlit 애플리케이션입니다.
"""
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# LangChain 모듈 임포트
from chains.text_to_sql_chain import invoke_text_to_sql_chain
from utils import run_query, insert_doc, make_table_desc_dict, log_step, engine

# .env 환경변수 불러오기
load_dotenv()

# 초기 테이블 docs 설정
INIT_TABLE_DOCS = os.getenv("INIT_TABLE_DOCS", "0") == "1"


############################# 초기 테이블 작업: 임베딩 삽입 시작 #############################
if INIT_TABLE_DOCS:
    print("초기 테이블 작업: 임베딩 삽입 시작.")
    tables = make_table_desc_dict().keys()
    for table in make_table_desc_dict():
        insert_doc(table)
    print("초기 테이블 작업: 임베딩 삽입 완료.")
#######################################################################################


def main():
    """Streamlit 메인 애플리케이션"""
    st.title("📝 Text2SQL Demo with LangChain")

    # 사용자 입력
    natural_query = st.text_input(
        "Enter your question:",
        "List the title and release year of movies.",
    )

    if st.button("Run"):
        try:
            log_step("🎯 사용자 요청 시작")

            # LangChain 체인 실행 (자동으로 벡터 검색 + LLM 실행)
            sql = invoke_text_to_sql_chain(natural_query)

            log_step(
                "Step 6: SQL 정리 완료",
                {
                    "정리된_SQL": sql,
                },
            )

            # SQL 코드 표시
            st.code(sql, language="sql")

            try:
                log_step("Step 7: SQL 쿼리 실행 중...", {"SQL": sql})

                # SQL 실행
                rows = run_query(sql)
                df = pd.DataFrame(rows)

                log_step(
                    "Step 8: 쿼리 실행 완료",
                    {
                        "반환된_행_수": len(rows),
                        "컬럼_수": len(df.columns),
                        "컬럼명": list(df.columns),
                    },
                )

                # 결과 표시
                st.dataframe(df)

                log_step(
                    "✅ 전체 파이프라인 완료",
                    {
                        "최종_결과_행수": len(rows),
                        "처리_상태": "성공",
                    },
                )

            except Exception as e:
                log_step(
                    "❌ 쿼리 실행 오류 발생",
                    {
                        "에러_타입": type(e).__name__,
                        "에러_메시지": str(e),
                    },
                )
                st.error(f"Error running query: {e}")

        except Exception as e:
            log_step(
                "❌ SQL 생성 오류 발생",
                {
                    "에러_타입": type(e).__name__,
                    "에러_메시지": str(e),
                },
            )
            st.error(f"Error generating SQL: {e}")


if __name__ == "__main__":
    main()
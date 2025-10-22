# init/init_table_docs.py
import os
from utils.db_utils import insert_doc, make_table_desc_dict, run_command  # run_sql_command 추가

FLAG_FILE = "/app/init/.init_table_docs_done"

def main():
    if os.path.exists(FLAG_FILE):
        print("초기 테이블 임베딩 작업이 이미 완료되었습니다.")
        return

    print("초기 테이블 임베딩 작업 시작.")

    # ✅ 0. table_docs 테이블 생성
    create_table_sql = """
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE IF NOT EXISTS table_docs (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        embedding VECTOR(1536),
        created_at TIMESTAMP DEFAULT now()
    );
    """
    run_command(query=create_table_sql, dvd=False)
    print("✅ table_docs 테이블이 준비되었습니다.")

    # ✅ 1. 테이블 설명 삽입
    for table in make_table_desc_dict():
        insert_doc(table)

    # ✅ 2. 완료 플래그 생성
    with open(FLAG_FILE, "w") as f:
        f.write("done\n")
    print("✅ 초기 테이블 임베딩 작업 완료.")

if __name__ == "__main__":
    main()

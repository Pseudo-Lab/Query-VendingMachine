# LangChain 모듈 임포트
from chains.text_to_sql_chain import invoke_text_to_sql_chain
from utils import run_query, log_step
import pandas as pd
import os

def run():

    if os.path.exists("experiments/experiment_1/result.csv"):
        return pd.read_csv("experiments/experiment_1/result.csv")

    testset = pd.read_csv("experiments/dvdrental_testset.csv")
    question = testset["question"].tolist()
    infer = []
    for natural_query in question:
        try:
            sql = invoke_text_to_sql_chain(natural_query, )
            rows = run_query(query=sql, dvd=True)
            df = pd.DataFrame(rows)
            value = df.iloc[0,0] if not df.empty else None # 단일값 하드 코딩.
            infer.append(str(value) if value is not None else "")
        except Exception as e:
            log_step("❌ 오류 발생", {
                "에러_타입": type(e).__name__,
                "에러_메시지": str(e),
            })
            infer.append(None)

    testset["infer"] = infer
    testset.to_csv("experiments/experiment_1/result.csv", index=False, encoding="utf-8-sig")
    return testset
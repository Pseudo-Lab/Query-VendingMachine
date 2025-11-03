import pandas as pd

# LangChain 모듈 임포트
from chains.text_to_sql_chain import invoke_text_to_sql_chain
from utils import run_query, log_step

natural_query = "배우는 총 몇명일까?"

sql = invoke_text_to_sql_chain(natural_query, )

rows = run_query(query=sql, dvd=True)
df = pd.DataFrame(rows)
print(df)

# import pickle
# with open("main_test.pkl", "wb") as p:
#     pickle.dump(df, p)
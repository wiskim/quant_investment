# %%
import os

project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')

# %%
import pandas as pd
import sqlite3

df = pd.read_csv(os.path.join(data_path, 'dataguide_mkt_cap.csv'))

# %%
con = sqlite3.connect(os.path.join(data_path, 'kor_stock.db'))

dtype = {
    'date' : 'TEXT',
    'stock_cd' : 'TEXT',
    'mkt_cap' : 'INTEGER'
}

n = 1000
for i in range(0, df.shape[0], n):
    sub_df = df.iloc[i:i+n, :]
    sub_df.set_index(['date'], inplace=True)
    sub_df = sub_df.stack()
    sub_df = pd.DataFrame(sub_df, columns=['mkt_cap'])
    sub_df.reset_index(inplace=True)
    sub_df.columns = ['date', 'stock_cd', 'mkt_cap']
    sub_df.to_sql('kor_mkt_cap', con, if_exists='append', index=False, chunksize=1000, dtype=dtype)

con.close()

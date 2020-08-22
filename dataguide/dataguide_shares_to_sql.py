# %%
import os

project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')

# %%
import pandas as pd
import sqlite3

# %%
df = pd.read_csv(os.path.join(data_path, 'dataguide_shares.csv'), index_col=[0, 1])

# %%
df = df.stack().reset_index()

# %%
df = df.rename(columns={'level_2':'date', 0:'value'})

# %%
df['item_nm'] = df['item_nm'].replace({
    '상장주식수 (보통)(주)' : 'listed_shares_common',
    '상장주식수 (우선)(주)' : 'listed_shares_preferred',
    '상장예정주식수 (보통)(주)' : 'tobe_listed_shares_common',
    '상장예정주식수 (우선)(주)' : 'tobe_listed_shares_preferred',
    '자기주식수 (보통)(주)' : 'treasury_shares_common',
    '자기주식수 (우선)(주)' : 'treasury_shares_preferred',
    '종가(원)' : 'close_price',
    '시가총액 (보통-상장예정주식수 포함)(백만원)' : 'mkt_cap_common',
    '시가총액 (우선-상장예정주식수 포함)(백만원)' : 'mkt_cap_preferred'
})

# %%
dtype = {
    'stock_cd': 'TEXT',
    'item_nm': 'TEXT',
    'date' : 'TEXT',
    'value' : 'INTEGER'
}
con = sqlite3.connect(os.path.join(data_path, 'kor_stock.db'))
df.to_sql('kor_shares', con, if_exists='replace', index=False, dtype=dtype)
con.close()

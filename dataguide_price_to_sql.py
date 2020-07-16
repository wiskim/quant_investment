# %%
import pandas as pd
import sqlite3

# %%
df = pd.read_csv('./data/price_csv_200715.csv', header=[0, 1], index_col=0)

# %%
df = df.unstack().reset_index()

# %%
df.columns = ['stock_cd', 'price_div', 'date', 'price']
df['price_div'] = df['price_div'].replace({'시가(원)':'open', '저가(원)':'low', '고가(원)':'high', '종가(원)':'close'})

# %%
dtype = {
    'stock_cd': 'TEXT',
    'price_div': 'TEXT',
    'date' : 'TEXT',
    'price' : 'INTEGER'
}
con = sqlite3.connect('./data/kor_stock.db')
df.to_sql('kor_price', con, if_exists='replace', index=False, dtype=dtype)
con.close()

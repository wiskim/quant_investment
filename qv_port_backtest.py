# %%
import pandas as pd
import numpy as np
import sqlite3
import pyfolio as pf
import datetime

# %%
con = sqlite3.connect('./data/kor_stock.db')
sql = "SELECT * FROM kor_qv_portfolio"
raw_data = pd.read_sql(sql, con)
con.close()

# %%
qv_port = raw_data[raw_data['price'] >= 0.8]    # EBIT/EV 상위 20% 필터링
qv_port['rank'] = qv_port.groupby('year')['quality'].rank(method='min', ascending=False)    # 필터링된 종목들에 대해 연도별로 Quality 순위 매김
qv_port = qv_port[qv_port['rank'] <= 20].sort_values(['year', 'rank'])  # Quality 순위 상위 20위 필터링

# %%
def get_price(year, stock_cd=None):
    con = sqlite3.connect('./data/kor_stock.db')
    sql = "SELECT * FROM kor_price WHERE DATE(date) BETWEEN " + \
          "'" + str(year) + "-07-01' AND " +\
          "'" + str(year+1) + "-06-30'"
    if stock_cd == None:
        pass
    elif type(stock_cd) != list:
        raise TypeError('종목코드는 리스트 형태로 입력하여야합니다.')
    else:
        stock_cd_list = ','.join("'" + str(x) + "'" for x in stock_cd)
        sql = sql + " AND stock_cd IN (" + stock_cd_list + ")"
    df = pd.read_sql(sql, con)
    con.close()
    return df

# %%
port_ret_df = pd.DataFrame()
stock_ret_df = pd.DataFrame()

for year in range(2003, 2020):
    stock_cd_list = list(qv_port[qv_port['year'] == year]['stock_cd'])
    price_df = get_price(year, stock_cd_list)
    price_df = price_df.pivot_table(values='price', index='date', columns='stock_cd')
    ret_df = price_df.pct_change().fillna(0)
    ret_df['port_ret'] = ret_df.mean(axis=1)
    port_ret_df = pd.concat([port_ret_df, ret_df[['port_ret']]])
    ret_df = (1 + ret_df).cumprod(axis=0) - 1
    ret_df = pd.DataFrame(ret_df.iloc[-1, :-1])
    stock_ret_df = pd.concat([stock_ret_df, ret_df], axis=1)
    
port_ret_df = port_ret_df.reset_index()
port_ret_df['date'] = port_ret_df['date'].map(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
port_ret_df.set_index(port_ret_df['date'], inplace=True)
port_ret_df = port_ret_df[['port_ret']]

# %%
pf.create_returns_tear_sheet(port_ret_df['port_ret'])

# %%
con = sqlite3.connect('./data/kor_stock.db')
sql = "select * from kor_ticker"
ticker = pd.read_sql(sql, con)
con.close()

stock_ret_df = pd.merge(stock_ret_df, 
                        ticker[['stock_cd', 'stock_nm', 'fn_sec_nm']], 
                        left_on=stock_ret_df.index, 
                        right_on='stock_cd', 
                        how='left')

date = stock_ret_df.columns[stock_ret_df.columns.str.startswith('2020')][0]
stock_ret_df.loc[~stock_ret_df[date].isna(), ['stock_cd', 'stock_nm', date]]

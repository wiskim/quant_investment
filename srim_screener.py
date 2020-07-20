# %%
from stock_screener import *
import numpy as np
import pandas as pd
import sqlite3

# %%
fs = get_fs(account_nm=['지배주주지분', '지배주주순이익'],
            year=2019,
            period=4,
            ci_div='CON')

# %%
impaired_stock = fs.loc[(fs['account_nm']=='지배주주지분') & (fs['fs_value'] <= 0), :]['stock_cd'].unique()
fs = fs.loc[~fs['stock_cd'].isin(impaired_stock), :]    # 과거 3년내 완전자본잠식 기업 제외
fs = fs.pivot_table(values='fs_value', index=['stock_cd', 'year'], columns='account_nm')
fs['지배주주지분_lag'] = fs['지배주주지분'].shift(1)
fs['지배주주지분_avg'] = (fs['지배주주지분'] + fs['지배주주지분_lag']) / 2
fs['roe'] = np.trunc((fs['지배주주순이익'] / fs['지배주주지분_avg']) * 10000) / 10000
fs = fs.loc[fs.index.get_level_values('year') != '2016']
fs = fs.pivot_table(values=['지배주주지분', 'roe'], index='stock_cd', columns='year')

# %%
srim = fs['roe']
srim['roe'] = np.where((srim['2017'] < srim['2018']) & (srim['2018'] < srim['2019']),
                       srim['2019'], 
                       np.where((srim['2017'] > srim['2018']) & (srim['2018'] > srim['2019']),
                                srim['2019'], 
                                np.trunc(((srim['2017'] * 1 + srim['2018'] * 2 + srim['2019'] * 3) / 6) * 1000) / 1000))

# %%
temp = fs['지배주주지분'][['2019']]
temp.columns = ['b0']   # 자기자본
srim = pd.merge(srim, temp, left_on=srim.index, right_on=temp.index, how='left')
ke = 0.08   # 주주 요구 수익률
srim['equity_value'] = np.trunc(srim['b0'] * (srim['roe'] - ke) / ke)
srim = srim.rename(columns={'key_0' : 'stock_cd'})

# %%
sql = "SELECT * FROM kor_shares WHERE DATE = '2020-06-30'"
con = sqlite3.connect('./data/kor_stock.db')
shares = pd.read_sql(sql, con)

# %%
shares = shares.pivot_table(values='value', index='stock_cd', columns='item_nm')
shares['shares_no_common'] = shares['listed_shares_common'] + \
                             shares['tobe_listed_shares_common'] - \
                             shares['treasury_shares_common']
shares = shares[['mkt_cap_preferred', 'shares_no_common', 'close_price']]

# %%
srim = pd.merge(srim, shares, left_on='stock_cd', right_on=shares.index, how='left')
srim = srim.dropna()
srim['fair_price'] = np.trunc((srim['equity_value'] * 1000 - srim['mkt_cap_preferred'] * 1000000) / srim['shares_no_common'])
srim = srim[srim['fair_price'] > 0] # ROE가 ke 보다 작아서 적정주가가 (-)로 나오는 종목 제외
srim['ratio'] = np.trunc(srim['close_price'] / srim['fair_price'] * 10000) / 10000
srim = srim.sort_values('ratio')

# %%
srim.to_csv('./data/srim_result.csv', index=False)

# %%
from stock_screener import *
import numpy as np
import pandas as pd

# %%
fs = get_fs(account_nm=['지배주주지분', '지배주주순이익'],
            year=2019,
            period=4,
            ci_div='CON')

# %%
fs = fs.pivot_table(values='fs_value', index=['stock_cd', 'year'], columns='account_nm')
fs['지배주주지분_lag'] = fs['지배주주지분'].shift(1)
fs['지배주주지분_avg'] = (fs['지배주주지분'] + fs['지배주주지분_lag']) / 2
fs['roe'] = np.trunc((fs['지배주주순이익'] / fs['지배주주지분_avg']) * 1000) / 1000
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

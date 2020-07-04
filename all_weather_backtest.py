# %%
import datetime
import pandas as pd
import FinanceDataReader as fdr
import pyfolio as pf

# %%
etf_list = ['VT', 'IAU', 'EDV', 'VCLT', 'EMLC', 'LTPZ', 'BCI']
weight_list = [0.4, 0.05, 0.25, 0.075, 0.075, 0.1, 0.05]

price_df = pd.DataFrame()

for etf in etf_list:
    temp = fdr.DataReader(etf, start='2000-01-01')
    temp = temp['Close']
    price_df = pd.concat([price_df, temp], axis=1)

price_df.columns = etf_list
price_df = price_df.dropna()

# %%
change_df = price_df.pct_change()

ym_list = pd.date_range(
	datetime.datetime.strptime('2018-01', '%Y-%m'),
	datetime.datetime.strptime('2020-06', '%Y-%m'),
	freq='MS').strftime('%Y-%m').tolist()

port_ret_df = pd.DataFrame()

for ym in ym_list:
    temp = change_df[ym]
    temp = temp + 1
    temp = temp.cumprod()
    temp = temp - 1
    temp['port_cum_ret'] = (temp * weight_list).sum(axis=1)
    temp['port_daily_ret'] = (((1+temp['port_cum_ret']) / (1 + temp['port_cum_ret'].shift(1))) - 1).fillna(temp['port_cum_ret'])
    port_ret_df = pd.concat([port_ret_df, temp[['port_daily_ret']]])

port_ret_df['port_cum_ret'] = ((1 + port_ret_df['port_daily_ret']).cumprod()) - 1

# %%
pf.create_returns_tear_sheet(port_ret_df['port_daily_ret'])

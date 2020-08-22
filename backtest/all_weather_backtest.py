# %%
import datetime
import numpy as np
import pandas as pd
import FinanceDataReader as fdr
import pyfolio as pf

# %%
ticker_list = ['TLT', 'IEF', 'SPY', 'IAU', 'DBC']
weight = np.array([0.4, 0.15, 0.3, 0.075, 0.075])

open_df = pd.DataFrame()
close_df = pd.DataFrame()

for ticker in ticker_list:
    ohlc_df = fdr.DataReader(ticker, start='2000-01-01')
    open_df = pd.concat([open_df, ohlc_df[['Open']]], axis=1)
    close_df = pd.concat([close_df, ohlc_df[['Close']]], axis=1)

open_df.index = pd.to_datetime(open_df.index)
open_df.columns = ticker_list
open_df = open_df.dropna()

close_df.index = pd.to_datetime(close_df.index)
close_df.columns = ticker_list
close_df = close_df.dropna()

# %%
ym_list = pd.date_range(
	datetime.datetime.strptime('2015-08', '%Y-%m'),
	datetime.datetime.strptime('2020-06', '%Y-%m'),
	freq='MS').strftime('%Y-%m').tolist()

result_df = pd.DataFrame()

cash_amt = 10000

for ym in ym_list:
    open_temp = open_df[ym]
    close_temp = close_df[ym]
    cash_allct = cash_amt * weight
    quantity = np.trunc(cash_allct / open_temp.iloc[0, :])  # 리밸런싱일에 시초가로 매수 가정
    cash_amt = np.trunc((cash_amt - (open_temp.iloc[0, :] * quantity).sum()) * 100) / 100.0 # 주식은 1주 단위로 사야하므로 투자비율 대로 매수 시 현금이 남음
    port_temp = close_temp * quantity
    port_temp['CASH'] = cash_amt
    port_temp['PORT_VAL'] = port_temp.sum(axis=1)   # 매일 종목별로 종가에 수량을 곱하고 거기에 남은 현금금액을 더하여 포트폴리오 평가금액 계산
    cash_amt = port_temp['PORT_VAL'][-1]    # 리밸런싱일 전날 종가로 전종목 매도 가정
    result_df = pd.concat([result_df, port_temp])

result_df['PORT_VAL_SHIFT1'] = result_df['PORT_VAL'].shift(1).fillna(10000)
result_df['PORT_DAILY_RET'] = result_df['PORT_VAL'] / result_df['PORT_VAL_SHIFT1'] - 1
result_df['PORT_CUM_RET'] = (1 + result_df['PORT_DAILY_RET']).cumprod() - 1

# %%
pf.create_returns_tear_sheet(result_df['PORT_DAILY_RET'])

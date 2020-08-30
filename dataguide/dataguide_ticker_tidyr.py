import os
project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')

import pandas as pd
df = pd.read_csv(os.path.join(data_path, 'dataguide_ticker.csv'), dtype = 'str')

df = df.rename(columns={
    'Symbol' : 'stock_cd',
    'Name' : 'stock_nm',
    '시장구분' : 'mkt_div',
    '상장(등록)일자' : 'listing_date',
    '상장폐지일자' : 'delisting_date',
    '시장이전일' : 'mkt_move_date',
    '시장이전내용' : 'mkt_move',
    '투자조치구분' : 'warning_status',
    '거래정지여부' : 'stop_trading_status',
    '관리종목여부' : 'disqualifying_status',
    '결산월(Hist)' : 'closing_month',
    'FnGuide Industry Code' : 'fn_industry_cd',
    'FnGuide Industry' : 'fn_industry_nm',
    'FnGuide Industry Group Code' : 'fn_industry_grp_cd',
    'FnGuide Industry Group' : 'fn_industry_grp_nm',
    'FnGuide Sector Code' : 'fn_sec_cd',
    'FnGuide Sector' : 'fn_sec_nm'
})

df.listing_date = pd.to_datetime(df.listing_date)
df.delisting_date = pd.to_datetime(df.delisting_date)
df.mkt_move_date = pd.to_datetime(df.mkt_move_date)
df = df.loc[~df.listing_date.isnull(), ]

df[['mkt_move_from', 'mkt_move_to']] = df.mkt_move.str.split(', ', expand=True)
df.mkt_move_from = df.mkt_move_from.str.replace('변경전:', '')
df.mkt_move_to = df.mkt_move_to.str.replace('변경후:', '')

df = df.drop('mkt_move', axis=1)
df_col_seq = list(df.columns[:6]) + list(df.columns[-2:]) + list(df.columns[6:-2])
df = df.loc[:, df_col_seq]

df.to_csv(os.path.join(data_path, 'dataguide_ticker_tidyr.csv'), index=False)

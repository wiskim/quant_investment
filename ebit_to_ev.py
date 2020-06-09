# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from IPython import get_ipython

# %%
# SQL DB에서 필요한 자료 불러오기

import sqlite3
import pandas as pd
pd.options.display.float_format = '{:,.2f}'.format

con = sqlite3.connect('.\data\kor_stock.db')

sql = '''
SELECT stock_cd, year, account_nm, fs_value
FROM kor_fs
WHERE ci_div='IND' AND account_nm IN ('*순차입부채', '영업이익') AND year IN ('2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018');
'''
kor_fs = pd.read_sql(sql, con)

sql = '''
SELECT *
FROM kor_mkt_cap
WHERE date IN ('2011-06-30', '2012-06-29', '2013-06-28', '2014-06-30', '2015-06-30', '2016-06-30', '2017-06-30', '2018-06-29', '2019-06-28');
'''
kor_mkt_cap = pd.read_sql(sql, con)

sql = '''
SELECT stock_cd, stock_nm, unlisted_day, listed_day
FROM kor_ticker
WHERE fn_sec_nm != '금융';
'''
kor_ticker = pd.read_sql(sql, con)

sql = '''
SELECT * 
FROM kor_price 
WHERE SUBSTR(date, 1, 4)||SUBSTR(date, 6, 2)||SUBSTR(date, 9, 2) BETWEEN "20100101" AND "20191231";
'''
kor_price = pd.read_sql(sql, con)

con.close()


# %%
# 직전년도말 재무제표 및 6월말 시가총액을 기준으로 EBIT/EV 상위 20종목 추출

import numpy as np

kor_fs['year'] = kor_fs.year.astype('int')
kor_mkt_cap['year'] = kor_mkt_cap.date.str.slice(stop=4).astype('int')

screen_result = pd.DataFrame()

for year in range(2010, 2019):
    
    fs = kor_fs[kor_fs.year==year].pivot(index='stock_cd', columns='account_nm', values='fs_value')
    fs.rename(columns={'*순차입부채':'net_debt', '영업이익':'ebit'}, inplace=True)
    
    mcap = kor_mkt_cap[kor_mkt_cap.year==(year+1)][['stock_cd', 'mkt_cap']]
    
    ebit_to_ev = pd.merge(fs, mcap, left_on=fs.index, right_on='stock_cd', how='left')
    ebit_to_ev = pd.merge(ebit_to_ev, kor_ticker, on='stock_cd', how='inner')
    
    ebit_to_ev = ebit_to_ev[(ebit_to_ev.unlisted_day.isnull()) | (ebit_to_ev.unlisted_day> (str(year+1)+'-07-01'))]    # 상장폐지 종목 삭제
    ebit_to_ev = ebit_to_ev[ebit_to_ev.listed_day <= (str(year+1)+'-07-01')]    # 7월초 현재 상장된 종목만 필터링
    ebit_to_ev['net_debt'] = ebit_to_ev['net_debt'] / 1000
    ebit_to_ev['ebit'] = ebit_to_ev['ebit'] / 1000
    ebit_to_ev['ev'] = ebit_to_ev['net_debt'] + ebit_to_ev['mkt_cap']
    ebit_to_ev['ev'] = np.where(ebit_to_ev.ev<0, 1, ebit_to_ev.ev)    # 보유 현금 및 단기금융상품이 많아 순차입부채가 (-)인 경우 EV가 (-)가 되는 경우도 발생. 이 경우 EV를 1로 설정하여 영업이익이 높은 순으로 순위를 매김. 
    ebit_to_ev['ebit_to_ev_value'] = ebit_to_ev['ebit'] / ebit_to_ev['ev']
    ebit_to_ev['year'] = year    # 재무제표 년도 기준으로 입력
    ebit_to_ev.sort_values('ebit_to_ev_value', ascending=False, inplace=True)
    ebit_to_ev['ebit_to_ev_rank'] = np.round(ebit_to_ev.ebit_to_ev_value.rank(pct=True)*100, 2)
    ebit_to_ev = ebit_to_ev[['year', 'stock_cd', 'stock_nm', 'ebit', 'net_debt', 'mkt_cap', 'ev', 'ebit_to_ev_value', 'ebit_to_ev_rank']]
    
    screen_result = screen_result.append(ebit_to_ev, ignore_index=True)


# %%
# EBIT/EV 상위 20종목을 매년 7월초 종가로 매수하여 익년 6월말 매도 반복(동일가중포트)

port_ret_result = pd.DataFrame()
ind_ret_result = pd.DataFrame()

for year in range(2010, 2018):
    
    top_stock = screen_result[(screen_result.year==year)].head(20).stock_cd
    price = kor_price[(kor_price.date >= (str(year+1)+'-07-01')) & 
                      (kor_price.date <= (str(year+2)+'-06-31')) & 
                      kor_price.stock_cd.isin(top_stock)]
    ret = price.pivot(index='date', columns='stock_cd', values='price')
    ret = ret.pct_change(1)
    
    ind_ret = ret + 1
    ind_ret = ind_ret.apply(np.product) - 1
    ind_ret = pd.DataFrame(ind_ret, columns=[year])
    ind_ret.reset_index(inplace=True)
    try:
        ind_ret_result = pd.merge(ind_ret_result, ind_ret, on='stock_cd', how='outer')
    except KeyError:
        ind_ret_result = ind_ret
        
    ret['daily_ret'] = ret.sum(axis=1)/20
    ret.columns.name=''
    ret.reset_index(inplace=True)
    ret = ret[['date', 'daily_ret']]
    port_ret_result = port_ret_result.append(ret, ignore_index=True)
    
port_ret_result['acmlt_ret'] = (1+ port_ret_result.daily_ret).cumprod()
port_ret_result['date'] = pd.to_datetime(port_ret_result['date'])

ind_ret_result = pd.merge(ind_ret_result, kor_ticker[['stock_cd', 'stock_nm']], on='stock_cd', how='left')
col = ind_ret_result.columns.tolist()
ind_ret_result = ind_ret_result[col[-1:]+col[:-1]]


# %%
get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

plt.plot(port_ret_result['date'], port_ret_result['acmlt_ret'])


# %%
port_ret_result.tail(1).acmlt_ret.values


# %%
ind_ret_result.iloc[:, 2: ].apply(np.sum)/20


# %%
pd.set_option('display.max_rows', None)  
ind_ret_result


# %%
pd.set_option('display.max_rows', None)  
screen_result[screen_result.year==2018].head(100)


# %%
dtype = {
    'year':'TEXT',
    'stock_cd':'TEXT',
    'stock_nm':'TEXT',
    'ebit':'INTEGER',
    'mkt_cap':'INTEGER',
    'ev':'REAL',
    'ebit_to_ev_value':'REAL',
    'ebit_to_ev_rank':'REAL'
}
con = sqlite3.connect('.\data\kor_stock.db')
screen_result.to_sql('ebit_to_ev', con, if_exists='replace', index=False, dtype=dtype)


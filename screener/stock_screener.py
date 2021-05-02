# %%
import os
project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import datetime
sns.set()
pd.options.display.float_format = '{:,.4f}'.format

def get_fs(stock_cd=[], item_nm=[], fiscal_year=None, period=5, con_div='Seperated'):
    if fiscal_year is None:
        fiscal_year = int(datetime.date.today().year)
    year_list = ','.join(str(x) for x in range(fiscal_year-(period-1), fiscal_year+1))
    sql = "SELECT * FROM kor_fs WHERE fiscal_year IN (" + year_list + ")"
    if not stock_cd:
        pass
    elif type(stock_cd) != list:
        raise TypeError('종목코드는 리스트 형태로 입력하여야합니다.')
    else:
        stock_cd_list = ','.join("'" + str(x) + "'" for x in stock_cd)
        sql = sql + " AND stock_cd IN (" + stock_cd_list + ")"
    if not item_nm:
        pass
    elif type(item_nm) != list:
        raise TypeError('계정과목명은 리스트 형태로 입력하여야합니다.')
    else:
        item_nm_list = ','.join("'" + str(x) + "'" for x in item_nm)
        sql = sql + " AND item_nm IN (" + item_nm_list + ")"
    sql = sql + " AND con_div = '" + con_div + "'"
    con = sqlite3.connect(os.path.join(data_path, 'quant.db'))
    kor_fs = pd.read_sql(sql, con)
    con.close()
    kor_fs['item_value'] = pd.to_numeric(kor_fs['item_value'])
    kor_fs['item_value'] = kor_fs['item_value'].fillna(0)
    return kor_fs

def get_listed_stock(date_from, date_to, no_fin = True):
    if no_fin:
        sql = "SELECT * FROM kor_ticker WHERE fn_sec_nm != '금융'"
    else:
        sql = "SELECT * FROM kor_ticker"
    con = sqlite3.connect(os.path.join(data_path, 'quant.db'))
    kor_ticker = pd.read_sql(sql, con)
    con.close()
    kor_ticker.listing_date = pd.to_datetime(kor_ticker.listing_date)
    kor_ticker.delisting_date = pd.to_datetime(kor_ticker.delisting_date)
    kor_ticker = kor_ticker[(kor_ticker.listing_date <= pd.to_datetime(date_from)) & 
                            ((kor_ticker.delisting_date.isnull()) | 
                             (kor_ticker.delisting_date > pd.to_datetime(date_to)))]
    kor_ticker = kor_ticker[['stock_cd', 'stock_nm', 'fn_industry_grp_nm']]
    return kor_ticker

def get_mkt_cap(date):
    sql = "SELECT * FROM kor_mkt_cap WHERE date = '" + date +"'"
    con = sqlite3.connect(os.path.join(data_path, 'quant.db'))
    mcap_df = pd.read_sql(sql, con)
    mcap_df = mcap_df.pivot_table(index=['stock_cd', 'stock_nm'], columns='item_nm', values='item_value').reset_index()
    mcap_df['mkt_cap'] = mcap_df['mkt_cap_common'] + mcap_df['mkt_cap_preferred']
    mcap_df = mcap_df[['stock_cd', 'stock_nm', 'mkt_cap']]
    mcap_df.columns.name = None
    return mcap_df

def roa_screener(fiscal_year, period=1):
    roa_df = get_fs(fiscal_year=fiscal_year, item_nm=['당기순이익(손실)', '자산'], period=period)
    roa_df = roa_df.pivot_table(index=['stock_cd', 'fiscal_year'], columns='item_nm', values='item_value')
    roa_df['roa'] = roa_df['당기순이익(손실)'] / roa_df['자산']
    roa_df['roa'] = np.round(roa_df['roa'], 4)
    roa_df['roa'] = np.where(roa_df.roa<=-1, np.nan, roa_df.roa)    # roa가 (-)100% 이하인 경우 기하평균수익률 계산시 오류가 발생하므로 NA로 마스킹
    roa_df = roa_df.pivot_table(index='stock_cd', columns='fiscal_year', values='roa')
    roa_df = roa_df.dropna()    # 5년간 roa가 정상적으로 산출된 종목만 필터링
    roa_df = roa_df + 1
    roa_df['roa_gmean'] = roa_df.product(axis=1, skipna=True) ** (1 / roa_df.count(axis=1))
    roa_df['roa_gmean'] = np.round(roa_df.roa_gmean, 4)
    roa_df = roa_df - 1
    roa_df = roa_df.sort_values('roa_gmean', ascending=False)
    roa_df.columns.name = ''
    roa_df = roa_df.reset_index()
    return roa_df

def roic_screener(fiscal_year, period=1):
    roic_df = get_fs(fiscal_year=fiscal_year, 
                     item_nm=['단기사채', '단기차입금', '사채', '장기차입금', '자본', 
                              '현금및현금성자산', '유동금융자산', '장기금융자산', '투자부동산', '영업이익(손실)'], 
                     period=period)
    roic_df = roic_df.pivot_table(index=['stock_cd', 'fiscal_year'], columns='item_nm', values='item_value')
    roic_df['ic'] = (
        roic_df['단기사채'] + roic_df['단기차입금'] + roic_df['사채'] + roic_df['장기차입금'] + roic_df['자본'] - 
        roic_df['현금및현금성자산'] - roic_df['유동금융자산'] - roic_df['장기금융자산'] - roic_df['투자부동산'] 
    )
    roic_df['ic'] = np.where(roic_df.ic<=0, np.nan, roic_df.ic)     #투하자본이 0이하인 종목은 아웃라이어로 보아 NA로 마스킹
    roic_df['roic'] = roic_df['영업이익(손실)'] / roic_df['ic']
    roic_df['roic'] = np.round(roic_df.roic, 4)
    roic_df['roic'] = np.where(roic_df.roic<=-1, np.nan, roic_df.roic)     # roic가 (-)100% 이하인 경우 기하평균수익률 계산시 오류가 발생하므로 NA로 마스킹
    roic_df = roic_df.pivot_table(index='stock_cd', columns='fiscal_year', values='roic')
    roic_df = roic_df.dropna()    # 5년간 roic가 정상적으로 산출된 종목만 필터링
    roic_df = roic_df + 1
    roic_df['roic_gmean'] = roic_df.product(axis=1, skipna=True) ** (1 / roic_df.count(axis=1))
    roic_df['roic_gmean'] = np.round(roic_df.roic_gmean, 4)
    roic_df = roic_df - 1
    roic_df = roic_df.sort_values('roic_gmean', ascending=False)
    roic_df.columns.name = ''
    roic_df = roic_df.reset_index()
    return roic_df

def fcfa_screener(fiscal_year, period=1):
    fcfa_df = get_fs(item_nm=['영업에서창출된현금흐름', '투자활동으로인한현금흐름', '자산'], 
                     fiscal_year=fiscal_year, period=period)
    fcfa_df = fcfa_df.pivot_table(index=['stock_cd', 'fiscal_year'], columns='item_nm', values='item_value')
    fcfa_df['fcf'] = fcfa_df['영업에서창출된현금흐름'] - fcfa_df['투자활동으로인한현금흐름']
    fcfa_df = fcfa_df.pivot_table(values=['fcf', '자산'], index='stock_cd', columns='fiscal_year')
    fcfa_df.columns = [(x[0])+'_'+str(x[1]) for x in fcfa_df.columns.values]
    fcfa_df['fcf_sum'] = fcfa_df.filter(regex='^fcf').sum(axis=1)
    fcfa_df['fcfa'] = fcfa_df['fcf_sum'] / fcfa_df['자산_'+str(fiscal_year)]
    fcfa_df = fcfa_df.sort_values('fcfa', ascending=False)
    fcfa_df = fcfa_df.reset_index()
    return fcfa_df

def mg_screener(fiscal_year, period=1):
    mg_df = get_fs(item_nm=['매출액(수익)', '매출총이익(손실)'], fiscal_year=fiscal_year, period=period+1)
    mg_df = mg_df.pivot_table(index=['stock_cd', 'fiscal_year'], columns='item_nm', values='item_value')
    mg_df['gm'] = np.round(mg_df['매출총이익(손실)'] / mg_df['매출액(수익)'], 4)
    mg_df = mg_df.pivot_table(index='stock_cd', columns='fiscal_year', values='gm')
    mg_df.columns = [str(col) for col in mg_df.columns.values]
    mg_df = mg_df.dropna()      # 매출총이익률을 계산할 수 있는 종목만 필터링
    mg_df = mg_df[(mg_df > 0).all(1)]       # 매출총이익이 적자인 종목은 제외
    for i in range(1, len(mg_df.columns)):
        mg_df['mg_'+mg_df.columns[i]] = np.round((mg_df.iloc[:, i] / mg_df.iloc[:, i-1]) - 1, 4) # margin growth
    mg_df = mg_df + 1 
    mg_df['mg_gmean'] = mg_df.filter(regex='^mg').product(axis=1, skipna=True) ** (1 / mg_df.filter(regex='^mg').count(axis=1))
    mg_df['mg_gmean'] = np.round(mg_df['mg_gmean'], 4)
    mg_df = mg_df - 1
    col_before = list(mg_df.columns[~mg_df.columns.str.startswith('mg')])
    col_after = ['gm_' + x for x in col_before]
    col_map = dict(zip(col_before, col_after))
    mg_df = mg_df.rename(columns=col_map)
    mg_df['ms'] = mg_df.filter(regex='^gm').iloc[:, 1:].mean(axis=1) / mg_df.filter(regex='^gm').iloc[:, 1:].std(axis=1) # margin stability
    mg_df['ms'] = np.round(mg_df['ms'], 4)
    mg_df['p_mg'] = mg_df.mg_gmean.rank(pct=True)
    mg_df['p_ms'] = mg_df.ms.rank(pct=True)
    mg_df['mm'] = mg_df[['p_mg', 'p_ms']].max(axis=1) # maximum margin
    mg_df = mg_df.sort_values('mm', ascending=False)
    mg_df.columns.name=''
    mg_df = mg_df.reset_index()
    return mg_df

def ete_screener(fiscal_year, mkt_cap_date):
    kor_fs = get_fs(item_nm=['단기사채', '단기차입금', '사채', '장기차입금', '현금및현금성자산', '영업이익(손실)'], 
                    fiscal_year=fiscal_year, period=1)
    kor_fs = kor_fs.pivot_table(index = 'stock_cd', columns='item_nm', values='item_value')
    kor_mkt_cap = get_mkt_cap(mkt_cap_date)    # 시가총액 기준일자 설정
    ete_df = pd.merge(kor_fs, kor_mkt_cap, left_on=kor_fs.index, right_on='stock_cd', how='inner')
    ete_df['net_debt'] = ete_df['단기사채'] + ete_df['단기차입금'] + ete_df['사채'] + ete_df['장기차입금'] - ete_df['현금및현금성자산']
    ete_df.rename(columns={'영업이익(손실)':'ebit'}, inplace=True)
    ete_df = ete_df[['stock_cd', 'ebit', 'net_debt', 'mkt_cap']]
    ete_df['net_debt'] = ete_df.net_debt / 1000
    ete_df['ebit'] = ete_df.ebit / 1000
    ete_df['ev'] = ete_df.net_debt + ete_df.mkt_cap
    ete_df['ev'] = np.where(ete_df.ev<0, 1, ete_df.ev)    # 보유 현금 및 단기금융상품이 많아 순차입부채가 (-)인 경우 EV가 (-)가 되는 경우도 발생. 이 경우 EV를 1로 설정하여 영업이익이 높은 순으로 순위를 매김
    ete_df['ete'] = np.round(ete_df.ebit / ete_df.ev, 4)
    ete_df = ete_df.sort_values('ete', ascending=False)
    ete_df = ete_df.reset_index(drop=True)
    return ete_df

def fscore_rawdata(fiscal_year):
    item_nm_list = [
        '당기순이익(손실)',
        '자산',
        '영업에서창출된현금흐름',
        '투자활동으로인한현금흐름',
        '장기차입금',
        '유동자산',
        '유동부채',
        '유상증자(감자)',
        '매출총이익(손실)',
        '매출액(수익)'
    ]
    fscore_df = get_fs(item_nm=item_nm_list, fiscal_year=fiscal_year, period=2)
    fscore_df = fscore_df.pivot_table(values='item_value', index=['stock_cd', 'fiscal_year'], columns='item_nm')
    fscore_df['roa'] = fscore_df['당기순이익(손실)'] / fscore_df['자산']
    fscore_df['fcfa'] = (fscore_df['영업에서창출된현금흐름'] - fscore_df['투자활동으로인한현금흐름']) / fscore_df['자산']
    fscore_df['accrual'] = fscore_df['fcfa'] - fscore_df['roa']
    fscore_df['lev'] = fscore_df['장기차입금'] / fscore_df['자산']
    fscore_df['liq'] = fscore_df['유동자산'] / fscore_df['유동부채']
    fscore_df['offer'] = fscore_df['유상증자(감자)']
    fscore_df['margin'] = fscore_df['매출총이익(손실)'] / fscore_df['매출액(수익)']
    fscore_df['turn'] = fscore_df['매출액(수익)'] / fscore_df['자산']
    fscore_df = fscore_df[['roa', 'fcfa', 'accrual', 'lev', 'liq', 'offer', 'margin', 'turn']]
    fscore_df = fscore_df.unstack()
    fscore_df = fscore_df.dropna()
    return fscore_df

def fscore_screener(fiscal_year):    
    fscore_df = fscore_rawdata(fiscal_year)
    # 현재 수익성
    fscore_df['f_1'] = np.where(fscore_df.loc[:, ('roa', fiscal_year)] > 0, 1, 0)
    fscore_df['f_2'] = np.where(fscore_df.loc[:, ('fcfa', fiscal_year)] > 0, 1, 0)
    fscore_df['f_3'] = np.where(fscore_df.loc[:, ('accrual', fiscal_year)] > 0, 1, 0)

    #안정성
    fscore_df['f_4'] = np.where(
        fscore_df.loc[:, ('lev', fiscal_year)] 
        - fscore_df.loc[:, ('lev', fiscal_year-1)] <= 0, 1, 0
    )
    fscore_df['f_5'] = np.where(
        fscore_df.loc[:, ('liq', fiscal_year)] 
        - fscore_df.loc[:, ('liq', fiscal_year-1)] > 0, 1, 0
    )
    fscore_df['f_6'] = np.where(fscore_df.loc[:, ('offer', fiscal_year)] <= 0, 1, 0)

    # 최근 영업 호전성
    fscore_df['f_7'] = np.where(
        fscore_df.loc[:, ('roa', fiscal_year)] 
        - fscore_df.loc[:, ('roa', fiscal_year-1)] > 0, 1, 0
    )
    fscore_df['f_8'] = np.where(
        fscore_df.loc[:, ('fcfa', fiscal_year)] 
        - fscore_df.loc[:, ('fcfa', fiscal_year-1)] > 0, 1, 0
    )
    fscore_df['f_9'] = np.where(
        fscore_df.loc[:, ('margin', fiscal_year)] 
        - fscore_df.loc[:, ('margin', fiscal_year-1)] > 0, 1, 0
    )
    fscore_df['f_10'] = np.where(
        fscore_df.loc[:, ('turn', fiscal_year)] 
        - fscore_df.loc[:, ('turn', fiscal_year-1)] > 0, 1, 0
    )
    fscore_df['fscore'] = fscore_df.loc[:, 'f_1':'f_10'].sum(axis=1)
    fscore_df = fscore_df['fscore']
    fscore_df = fscore_df.reset_index()
    fscore_df = fscore_df.sort_values('fscore', ascending=False)
    fscore_df = fscore_df.reset_index(drop=True)
    return fscore_df

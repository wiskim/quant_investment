# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import datetime
sns.set()
pd.options.display.float_format = '{:,.4f}'.format

def get_fs(stock_cd=[], account_nm=[], year=None, period=5, ci_div='IND'):
    if year is None:
        year = int(datetime.date.today().year)
    year_list = ','.join(str(x) for x in range(year-(period-1), year+1))
    sql = "SELECT * FROM kor_fs WHERE year IN (" + year_list + ")"
    if not stock_cd:
        pass
    elif type(stock_cd) != list:
        raise TypeError('종목코드는 리스트 형태로 입력하여야합니다.')
    else:
        stock_cd_list = ','.join("'" + str(x) + "'" for x in stock_cd)
        sql = sql + " AND stock_cd IN (" + stock_cd_list + ")"
    if not account_nm:
        pass
    elif type(account_nm) != list:
        raise TypeError('계정과목명은 리스트 형태로 입력하여야합니다.')
    else:
        account_nm_list = ','.join("'" + str(x) + "'" for x in account_nm)
        sql = sql + " AND account_nm IN (" + account_nm_list + ")"
    sql = sql + " AND ci_div = '" + ci_div + "'"
    con = sqlite3.connect('./data/kor_stock.db')
    kor_fs = pd.read_sql(sql, con)
    con.close()
    return kor_fs

def get_listed_stock(year, period=1):
    con = sqlite3.connect('./data/kor_stock.db')
    sql = "SELECT * FROM kor_ticker WHERE fn_sec_nm != '금융'"  #금융회사 제외
    kor_ticker = pd.read_sql(sql, con)
    con.close()
    kor_ticker.listed_day = pd.to_datetime(kor_ticker.listed_day)
    kor_ticker.unlisted_day = pd.to_datetime(kor_ticker.unlisted_day)
    kor_ticker = kor_ticker[(kor_ticker.listed_day < pd.to_datetime(str(year-(period-1))+'-01-01')) & 
                            ((kor_ticker.unlisted_day.isnull()) | 
                             (kor_ticker.unlisted_day > pd.to_datetime(str(year+1)+'-06-30')))]
    kor_ticker = kor_ticker[['stock_cd', 'stock_nm', 'fn_ind_nm']]
    return kor_ticker

def get_nearest_bizday(date):    
    date_str1 = datetime.datetime.strptime(date, '%Y-%m-%d')
    date_str1 = date_str1 + datetime.timedelta(days=-7)
    date_str1 = datetime.datetime.strftime(date_str1, '%Y-%m-%d')
    date_str1 = "'" + date_str1 + "'"
    date_str2 = "'" + date + "'"
    sql = "SELECT date FROM (SELECT date(date) date FROM kor_mkt_cap) t1 WHERE t1.date BETWEEN date("
    sql = sql + date_str1
    sql = sql + ") AND date("
    sql = sql + date_str2
    sql = sql + ") ORDER BY date DESC LIMIT 1"
    con = sqlite3.connect('./data/kor_stock.db')
    bizday = pd.read_sql(sql, con)
    bizday = bizday['date'].values[0]
    con.close()
    return bizday

def get_mkt_cap(date):
    bizday = get_nearest_bizday(date=date)
    bizday = "'" + bizday + "'"
    sql = "SELECT * FROM kor_mkt_cap WHERE date = " + bizday
    con = sqlite3.connect('./data/kor_stock.db')
    mcap_df = pd.read_sql(sql, con)
    return mcap_df

def roa_screener(year, period=1):
    roa_df = get_fs(year=year, account_nm=['당기순이익', '총자산'], period=period)
    roa_df = roa_df.pivot_table(index=['stock_cd', 'year'], columns='account_nm', values='fs_value')
    roa_df['roa'] = roa_df.당기순이익 / roa_df.총자산
    roa_df['roa'] = np.round(roa_df['roa'], 4)
    roa_df['roa'] = np.where(roa_df.roa<=-1, np.nan, roa_df.roa)    # roa가 (-)100% 이하인 경우 기하평균수익률 계산시 오류가 발생하므로 NA로 마스킹
    roa_df = roa_df.pivot_table(index='stock_cd', columns='year', values='roa')
    roa_df = roa_df.dropna()    # 5년간 roa가 정상적으로 산출된 종목만 필터링
    roa_df = roa_df + 1
    roa_df['roa_gmean'] = roa_df.product(axis=1, skipna=True) ** (1 / roa_df.count(axis=1))
    roa_df['roa_gmean'] = np.round(roa_df.roa_gmean, 4)
    roa_df = roa_df - 1
    roa_df = roa_df.sort_values('roa_gmean', ascending=False)
    roa_df.columns.name = ''
    roa_df = roa_df.reset_index()
    return roa_df

def roic_screener(year, period=1):
    roic_df = get_fs(year=year, account_nm=['*총차입부채', '총자본', '현금및현금성자산', '*총금융자산', '투자부동산', '영업이익'], period=period)
    roic_df = roic_df.pivot_table(index=['stock_cd', 'year'], columns='account_nm', values='fs_value')
    roic_df['ic'] = roic_df['*총차입부채'] + roic_df['총자본'] - roic_df['현금및현금성자산'] - roic_df['*총금융자산'] - roic_df['투자부동산']
    roic_df['ic'] = np.where(roic_df.ic<=0, np.nan, roic_df.ic)     #투하자본이 0이하인 종목은 아웃라이어로 보아 NA로 마스킹
    roic_df['roic'] = roic_df.영업이익 / roic_df.ic
    roic_df['roic'] = np.round(roic_df.roic, 4)
    roic_df['roic'] = np.where(roic_df.roic<=-1, np.nan, roic_df.roic)     # roic가 (-)100% 이하인 경우 기하평균수익률 계산시 오류가 발생하므로 NA로 마스킹
    roic_df = roic_df.pivot_table(index='stock_cd', columns='year', values='roic')
    roic_df = roic_df.dropna()    # 5년간 roic가 정상적으로 산출된 종목만 필터링
    roic_df = roic_df + 1
    roic_df['roic_gmean'] = roic_df.product(axis=1, skipna=True) ** (1 / roic_df.count(axis=1))
    roic_df['roic_gmean'] = np.round(roic_df.roic_gmean, 4)
    roic_df = roic_df - 1
    roic_df = roic_df.sort_values('roic_gmean', ascending=False)
    roic_df.columns.name = ''
    roic_df = roic_df.reset_index()
    return roic_df

def fcfa_screener(year, period=1):
    fcfa_df = get_fs(account_nm=['영업활동으로인한현금흐름', '*유형자산순취득액', '*무형자산순취득액', '총자산'], year=year, period=period)
    fcfa_df = fcfa_df.pivot_table(index=['stock_cd', 'year'], columns='account_nm', values='fs_value')
    fcfa_df['fcf'] = fcfa_df['영업활동으로인한현금흐름'] - (fcfa_df['*유형자산순취득액'] + fcfa_df['*무형자산순취득액'])
    fcfa_df = fcfa_df.pivot_table(values=['fcf', '총자산'], index='stock_cd', columns='year')
    fcfa_df.columns = fcfa_df.columns.map('_'.join)
    fcfa_df['fcf_sum'] = fcfa_df.filter(regex='^fcf').sum(axis=1)
    fcfa_df['fcfa'] = fcfa_df['fcf_sum'] / fcfa_df['총자산_'+str(year)]
    fcfa_df = fcfa_df.sort_values('fcfa', ascending=False)
    fcfa_df = fcfa_df.reset_index()
    return fcfa_df

def mg_screener(year, period=1):
    mg_df = get_fs(account_nm=['매출액', '매출총이익', '영업수익', '영업이익'], year=year, period=period+1)
    mg_df = mg_df.pivot_table(index=['stock_cd', 'year'], columns='account_nm', values='fs_value')
    mg_df['gm'] = np.where(
        mg_df.매출액 != mg_df.매출총이익, 
        np.round(mg_df.매출총이익 / mg_df.매출액, 4), 
        np.round(mg_df.영업이익 / mg_df.영업수익, 4)
    )    # gross margin (단, 매출액과 매출총이익 항목없이 영업수익과 영업이익만 보여주는 종목은 영업이익률 사용)
    mg_df = mg_df.pivot_table(index='stock_cd', columns='year', values='gm')
    mg_df = mg_df.dropna()  # 매출총이익률을 계산할 수 있는 종목만 필터링
    mg_df = mg_df[(mg_df > 0).all(1)] # 매출총이익이 적자인 종목은 제외
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

def ete_screener(year, mkt_cap_date):
    kor_fs = get_fs(account_nm=['*순차입부채', '영업이익'], year=year, period=1)
    kor_fs = kor_fs.pivot_table(index = 'stock_cd', columns='account_nm', values='fs_value')
    kor_mkt_cap = get_mkt_cap(mkt_cap_date)    # 시가총액 기준일자 설정
    ete_df = pd.merge(kor_fs, kor_mkt_cap, left_on=kor_fs.index, right_on='stock_cd', how='inner')
    ete_df.rename(columns={'*순차입부채':'net_debt', '영업이익':'ebit'}, inplace=True)
    ete_df = ete_df[['stock_cd', 'ebit', 'net_debt', 'mkt_cap']]
    ete_df['net_debt'] = ete_df.net_debt / 1000
    ete_df['ebit'] = ete_df.ebit / 1000
    ete_df['ev'] = ete_df.net_debt + ete_df.mkt_cap
    ete_df['ev'] = np.where(ete_df.ev<0, 1, ete_df.ev)    # 보유 현금 및 단기금융상품이 많아 순차입부채가 (-)인 경우 EV가 (-)가 되는 경우도 발생. 이 경우 EV를 1로 설정하여 영업이익이 높은 순으로 순위를 매김
    ete_df['ete'] = np.round(ete_df.ebit / ete_df.ev, 4)
    ete_df = ete_df.sort_values('ete', ascending=False)
    ete_df = ete_df.reset_index(drop=True)
    return ete_df

def fscore_rawdata(year):
    account_nm_list = [
        '당기순이익',
        '총자산',
        '영업활동으로인한현금흐름',
        '*유형자산순취득액',
        '*무형자산순취득액',
        '장기차입금',
        '유동자산',
        '유동부채',
        '자본의증가(감소)',
        '매출총이익',
        '매출액'
    ]
    fscore_df = get_fs(account_nm=account_nm_list, year=year, period=2)
    fscore_df = fscore_df.pivot_table(values='fs_value', index=['stock_cd', 'year'], columns='account_nm')
    fscore_df['roa'] = fscore_df['당기순이익'] / fscore_df['총자산']
    fscore_df['fcfa'] = (fscore_df['영업활동으로인한현금흐름'] - (fscore_df['*유형자산순취득액'] + fscore_df['*무형자산순취득액'])) / fscore_df['총자산']
    fscore_df['accrual'] = fscore_df['fcfa'] - fscore_df['roa']
    fscore_df['lev'] = fscore_df['장기차입금'] / fscore_df['총자산']
    fscore_df['liq'] = fscore_df['유동자산'] / fscore_df['유동부채']
    fscore_df['offer'] = fscore_df['자본의증가(감소)']
    fscore_df['margin'] = fscore_df['매출총이익'] / fscore_df['매출액']
    fscore_df['turn'] = fscore_df['매출액'] / fscore_df['총자산']
    fscore_df = fscore_df[['roa', 'fcfa', 'accrual', 'lev', 'liq', 'offer', 'margin', 'turn']]
    fscore_df = fscore_df.unstack()
    fscore_df = fscore_df.dropna()
    return fscore_df

def fscore_screener(year):    
    fscore_df = fscore_rawdata(year)
    # 현재 수익성
    fscore_df['f_1'] = np.where(fscore_df.loc[:, ('roa', str(year))] > 0, 1, 0)
    fscore_df['f_2'] = np.where(fscore_df.loc[:, ('fcfa', str(year))] > 0, 1, 0)
    fscore_df['f_3'] = np.where(fscore_df.loc[:, ('accrual', str(year))] > 0, 1, 0)

    #안정성
    fscore_df['f_4'] = np.where(
        fscore_df.loc[:, ('lev', str(year))] 
        - fscore_df.loc[:, ('lev', str(year-1))] <= 0, 1, 0
    )
    fscore_df['f_5'] = np.where(
        fscore_df.loc[:, ('liq', str(year))] 
        - fscore_df.loc[:, ('liq', str(year-1))] > 0, 1, 0
    )
    fscore_df['f_6'] = np.where(fscore_df.loc[:, ('offer', str(year))] <= 0, 1, 0)

    # 최근 영업 호전성
    fscore_df['f_7'] = np.where(
        fscore_df.loc[:, ('roa', str(year))] 
        - fscore_df.loc[:, ('roa', str(year-1))] > 0, 1, 0
    )
    fscore_df['f_8'] = np.where(
        fscore_df.loc[:, ('fcfa', str(year))] 
        - fscore_df.loc[:, ('fcfa', str(year-1))] > 0, 1, 0
    )
    fscore_df['f_9'] = np.where(
        fscore_df.loc[:, ('margin', str(year))] 
        - fscore_df.loc[:, ('margin', str(year-1))] > 0, 1, 0
    )
    fscore_df['f_10'] = np.where(
        fscore_df.loc[:, ('turn', str(year))] 
        - fscore_df.loc[:, ('turn', str(year-1))] > 0, 1, 0
    )
    fscore_df['fscore'] = fscore_df.loc[:, 'f_1':'f_10'].sum(axis=1)
    fscore_df = fscore_df['fscore']
    fscore_df = fscore_df.reset_index()
    fscore_df = fscore_df.sort_values('fscore', ascending=False)
    fscore_df = fscore_df.reset_index(drop=True)
    return fscore_df

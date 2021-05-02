# %%
import os
project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')
import sys
sys.path.append(project_path)

# %%
from screener.stock_screener import *
import pandas as pd
import numpy as np
import sqlite3

# %%
def qv_portfolio_screener(year, period=3):
    # 0. 매년 4월말에 직전연도 재무제표를 기준으로 종목선정
    # 1. 투자 유니버스 : 금융주를 제외하고 과거 3년 실적이 존재하는 기업
    universe = get_listed_stock(str(year-period)+'-01-01', str(year)+'-04-30', no_fin=True)
    # 2. Price
    ete_df = ete_screener(fiscal_year=year-1, mkt_cap_date=str(year)+'-04-30')
    ete_df = pd.merge(universe, ete_df, how='left', on='stock_cd')
    ete_df['price'] = np.round(ete_df['ete'].rank(pct=True), 5)
    # 3. Quality
    # 3-1. 경제적해자
    # 3-1-1. ROA(3)
    roa_df = roa_screener(fiscal_year=year-1, period=period)
    roa_df = pd.merge(universe, roa_df, how='left', on='stock_cd')
    roa_df['p_roa'] = np.round(roa_df['roa_gmean'].rank(pct=True), 5)
    # 3-1-2. ROIC(3)
    roic_df = roic_screener(fiscal_year=year-1, period=period)
    roic_df = pd.merge(universe, roic_df, how='left', on='stock_cd')
    roic_df['p_roic'] = np.round(roic_df['roic_gmean'].rank(pct=True), 5)
    # 3-1-3. 장기 FCFA
    fcfa_df = fcfa_screener(fiscal_year=year-1, period=period)
    fcfa_df = pd.merge(universe, fcfa_df, how='left', on='stock_cd')
    fcfa_df['p_fcfa'] = np.round(fcfa_df['fcfa'].rank(pct=True), 5)
    # 3-1-4. Margin Max
    mm_df = mg_screener(fiscal_year=year-1, period=period)
    mm_df = pd.merge(universe, mm_df, how='left', on='stock_cd')
    mm_df['p_mm'] = np.round(mm_df['mm'].rank(pct=True), 5)
    # 3-2. FS_Score
    fscore_df = fscore_screener(fiscal_year=year-1)
    fscore_df['p_fs'] = fscore_df['fscore'] / 10

    result_df = universe
    result_df = pd.merge(result_df, ete_df[['stock_cd', 'price']], how='left', on='stock_cd')
    result_df = pd.merge(result_df, roa_df[['stock_cd', 'p_roa']], how='left', on='stock_cd')
    result_df = pd.merge(result_df, roic_df[['stock_cd', 'p_roic']], how='left', on='stock_cd')
    result_df = pd.merge(result_df, fcfa_df[['stock_cd', 'p_fcfa']], how='left', on='stock_cd')
    result_df = pd.merge(result_df, mm_df[['stock_cd', 'p_mm']], how='left', on='stock_cd')
    result_df['p_fp'] = np.round(result_df.iloc[:, 4:].mean(axis=1), 5)
    result_df = pd.merge(result_df, fscore_df[['stock_cd', 'p_fs']], how='left', on='stock_cd')
    result_df['quality'] = np.round(0.5 * result_df['p_fp'] + 0.5 * result_df['p_fs'], 5)
    result_df = result_df.dropna()
    result_df = result_df.sort_values(['price', 'quality'], ascending=False)
    result_df = result_df.reset_index()
    result_df = result_df[['stock_cd', 
                           'stock_nm', 
                           'fn_ind_nm', 
                           'price', 
                           'quality', 
                           'p_fp', 
                           'p_roa', 
                           'p_roic', 
                           'p_fcfa', 
                           'p_mm', 
                           'p_fs'
    ]]
    return result_df

# %%
qv_port_all = pd.DataFrame()
for year in range(2020, 2021):
    qv_port_year = qv_portfolio_screener(year)
    qv_port_year['year'] = year
    first_col = qv_port_year.pop('year')
    qv_port_year.insert(0, 'year', first_col)
    qv_port_all = qv_port_all.append(qv_port_year, ignore_index=True)

# %%
dtype = {
    'year': 'INTEGER',
    'stock_cd': 'TEXT',
    'stock_nm': 'TEXT',
    'fn_ind_nm': 'TEXT',
    'price': 'REAL',
    'quality': 'REAL',
    'p_fp': 'REAL',
    'p_roa': 'REAL',
    'p_roic': 'REAL',
    'p_fcfa': 'REAL',
    'p_mm': 'REAL',
    'p_fs': 'REAL'  
}
con = sqlite3.connect('./data/kor_stock.db')
qv_port_all.to_sql('kor_qv_portfolio', con, if_exists='replace', index=False, dtype=dtype)
con.close()

# %%
from stock_screener import *
import pandas as pd
import sqlite3

# %%
universe = get_listed_stock(2019, period=5)

# %%
# 1. Price
ete_df = ete_screener(2019, mkt_cap_date='2020-06-11')
ete_df = pd.merge(universe, ete_df, how='left', on='stock_cd')
ete_df['p_ete'] = ete_df['ete'].rank(pct=True)

# %%
# 2. Quality
# 2-1. 경제적해자
# 2-1-1. ROA(5)
roa_df = roa_screener(2019, period=5)
roa_df = pd.merge(universe, roa_df, how='left', on='stock_cd')
roa_df['p_roa'] = roa_df['roa_gmean'].rank(pct=True)

# %%
# 2-1-2. ROIC(5)
roic_df = roic_screener(2019, period=5)
roic_df = pd.merge(universe, roic_df, how='left', on='stock_cd')
roic_df['p_roic'] = roic_df['roic_gmean'].rank(pct=True)

# %%
# 2-1-3. 장기 FCFA
fcfa_df = fcfa_screener(2019, period=5)
fcfa_df = pd.merge(universe, fcfa_df, how='left', on='stock_cd')
fcfa_df['p_fcfa'] = fcfa_df['fcfa'].rank(pct=True)

# %%
# 2-1-4. Margin Max
mm_df = mg_screener(2019, period=5)
mm_df = pd.merge(universe, mm_df, how='left', on='stock_cd')
mm_df['p_mm'] = mm_df['mm'].rank(pct=True)

# %%
fscore_df = fscore_screener(2019)
fscore_df['p_fs'] = fscore_df['fscore'] / 10

# %%
result = universe
result = pd.merge(result, ete_df[['stock_cd', 'p_ete']], how='left', on='stock_cd')
result = pd.merge(result, roa_df[['stock_cd', 'p_roa']], how='left', on='stock_cd')
result = pd.merge(result, roic_df[['stock_cd', 'p_roic']], how='left', on='stock_cd')
result = pd.merge(result, fcfa_df[['stock_cd', 'p_fcfa']], how='left', on='stock_cd')
result = pd.merge(result, mm_df[['stock_cd', 'p_mm']], how='left', on='stock_cd')
result['p_fp'] = result.iloc[:, 2:].mean(axis=1)
result = pd.merge(result, fscore_df[['stock_cd', 'p_fs']], how='left', on='stock_cd')
result['quality'] = 0.5 * result['p_fp'] + 0.5 * result['p_fs']
result = result.rename(columns={'p_ete':'price'})
result = result.dropna()
result = result[result['price'] > 0.9].sort_values('quality', ascending=False)

con = sqlite3.connect('./data/kor_stock.db')
sql = "SELECT * FROM kor_ticker"
ticker = pd.read_sql(sql, con)
con.close()

result = pd.merge(result, ticker[['stock_cd', 'stock_nm']], how='left', on='stock_cd')
result = result[['stock_cd', 'stock_nm', 'price', 'quality', 'p_fp', 'p_roa', 'p_roic', 'p_fcfa', 'p_mm', 'p_fs']]

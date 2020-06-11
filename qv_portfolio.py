# %%
from stock_screener import *
import pandas as pd

# %%
universe = get_listed_stock(2018, period=5)

# %%
# 1. Price
ete_df = ete_screener(2018, mkt_cap_date='2019-06-30')
ete_df = pd.merge(universe, ete_df, how='left', on='stock_cd')
ete_df['p_ete'] = ete_df['ete'].rank(ascending=False, pct=True)

# %%
# 2. Quality
# 2-1. 경제적해자
# 2-1-1. ROA(5)
roa_df = roa_screener(2018, period=5)
roa_df = pd.merge(universe, roa_df, how='left', on='stock_cd')
roa_df['p_roa'] = roa_df['roa_gmean'].rank(ascending=False, pct=True)

# %%
# 2-1-2. ROIC(5)
roic_df = roic_screener(2018, period=5)
roic_df = pd.merge(universe, roic_df, how='left', on='stock_cd')
roic_df['p_roic'] = roic_df['roic_gmean'].rank(ascending=False, pct=True)

# %%
# 2-1-3. 장기 FCFA
fcfa_df = fcfa_screener(2018, period=5)
fcfa_df = pd.merge(universe, fcfa_df, how='left', on='stock_cd')
fcfa_df['p_fcfa'] = fcfa_df['fcfa'].rank(ascending=False, pct=True)

# %%
# 2-1-4. Margin Max
mm_df = mg_screener(2018, period=5)
mm_df = pd.merge(universe, mm_df, how='left', on='stock_cd')
mm_df['p_mm'] = mm_df['mm'].rank(ascending=False, pct=True)

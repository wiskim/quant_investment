# %%
import os
project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')
import sys
sys.path.append(project_path)

# %%
from screener.stock_screener import *
import numpy as np
import pandas as pd
import sqlite3
# %%
kor_fs = get_fs(item_nm=['지배기업주주지분'], fiscal_year=2019, period=1, con_div='Consolidated')
# %%
kor_mkt_cap = get_mkt_cap('2019-12-31')
# %%
kor_pbr = pd.merge(kor_fs[['stock_cd', 'stock_nm', 'item_value']], 
                   kor_mkt_cap[['stock_cd', 'mkt_cap']],
                   on='stock_cd',
                   how='outer')
kor_pbr = kor_pbr.rename(columns={'item_value':'book_value'})
# %%
kor_pbr['pbr'] = np.round((kor_pbr['mkt_cap'] * 1000) / kor_pbr['book_value'], 4)
# %%
kor_ticker = get_listed_stock('2019-12-31', '2019-12-31', no_fin=True)
# %%
kor_pbr = pd.merge(kor_ticker[['stock_cd']], kor_pbr, on='stock_cd', how='left')
# %%

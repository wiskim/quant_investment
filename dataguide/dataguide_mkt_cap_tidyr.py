import os
project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')

import pandas as pd
import numpy as np
df = pd.read_csv(os.path.join(data_path, 'dataguide_mkt_cap.csv'), index_col=[0, 1, 2, 3, 4, 5])
df = df.stack().reset_index()
df.columns = ['stock_cd', 'stock_nm', 'kind', 'item', 'item_nm', 'freq', 'date', 'item_value']
df['item_nm'] = df['item_nm'].replace({
    '상장주식수 (보통)(주)' : 'no_common',
    '상장주식수 (우선)(주)' : 'no_preferred',
    '상장예정주식수 (보통)(주)' : 'tb_no_common',
    '상장예정주식수 (우선)(주)' : 'tb_no_preferred',
    '자기주식수 (보통)(주)' : 'no_treasury_common',
    '자기주식수 (우선)(주)' : 'no_treasury_preferred',
    '시가총액 (보통-상장예정주식수 포함)(백만원)' : 'mkt_cap_common',
    '시가총액 (우선-상장예정주식수 포함)(백만원)' : 'mkt_cap_preferred'
})
df['unit'] = np.where(((df.item_nm == 'mkt_cap_common') | (df.item_nm == 'mkt_cap_preferred')), 1000000, 1)
df = df[['stock_cd', 'stock_nm', 'date', 'item_nm', 'unit', 'item_value']]

df.to_csv(os.path.join(data_path, 'dataguide_mkt_cap_tidyr.csv'), index=False)

import os
project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')

import pandas as pd
df = pd.read_csv(os.path.join(data_path, 'dataguide_adjusted.csv'), index_col=[0, 1, 2, 3, 4, 5])
df = df.stack().reset_index()
df.columns = ['stock_cd', 'stock_nm', 'kind', 'item', 'price_div', 'freq', 'date', 'price']
df['price_div'] = df['price_div'].replace({'수정주가(원)':'Adjusted'})
df = df[['stock_cd', 'stock_nm', 'date', 'price_div', 'price']]

df.to_csv(os.path.join(data_path, 'dataguide_adjusted_tidyr.csv'), index=False)

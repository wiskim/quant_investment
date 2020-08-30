import os
project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')

import pandas as pd
df = pd.read_csv(os.path.join(data_path, 'dataguide_price.csv'), header=[0, 1, 2, 3, 4, 5], index_col=0)
df = df.unstack().reset_index()
df.columns = ['stock_cd', 'stock_nm', 'kind', 'item', 'price_div', 'freq', 'date', 'price']
df['price_div'] = df['price_div'].replace({'시가(원)':'Open', '저가(원)':'Low', '고가(원)':'High', '종가(원)':'Close'})
df = df[['stock_cd', 'stock_nm', 'date', 'price_div', 'price']]

df.to_csv(os.path.join(data_path, 'dataguide_price_tidyr.csv'), index=False)

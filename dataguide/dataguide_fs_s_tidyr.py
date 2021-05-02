import os
project_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_path, 'data')

import pandas as pd
df = pd.read_csv(os.path.join(data_path, 'dataguide_fs_s.csv'), 
                 header = [0, 1], dtype = 'str')
id_vars = df.columns[:5].to_list()
df = df.melt(id_vars=id_vars)
df.columns = ['stock_cd', 'stock_nm', 'closing_month', 'fiscal_year', 
              'freq', 'item_cd', 'item_nm', 'item_value']
df['con_div'] = 'Seperated'                                                     # 연결/별도 구분
df['fiscal_quarter'] = ''                                                       # 분기 재무제표 구분
df['unit'] = 1000                                                               # 재무제표 금액 단위
df['item_nm'] = df.item_nm.str.replace('\(\*+\)', '', regex=True)               # 계정과목명 정리
df['item_nm'] = df.item_nm.str.replace('\*', '', regex=True)                    # 계정과목명 정리
df['item_nm'] = df.item_nm.str.replace('\(천원\)', '', regex=True)              # 계정과목명 정리
df['item_cd'] = df.item_cd.str.slice(start=4)                                   # fs_item_info 테이블과 계정과목 코드 자릿수 일치
df = df.loc[~df.item_nm.isin(['113903', '113904', '112503', '112504']), ]       # fs_item_info 테이블에 존재하지 않는 계정과목 삭제
df = df[['con_div', 'stock_cd', 'stock_nm', 'closing_month', 'freq', 
         'fiscal_year', 'fiscal_quarter', 'item_cd', 'item_nm', 'unit', 
         'item_value']]

df.to_csv(os.path.join(data_path, 'dataguide_fs_s_tidyr.csv'), index=False)

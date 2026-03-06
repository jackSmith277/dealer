import pandas as pd

excel_path = '地方促消费政策列表-202410-未整理.xlsx'

try:
    df = pd.read_excel(excel_path)
    print('列名:')
    print(df.columns.tolist())
    print('\n前5行数据:')
    print(df.head())
except Exception as e:
    print(f'读取Excel文件失败: {str(e)}')

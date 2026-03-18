
from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import json

app = Flask(__name__)

# 加载数据
def load_data():
    file_path = '24年13维度数据.xlsx'  # 更改为你的文件路径
    xls = pd.ExcelFile(file_path)
    data = {}
    for sheet_name in xls.sheet_names:
        data[sheet_name] = xls.parse(sheet_name)
    return data

data = load_data()


@app.route('/line-chart')
def line_chart():
    # 提取所有经销商代码和维度名称
    dealers = data['各月销量']['经销商代码'].unique()
    dimensions = list(data.keys())
    # 加载 line-chart.html 模板
    return render_template('line-chart.html', dealers=dealers, dimensions=dimensions)

@app.route('/plot', methods=['POST'])
def plot():
    dealer_code = request.form['dealer']
    dimension = request.form['dimension']

    # 提取数据并构造图表
    df = data[dimension]
    dealer_data = df[df['经销商代码'] == dealer_code]

    if dealer_data.empty:
        return jsonify({'message': '该维度无数据'})

    months = dealer_data.columns[3:]
    x_values = [col.split('月')[0] + '月' for col in months]
    y_values = dealer_data.iloc[0, 3:].fillna(0).values

    # 构造符合 Plotly 格式的数据
    fig = {
        "data": [
            {
                "x": x_values,
                "y": y_values.tolist(),  # 确保 y 值是列表
                "type": "scatter",
                "mode": "lines+markers",
                "name": "销量数据"
            }
        ],
        "layout": {
            "title": f"经销商 {dealer_code} - {dimension}",
            "xaxis": {"title": "月份"},
            "yaxis": {"title": "销量"}
        }
    }

    # print("返回的图表数据:", json.dumps(fig, indent=4))  # 打印返回的数据
    return jsonify(fig)


if __name__ == '__main__':
    app.run(port=5001)

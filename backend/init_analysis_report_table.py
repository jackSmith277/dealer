"""
初始化 analysis_report 表的脚本
运行此脚本将在数据库中创建 analysis_report 表
"""

from app import app, db, AnalysisReport

def init_table():
    with app.app_context():
        # 删除旧表（如果存在）
        db.drop_all(bind_key=None, tables=[AnalysisReport.__table__])
        
        # 创建新的 analysis_report 表
        db.create_all()
        print("✓ analysis_report 表创建成功！")
        
        # 显示表结构
        print("\n表结构:")
        print("- id: 主键，自增")
        print("- username: 生成报告的用户名")
        print("- dealer_code: 经销商代码（来自经销商选择器）")
        print("- report_date: 报告生成日期")
        print("- selected_cards: 选中的卡片（JSON格式）")
        print("- report_content: 报告内容（Markdown格式）")
        print("\n注意：已删除 created_at 字段，添加了 username 字段")

if __name__ == '__main__':
    init_table()

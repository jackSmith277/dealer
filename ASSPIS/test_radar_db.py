"""
测试数据库版本的 radar 功能
"""
import sys
sys.path.insert(0, '.')

from radar import (
    load_radar_source_from_db,
    get_scores_dataframe_from_db,
    plot_dealers_radar,
    dealers_score,
    save_scores_to_db,
)

print("="*60)
print("测试数据库版本 radar 功能")
print("="*60)

print("\n1. 测试 load_radar_source_from_db()...")
try:
    source_df = load_radar_source_from_db(year=2024)
    print(f"   成功读取 {len(source_df)} 条原始数据")
    print(f"   列数: {len(source_df.columns)}")
    print(f"   示例经销商: {source_df['经销商代码'].head(3).tolist()}")
except Exception as e:
    print(f"   失败: {e}")

print("\n2. 测试 get_scores_dataframe_from_db()...")
try:
    scores_df = get_scores_dataframe_from_db(
        year=2024,
        prefer_db=True,
        refresh=True,
        persist_to_db=True,
        calc_version='v1.0_db_test',
    )
    print(f"   成功计算 {len(scores_df)} 条五力结果")
    print(f"   列数: {len(scores_df.columns)}")
except Exception as e:
    print(f"   失败: {e}")

print("\n3. 测试 dealers_score() 使用数据库...")
try:
    result = dealers_score(
        dealer_codes=['9210006', '9210007'],
        month=1,
        use_db=True,
        db_year=2024,
    )
    print(f"   成功获取 {len(result)} 个经销商的分数")
    for code, scores in result.items():
        print(f"   {code}: {scores}")
except Exception as e:
    print(f"   失败: {e}")

print("\n4. 测试 plot_dealers_radar() 使用数据库...")
try:
    img_path = plot_dealers_radar(
        dealer_codes=['9210006'],
        month=1,
        use_db=True,
        db_year=2024,
    )
    print(f"   成功生成雷达图: {img_path}")
except Exception as e:
    print(f"   失败: {e}")

print("\n" + "="*60)
print("测试完成")
print("="*60)

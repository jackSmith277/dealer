# 汽车评论分析 Demo

## 功能

- 前端输入评论页 URL
- 后端调用 `新爬取.py` 抓取评论
- 后端调用 `评论分析.py` 生成 Markdown 报告和汇总 Excel
- 前端展示部分评论预览和完整分析报告

## 启动

```bat
start.bat
```

或手动运行：

```bat
python app.py
```

启动后访问：

```text
http://127.0.0.1:8000
```

## 输出

每次分析都会在 `runtime/时间戳/` 下生成：

- `reviews.xlsx`
- `reviews.json`
- `review_analysis_report.md`
- `review_analysis_summary.xlsx`

## 说明

- 默认复用上级目录里的 `新爬取.py` 和 `评论分析.py`
- 目标目录结构建议保持为：`汽车服务\测试\app.py`
- 如果抓取失败，优先检查 URL 是否为公开评论页，以及本机是否已安装可被 Playwright 调用的浏览器

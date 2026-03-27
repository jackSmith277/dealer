from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from types import ModuleType

import pandas as pd
import numpy as np
from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent


def resolve_source_dir() -> Path:
    parent = BASE_DIR.parent
    if (parent / "新爬取.py").exists() and (parent / "评论分析.py").exists():
        return parent
    candidate = parent / "汽车服务"
    if (candidate / "新爬取.py").exists() and (candidate / "评论分析.py").exists():
        return candidate
    return parent


SOURCE_DIR = resolve_source_dir()
SCRAPER_PATH = SOURCE_DIR / "新爬取.py"
ANALYZER_PATH = SOURCE_DIR / "评论分析.py"
RUNTIME_DIR = BASE_DIR / "runtime"

app = Flask(__name__, static_folder="static", static_url_path="/static")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def load_module(module_name: str, file_path: Path, strip_after: str | None = None):
    source = file_path.read_text(encoding="utf-8")
    if strip_after and strip_after in source:
        source = source.split(strip_after, 1)[0]
    module = ModuleType(module_name)
    module.__file__ = str(file_path)
    sys.modules[module_name] = module
    exec(compile(source, str(file_path), "exec"), module.__dict__)
    return module


def ensure_runtime_dirs() -> dict[str, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNTIME_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    return {
        "run_dir": run_dir,
        "excel": run_dir / "reviews.xlsx",
        "report": run_dir / "review_analysis_report.md",
        "summary_excel": run_dir / "review_analysis_summary.xlsx",
        "reviews_json": run_dir / "reviews.json",
    }


def read_excel_file(file_path: Path) -> dict[str, pd.DataFrame]:
    suffix = file_path.suffix.lower()
    engine = "xlrd" if suffix == ".xls" else "openpyxl"
    excel = pd.ExcelFile(file_path, engine=engine)
    return {sheet_name: pd.read_excel(file_path, sheet_name=sheet_name, engine=engine) for sheet_name in excel.sheet_names}


class DataCleaningTool:
    def run(self, parameters: dict) -> str:
        data_json = parameters.get("data_json")
        if not data_json:
            return "错误：缺少原始数据"
        try:
            raw_data = json.loads(data_json)
            records = raw_data.get("完整数据", raw_data.get("data", []))
            if not records:
                return "警告：原始数据为空"
            df = pd.DataFrame(records)
            columns_to_keep = parameters.get("columns_to_keep")
            if columns_to_keep:
                df = df[columns_to_keep]
            if parameters.get("drop_na", False):
                df = df.dropna()
            df = df.fillna(0)
            cleaned_records = df.where(pd.notnull(df), None).to_dict(orient="records")
            return json.dumps({"clean_data": cleaned_records}, ensure_ascii=False, indent=2)
        except Exception as exc:
            return f"清洗出错：{exc}"


class DataStatisticsTool:
    def run(self, parameters: dict) -> str:
        data_json = parameters.get("data_json")
        if not data_json:
            return "错误：缺少数据"
        try:
            raw_data = json.loads(data_json)
            records = raw_data.get("clean_data", raw_data.get("data", []))
            df = pd.DataFrame(records)
            numeric_stats = {}
            for col in df.select_dtypes(include=[np.number]).columns:
                numeric_stats[str(col)] = {
                    "count": int(df[col].count()),
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()) if pd.notna(df[col].std()) else 0.0,
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                }
            categorical_stats = {}
            for col in df.select_dtypes(include=["object"]).columns:
                categorical_stats[str(col)] = {
                    "unique_count": int(df[col].nunique()),
                    "top_values": df[col].astype(str).value_counts().head(10).to_dict(),
                }
            result = {
                "shape": f"{len(df)} 行，{len(df.columns)} 列",
                "numeric_stats": numeric_stats,
                "categorical_stats": categorical_stats,
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            return f"统计出错：{exc}"


def preview_markdown(df: pd.DataFrame, limit: int = 5) -> str:
    preview = df.head(limit).fillna("")
    if preview.empty:
        return "无可预览数据。"
    headers = [str(col) for col in preview.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in preview.iterrows():
        values = [str(value).replace("\n", " ").replace("|", "\\|") for value in row.tolist()]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_key_findings(df: pd.DataFrame, stats: dict) -> list[str]:
    findings: list[str] = []
    numeric_stats = stats.get("numeric_stats", {})
    categorical_stats = stats.get("categorical_stats", {})

    for col, item in list(numeric_stats.items())[:4]:
        spread = item["max"] - item["min"]
        findings.append(
            f"`{col}` 的均值为 `{item['mean']:.2f}`，中位数为 `{item['median']:.2f}`，区间跨度为 `{spread:.2f}`。"
        )

    for col, item in list(categorical_stats.items())[:2]:
        top_values = item.get("top_values", {})
        if top_values:
            top_label = next(iter(top_values.keys()))
            top_count = top_values[top_label]
            findings.append(f"`{col}` 共出现 `{item['unique_count']}` 个不同取值，其中 `{top_label}` 最常见，出现 `{top_count}` 次。")

    if not findings:
        findings.append("该表以文本列为主，暂无足够数值字段进行深入统计。")
    return findings


def build_trend_analysis(df: pd.DataFrame) -> list[str]:
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if len(numeric_cols) < 2:
        return ["未识别到足够的数值列，暂不生成趋势分析。"]

    first_col = df.columns[0]
    trend_lines: list[str] = []
    for _, row in df.head(6).iterrows():
        values = [(col, row[col]) for col in numeric_cols if pd.notna(row[col])]
        if len(values) < 2:
            continue
        start_col, start_val = values[-1]
        end_col, end_val = values[0]
        delta = float(end_val) - float(start_val)
        direction = "上升" if delta > 0 else "下降" if delta < 0 else "持平"
        trend_lines.append(
            f"`{row[first_col]}` 从 `{start_col}` 的 `{float(start_val):.2f}` 变化到 `{end_col}` 的 `{float(end_val):.2f}`，整体呈 `{direction}` 趋势。"
        )
    return trend_lines or ["未生成有效趋势分析。"]


def build_markdown_report(file_name: str, sheet_name: str, df: pd.DataFrame, clean_data: dict, stats: dict) -> str:
    findings = build_key_findings(df, stats)
    trends = build_trend_analysis(df)
    numeric_stats = stats.get("numeric_stats", {})

    stat_lines = [
        "| 列名 | 均值 | 中位数 | 标准差 | 最小值 | 最大值 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for col, item in list(numeric_stats.items())[:8]:
        stat_lines.append(
            f"| {col} | {item['mean']:.2f} | {item['median']:.2f} | {item['std']:.2f} | {item['min']:.2f} | {item['max']:.2f} |"
        )
    if len(stat_lines) == 2:
        stat_lines.append("| 无数值列 | - | - | - | - | - |")

    return "\n".join(
        [
            "# 数据分析报告",
            "",
            "## 分析背景与目标",
            "",
            f"本次分析基于文件 `{file_name}` 中的工作表 `{sheet_name}` 展开，目标是对数据进行清洗、统计概览与趋势识别，并输出适合前端展示的 Markdown 报告。",
            "",
            "## 数据概况",
            "",
            f"- 数据规模：`{stats.get('shape', f'{len(df)} 行，{len(df.columns)} 列')}`",
            f"- 原始字段：`{'`, `'.join(map(str, df.columns.tolist()))}`",
            f"- 清洗后记录数：`{len(clean_data.get('clean_data', []))}`",
            "",
            "## 数据预览",
            "",
            preview_markdown(df),
            "",
            "## 关键发现",
            "",
            "\n".join(f"- {item}" for item in findings),
            "",
            "## 统计计算结果",
            "",
            "\n".join(stat_lines),
            "",
            "## 趋势识别与对比分析",
            "",
            "\n".join(f"- {item}" for item in trends),
            "",
            "## 结论与建议",
            "",
            "- 若该表用于月度对比，可重点关注波动幅度最大的指标，并结合业务背景解释变化原因。",
            "- 若该表用于展示看板，建议优先把数值列均值、最大值、最小值和趋势方向做成图表。",
            "- 当前报告为结构化快速分析版，适合作为前端预览和进一步深度分析的基础。",
        ]
    ).strip() + "\n"


def analyze_excel_file(file_path: Path) -> dict:
    sheets = read_excel_file(file_path)
    if not sheets:
        raise RuntimeError("Excel 文件中没有可分析的工作表。")

    first_sheet_name = next(iter(sheets.keys()))
    df = sheets[first_sheet_name]
    data_records = df.to_dict(orient="records")
    sample_data = json.dumps({"完整数据": data_records}, ensure_ascii=False, indent=2)

    cleaner = DataCleaningTool()
    clean_result_text = cleaner.run({"data_json": sample_data, "drop_na": False})
    if clean_result_text.startswith("错误") or clean_result_text.startswith("警告") or clean_result_text.startswith("清洗出错"):
        raise RuntimeError(clean_result_text)
    clean_result = json.loads(clean_result_text)

    statistician = DataStatisticsTool()
    stats_result_text = statistician.run({"data_json": json.dumps(clean_result, ensure_ascii=False)})
    if stats_result_text.startswith("错误") or stats_result_text.startswith("统计出错"):
        raise RuntimeError(stats_result_text)
    stats_result = json.loads(stats_result_text)

    markdown_report = build_markdown_report(file_path.name, first_sheet_name, df, clean_result, stats_result)

    summary = {
        "sheet_count": len(sheets),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "sheet_names": list(sheets.keys()),
    }

    return {
        "ok": True,
        "markdown_report": markdown_report,
        "echarts": None,
        "summary": summary,
    }


def scrape_reviews(target_url: str, max_items: int) -> tuple[list[dict[str, str]], Path]:
    scraper = load_module("car_review_scraper_runtime", SCRAPER_PATH, strip_after="class Solution(object):")
    paths = ensure_runtime_dirs()
    browser_path, browser_channel = scraper.detect_local_browser()
    site = scraper.detect_site(target_url, None)
    reviews = scraper.scrape_url(
        url=target_url,
        site=site,
        max_items=max_items,
        max_pages=5,
        scroll_rounds=6,
        pause_seconds=1.5,
        headless=True,
        browser_executable=browser_path,
        browser_channel=browser_channel,
    )
    reviews = [scraper.normalize_review(review) for review in reviews]
    reviews.sort(key=scraper.review_sort_key, reverse=True)
    scraper.write_excel(str(paths["excel"]), [(target_url, reviews)])
    paths["reviews_json"].write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    return reviews, paths["run_dir"]


def analyze_reviews(run_dir: Path) -> tuple[str, Path]:
    analyzer = load_module("car_review_analyzer_runtime", ANALYZER_PATH)
    excel_path = run_dir / "reviews.xlsx"
    report_path = run_dir / "review_analysis_report.md"
    summary_excel_path = run_dir / "review_analysis_summary.xlsx"

    reviews_by_sheet = analyzer.load_reviews_by_sheet(str(excel_path))
    if not reviews_by_sheet:
        raise RuntimeError("没有读取到可分析的评论数据。")

    results = []
    for sheet_name, reviews in reviews_by_sheet.items():
        results.append(analyzer.analyze_sheet(sheet_name, reviews))

    markdown = analyzer.render_markdown(results)
    analyzer.write_text(str(report_path), markdown)
    analyzer.write_summary_excel(str(summary_excel_path), results)
    return markdown, report_path


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/analyze")
def api_analyze():
    payload = request.get_json(silent=True) or {}
    target_url = str(payload.get("url", "")).strip()
    max_items = int(payload.get("max_items", 20) or 20)

    if not target_url:
        return jsonify({"ok": False, "error": "请输入评论页 URL。"}), 400
    if not SCRAPER_PATH.exists():
        return jsonify({"ok": False, "error": f"未找到爬虫脚本: {SCRAPER_PATH}"}), 500
    if not ANALYZER_PATH.exists():
        return jsonify({"ok": False, "error": f"未找到分析脚本: {ANALYZER_PATH}"}), 500

    try:
        reviews, run_dir = scrape_reviews(target_url, max_items)
        if not reviews:
            return jsonify({"ok": False, "error": "没有爬取到评论，请检查 URL 是否为公开评论页。"}), 400

        markdown, report_path = analyze_reviews(run_dir)

        preview_reviews = []
        for item in reviews[:8]:
            preview_reviews.append(
                {
                    "user_name": item.get("user_name", ""),
                    "car_name": item.get("car_name", ""),
                    "rating": item.get("rating", ""),
                    "published_at": item.get("published_at", ""),
                    "content": item.get("content", ""),
                    "source_url": item.get("source_url", ""),
                }
            )

        return jsonify(
            {
                "ok": True,
                "url": target_url,
                "review_count": len(reviews),
                "preview_reviews": preview_reviews,
                "report_markdown": markdown,
                "report_file": str(report_path),
                "excel_file": str(run_dir / "reviews.xlsx"),
                "summary_excel_file": str(run_dir / "review_analysis_summary.xlsx"),
                "reviews_json_file": str(run_dir / "reviews.json"),
            }
        )
    except Exception as exc:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
        )


@app.route("/api/excel-report", methods=["POST", "OPTIONS"])
def api_excel_report():
    if request.method == "OPTIONS":
        return ("", 200)

    if "excel_file" not in request.files:
        return jsonify({"ok": False, "error": "未检测到上传的 Excel 文件。"}), 400

    excel_file = request.files["excel_file"]
    if not excel_file or not excel_file.filename:
        return jsonify({"ok": False, "error": "Excel 文件名为空。"}), 400

    suffix = Path(excel_file.filename).suffix.lower()
    if suffix not in {".xls", ".xlsx"}:
        return jsonify({"ok": False, "error": "仅支持 .xls 或 .xlsx 文件。"}), 400

    temp_dir = RUNTIME_DIR / f"excel_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / excel_file.filename

    try:
        excel_file.save(temp_path)
        analysis_result = analyze_excel_file(temp_path)
        analysis_result["success"] = analysis_result.get("ok", False)
        analysis_result["source_file"] = str(temp_path)
        return jsonify(analysis_result)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc), "traceback": traceback.format_exc()}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    app.run(host="127.0.0.1", port=8000, debug=True)

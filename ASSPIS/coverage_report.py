#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coverage_report.py
------------------
不改动数据集，仅输出“经销商参与率被哪个字段卡住”的统计报告。

用法示例：
  python coverage_report.py --data_dir data
  python coverage_report.py --files data/a.xlsx data/b.xlsx
  python coverage_report.py --min_base_signal 1

输出（默认写入 reports/）：
  - coverage_by_month.csv
  - missing_by_field_month.csv
  - blocking_fields_overall.csv
  - dealer_participation.csv
"""

import argparse
import os
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd

from dealer_data_preprocessing import load_and_process_data

BASE_FIELDS = [
    ("potential_customers", "潜客量"),
    ("test_drives", "试驾数"),
    ("leads", "线索量"),
    ("customer_flow", "客流量"),
    ("defeat_rate", "战败率"),
    ("success_rate", "成交率"),
    ("success_response_time", "成交响应时间"),
    ("defeat_response_time", "战败响应时间"),
    ("policy", "政策"),
    ("gsev", "GSEV"),
]

def make_time_key(year: int, month: int) -> int:
    return int(year) * 12 + (int(month) - 1)

def _is_present(v) -> bool:
    if v is None:
        return False
    try:
        if isinstance(v, float) and np.isnan(v):
            return False
    except Exception:
        pass
    return True

def _auto_find_excels(data_dir: str | None) -> List[str]:
    cands: List[Path] = []
    if data_dir:
        p = Path(data_dir)
        if p.exists() and p.is_dir():
            cands.extend(sorted(p.glob("*.xlsx")))
            cands.extend(sorted(p.glob("*.xls")))
            cands.extend(sorted(p.glob("*.xlsm")))

    # fallback: 常见目录
    if not cands:
        for d in ["data", "dataset", "datasets", "."]:
            p = Path(d)
            if p.exists() and p.is_dir():
                cands.extend(sorted(p.glob("*.xlsx")))
                cands.extend(sorted(p.glob("*.xls")))
                cands.extend(sorted(p.glob("*.xlsm")))
            if cands:
                break

    # 去重
    seen = set()
    out = []
    for fp in cands:
        ap = str(fp.resolve())
        if ap not in seen:
            seen.add(ap)
            out.append(ap)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="*", default=None, help="显式指定 Excel 文件路径列表")
    ap.add_argument("--data_dir", default=None, help="包含 Excel 的目录（自动搜 xlsx/xls/xlsm）")
    ap.add_argument("--out_dir", default="reports", help="输出目录")
    ap.add_argument("--min_base_signal", type=int, default=int(os.getenv("PHASE23_MIN_BASE_SIGNAL", "1")),
                    help="软门槛：当月原子特征可用数量 >= K 即认为可参与（默认取 PHASE23_MIN_BASE_SIGNAL 或 1）")
    args = ap.parse_args()

    if args.files and len(args.files) > 0:
        file_paths = args.files
    else:
        file_paths = _auto_find_excels(args.data_dir)

    if not file_paths:
        raise SystemExit("未找到 Excel 文件。请使用 --files 或 --data_dir 指定。")

    print("Using Excel files:")
    for fp in file_paths:
        print("  -", fp)

    dealers, dealer_codes = load_and_process_data(file_paths)

    # 收集所有 (year,month)：以 sales 为基准（解释“训练/评估覆盖”）
    months_set = set()
    for d in dealers.values():
        for k in getattr(d, "sales", {}).keys():
            if isinstance(k, tuple) and len(k) == 2:
                months_set.add((int(k[0]), int(k[1])))
    months = sorted(months_set, key=lambda ym: make_time_key(ym[0], ym[1]))
    if not months:
        raise SystemExit("未发现任何 (year,month) 销量键，请确认各月销量 sheet 是否读取成功。")

    # per dealer participation
    dealer_rows = []

    # per month stats
    cov_rows = []
    miss_rows = []
    block_counter_total = {f: 0 for f, _ in BASE_FIELDS}

    for (y, m) in months:
        # dealers that have sales that month
        sales_dealers = []
        sum_sales = 0.0
        for code, d in dealers.items():
            sv = getattr(d, "sales", {}).get((y, m), None)
            if _is_present(sv):
                sales_dealers.append(code)
                try:
                    sum_sales += float(sv)
                except Exception:
                    pass

        n_sales = len(sales_dealers)
        if n_sales == 0:
            continue

        strict_ok = 0
        soft_ok = 0

        # field missing counts among sales_dealers
        miss_cnt = {f: 0 for f, _ in BASE_FIELDS}
        # strict drop reasons: count missing fields among those with sales but not strict
        strict_drop_reason = {f: 0 for f, _ in BASE_FIELDS}

        for code in sales_dealers:
            d = dealers[code]
            present_cnt = 0
            missing_fields = []
            for f, _cn in BASE_FIELDS:
                mp = getattr(d, f, {})
                v = mp.get((y, m), None)
                ok = _is_present(v)
                if ok:
                    present_cnt += 1
                else:
                    miss_cnt[f] += 1
                    missing_fields.append(f)

            if present_cnt == len(BASE_FIELDS):
                strict_ok += 1
            else:
                for f in missing_fields:
                    strict_drop_reason[f] += 1

            if present_cnt >= max(0, int(args.min_base_signal)):
                soft_ok += 1

        # update global block counter (按 dealer-month 计数)
        for f, c in miss_cnt.items():
            block_counter_total[f] += int(c)

        tk = make_time_key(y, m)
        cov_rows.append({
            "year": y,
            "month": m,
            "time_key": tk,
            "n_with_sales": n_sales,
            "sum_sales": sum_sales,
            "n_strict_all10": strict_ok,
            "n_soft_k": soft_ok,
            "strict_rate": strict_ok / n_sales if n_sales else 0.0,
            "soft_rate": soft_ok / n_sales if n_sales else 0.0,
        })

        for f, cn in BASE_FIELDS:
            miss_rows.append({
                "year": y,
                "month": m,
                "time_key": tk,
                "field": f,
                "field_cn": cn,
                "missing_cnt": miss_cnt[f],
                "missing_rate": miss_cnt[f] / n_sales if n_sales else 0.0,
                "strict_drop_reason_cnt": strict_drop_reason[f],
                "strict_drop_reason_rate": strict_drop_reason[f] / n_sales if n_sales else 0.0,
            })

    # dealer-level participation across months with sales
    for code, d in dealers.items():
        months_with_sales = 0
        months_strict = 0
        months_soft = 0
        for (y, m) in months:
            sv = getattr(d, "sales", {}).get((y, m), None)
            if not _is_present(sv):
                continue
            months_with_sales += 1
            present_cnt = 0
            for f, _ in BASE_FIELDS:
                v = getattr(d, f, {}).get((y, m), None)
                if _is_present(v):
                    present_cnt += 1
            if present_cnt == len(BASE_FIELDS):
                months_strict += 1
            if present_cnt >= max(0, int(args.min_base_signal)):
                months_soft += 1
        dealer_rows.append({
            "dealer_code": code,
            "months_with_sales": months_with_sales,
            "months_strict_all10": months_strict,
            "months_soft_k": months_soft,
            "strict_rate": months_strict / months_with_sales if months_with_sales else 0.0,
            "soft_rate": months_soft / months_with_sales if months_with_sales else 0.0,
        })

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cov_df = pd.DataFrame(cov_rows).sort_values(["time_key"])
    miss_df = pd.DataFrame(miss_rows).sort_values(["time_key", "field"])
    dealer_df = pd.DataFrame(dealer_rows).sort_values(["months_with_sales", "soft_rate"], ascending=[False, False])

    # blocking fields overall
    block_df = pd.DataFrame([{
        "field": f,
        "field_cn": cn,
        "missing_cnt_total": int(block_counter_total[f]),
    } for f, cn in BASE_FIELDS]).sort_values("missing_cnt_total", ascending=False)

    cov_df.to_csv(out_dir / "coverage_by_month.csv", index=False, encoding="utf-8-sig")
    miss_df.to_csv(out_dir / "missing_by_field_month.csv", index=False, encoding="utf-8-sig")
    block_df.to_csv(out_dir / "blocking_fields_overall.csv", index=False, encoding="utf-8-sig")
    dealer_df.to_csv(out_dir / "dealer_participation.csv", index=False, encoding="utf-8-sig")

    print("\n=== Coverage summary (last 6 months) ===")
    print(cov_df.tail(6).to_string(index=False))

    print("\n=== Top blocking fields (overall) ===")
    print(block_df.head(10).to_string(index=False))

    # 2024 only quick view
    cov_2024 = cov_df[cov_df["year"] == 2024]
    if len(cov_2024) > 0:
        print("\n=== Coverage in 2024 (last 6 rows) ===")
        print(cov_2024.tail(6).to_string(index=False))

        miss_2024 = miss_df[miss_df["year"] == 2024].groupby(["field", "field_cn"], as_index=False)["missing_cnt"].sum()
        miss_2024 = miss_2024.sort_values("missing_cnt", ascending=False)
        print("\n=== Top missing fields in 2024 (sum over months) ===")
        print(miss_2024.head(10).to_string(index=False))

    print(f"\nSaved reports to: {out_dir.resolve()}")

if __name__ == "__main__":
    main()

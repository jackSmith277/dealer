# audit_dealers_completeness.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


# 10个当月原子字段（与 QuantileForecaster._latest_month_with_features 的维度一致）
REQUIRED_DIMS: List[Tuple[str, str]] = [
    ("potential_customers", "potential_customers"),
    ("test_drives", "test_drives"),
    ("leads", "leads"),
    ("customer_flow", "customer_flow"),
    ("defeat_rate", "defeat_rate"),
    ("success_rate", "success_rate"),
    ("success_response_time", "success_response_time"),
    ("defeat_response_time", "defeat_response_time"),
    ("policy", "policy"),
    ("gsev", "gsev"),
]


def _keys_of_map(obj: Any) -> Set[int]:
    """把 dealer_data.<dim> 的 key 取出来（如果不是 dict 就当缺失）"""
    if isinstance(obj, dict):
        out = set()
        for k in obj.keys():
            try:
                out.add(int(k))
            except Exception:
                pass
        return out
    return set()


@dataclass
class DealerAuditRow:
    dealer_code: str
    # base_month -> 缺失维度列表
    missing_dims_by_base_month: Dict[int, List[str]]
    # base_month -> 缺失目标月（sales缺失）列表
    missing_sales_targets_by_base_month: Dict[int, List[int]]
    # 该 dealer “特征齐全”的月份（10维交集）
    feature_complete_months: List[int]


def audit_dealers(
    dealers: Dict[str, Any],
    base_months: Iterable[int],
    horizons: Iterable[int],
    require_sales_targets: bool = True,
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """
    返回：
      complete_dealers: 在给定 base_months + horizons 约束下可用于评估的 dealer_code 列表
      incomplete_dealers: 不满足约束的 dealer_code 列表
      report: 详细报告（含每个dealer缺失维度、缺失target等）
    """
    base_months = [int(m) for m in base_months]
    horizons = [int(h) for h in horizons]

    audit_rows: List[DealerAuditRow] = []
    complete: List[str] = []
    incomplete: List[str] = []

    for code, d in dealers.items():
        dim_months: Dict[str, Set[int]] = {}
        for dim_name, attr in REQUIRED_DIMS:
            dim_months[dim_name] = _keys_of_map(getattr(d, attr, None))

        # 10维交集：哪些月份特征齐全
        common = None
        for dim_name, _ in REQUIRED_DIMS:
            if common is None:
                common = set(dim_months[dim_name])
            else:
                common &= set(dim_months[dim_name])
        common = common or set()

        sales_map = getattr(d, "sales", {}) if isinstance(getattr(d, "sales", {}), dict) else {}
        sales_months = _keys_of_map(sales_map)

        missing_dims_by_bm: Dict[int, List[str]] = {}
        missing_sales_targets_by_bm: Dict[int, List[int]] = {}

        ok_for_all_selected = True
        for bm in base_months:
            miss_dims = [dim for dim, _ in REQUIRED_DIMS if bm not in dim_months[dim]]
            missing_dims_by_bm[bm] = miss_dims

            miss_targets: List[int] = []
            if require_sales_targets:
                for h in horizons:
                    tm = bm + h
                    if tm not in sales_months:
                        miss_targets.append(tm)
            missing_sales_targets_by_bm[bm] = miss_targets

            # 若任何一个 base_month 缺维度或缺 target，就认为该 dealer 在本次评估协议下不可用
            if miss_dims or (require_sales_targets and miss_targets):
                ok_for_all_selected = False

        audit_rows.append(
            DealerAuditRow(
                dealer_code=code,
                missing_dims_by_base_month=missing_dims_by_bm,
                missing_sales_targets_by_base_month=missing_sales_targets_by_bm,
                feature_complete_months=sorted(common),
            )
        )

        if ok_for_all_selected:
            complete.append(code)
        else:
            incomplete.append(code)

    report = {
        "config": {
            "base_months": base_months,
            "horizons": horizons,
            "require_sales_targets": require_sales_targets,
            "required_dims": [d for d, _ in REQUIRED_DIMS],
        },
        "summary": {
            "n_total": len(dealers),
            "n_complete": len(complete),
            "n_incomplete": len(incomplete),
        },
        "complete_dealers": sorted(complete),
        "incomplete_dealers": sorted(incomplete),
        "details": [
            {
                "dealer_code": r.dealer_code,
                "missing_dims_by_base_month": r.missing_dims_by_base_month,
                "missing_sales_targets_by_base_month": r.missing_sales_targets_by_base_month,
                "feature_complete_months": r.feature_complete_months,
            }
            for r in audit_rows
        ],
    }
    return sorted(complete), sorted(incomplete), report


def audit_and_save(
    dealers: Dict[str, Any],
    base_months: Iterable[int],
    horizons: Iterable[int],
    out_json: str = "dealer_completeness_report.json",
    complete_json: str = "complete_dealers.json",
) -> List[str]:
    complete, incomplete, report = audit_dealers(
        dealers=dealers,
        base_months=base_months,
        horizons=horizons,
        require_sales_targets=True,
    )
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(complete_json, "w", encoding="utf-8") as f:
        json.dump({"complete_dealers": complete}, f, ensure_ascii=False, indent=2)

    print(f"[audit] wrote: {out_json}")
    print(f"[audit] wrote: {complete_json}")
    print(f"[audit] complete={len(complete)} / total={len(complete)+len(incomplete)}")
    return complete


if __name__ == "__main__":
    from pathlib import Path
    from dealer_data_preprocessing import load_and_process_data
    dealers, _ = load_and_process_data("1.xlsx")
    audit_and_save(dealers, base_months=range(1, 8), horizons=[1, 2])

    BASE_DIR = Path(__file__).resolve().parent
    xlsx_path = BASE_DIR / "1.xlsx"   # 与 main.py 保持一致

    if not xlsx_path.exists():
        candidates = list(BASE_DIR.glob("*.xlsx"))
        raise FileNotFoundError(f"找不到 {xlsx_path}；当前目录下 xlsx 候选: {candidates}")

    dealers, dealer_codes = load_and_process_data(str(xlsx_path))
    print(f"[audit] dealers loaded: {len(dealers)}")

    audit_and_save(dealers, base_months=range(1, 8), horizons=[1, 2])

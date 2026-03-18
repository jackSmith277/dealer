import copy
import numpy as np

from main import init_app, dealers, scaler  # 你若 main.py 不是可import结构，可把init逻辑单独抽出来
from quantile_forecast import QuantileForecaster
from model import build_features, _has_required_month_fields

def truncate_sales(dealers_dict, max_month: int):
    d2 = {}
    monthly_fields = [
        "sales", "potential_customers", "test_drives", "leads", "customer_flow",
        "defeat_rate", "success_rate", "success_response_time", "defeat_response_time",
        "policy", "gsev"
    ]
    for k, d in dealers_dict.items():
        dd = copy.deepcopy(d)
        for f in monthly_fields:
            mp = getattr(dd, f, {})
            setattr(dd, f, {m: v for m, v in mp.items() if int(m) <= int(max_month)})
        d2[k] = dd
    return d2

def mae(a, b): return float(np.mean(np.abs(a - b)))
def rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))
def mape(a, b):
    denom = np.maximum(np.abs(a), 1e-6)
    return float(np.mean(np.abs(a - b) / denom))

def coverage(y, lo, hi):
    y = np.asarray(y); lo = np.asarray(lo); hi = np.asarray(hi)
    return float(np.mean((y >= lo) & (y <= hi)))

def avg_width(lo, hi):
    lo = np.asarray(lo); hi = np.asarray(hi)
    return float(np.mean(np.maximum(hi - lo, 0.0)))

def run_backtest(max_h=9, alpha=0.2, min_base_month=3):
    # 初始化全局 dealers/scaler
    init_app()

    # 取全局最大月
    global_max = 0
    for _, d in dealers.items():
        if len(d.sales) > 0:
            global_max = max(global_max, max(d.sales.keys()))

    # 这里给两种评估：
    # 1) 快速评估：用全量训练的 forecaster，直接在历史样本上评估（偏乐观）
    # 2) 更严谨：rolling origin（每个 cutoff 重新训练），你数据少也跑得动

    print("=== Quick eval (in-sample-ish, optimistic) ===")
    forecaster = QuantileForecaster(default_quantiles=[0.1,0.5,0.9], calib_alpha=alpha)
    forecaster.fit(dealers=dealers, scaler=scaler)

    quick_metrics = {h: {"y": [], "p": [], "lo": [], "hi": []} for h in range(1, max_h+1)}

    for code, d in dealers.items():
        for m in range(min_base_month, global_max+1):
            if not _has_required_month_fields(d, m, include_target=False):
                continue
            for h in range(1, max_h+1):
                tm = m + h
                if tm not in d.sales:
                    continue
                pred = forecaster.predict(d, scaler, base_month=m, horizons=[h], quantiles=[0.1,0.5,0.9])
                if len(pred["point"]) == 0:
                    continue
                y = float(d.sales[tm])
                p = float(pred["point"][0])
                lo = float(pred["calibrated_interval_80"]["lower"][0])
                hi = float(pred["calibrated_interval_80"]["upper"][0])
                quick_metrics[h]["y"].append(y)
                quick_metrics[h]["p"].append(p)
                quick_metrics[h]["lo"].append(lo)
                quick_metrics[h]["hi"].append(hi)

    for h in range(1, max_h+1):
        y = np.array(quick_metrics[h]["y"], dtype=float)
        if y.size == 0:
            continue
        p = np.array(quick_metrics[h]["p"], dtype=float)
        lo = np.array(quick_metrics[h]["lo"], dtype=float)
        hi = np.array(quick_metrics[h]["hi"], dtype=float)
        print(f"h={h:02d} n={y.size:4d} MAE={mae(y,p):.2f} RMSE={rmse(y,p):.2f} MAPE={mape(y,p):.3f} "
              f"cov80={coverage(y,lo,hi):.3f} width={avg_width(lo,hi):.2f}")

    # ------- rolling origin（更可信）-------
    print("\n=== Rolling-origin eval (more realistic) ===")
    # cutoff 至少要让 h=1 有测试样本
    for cutoff in range(min_base_month+2, global_max-1):
        train_dealers = truncate_sales(dealers, max_month=cutoff)
        f = QuantileForecaster(default_quantiles=[0.1,0.5,0.9], calib_alpha=alpha)
        f.fit(dealers=train_dealers, scaler=scaler)

        # 用 base_month=cutoff 这个点，预测 cutoff+h，并与真实对比（真实在原 dealers 里）
        for h in range(1, min(max_h, global_max-cutoff)+1):
            y_list, p_list, lo_list, hi_list = [], [], [], []
            for code, d in dealers.items():
                if not _has_required_month_fields(d, cutoff, include_target=False):
                    continue
                tm = cutoff + h
                if tm not in d.sales:
                    continue
                pred = f.predict(d, scaler, base_month=cutoff, horizons=[h], quantiles=[0.1,0.5,0.9])
                if len(pred["point"]) == 0:
                    continue
                y_list.append(float(d.sales[tm]))
                p_list.append(float(pred["point"][0]))
                lo_list.append(float(pred["calibrated_interval_80"]["lower"][0]))
                hi_list.append(float(pred["calibrated_interval_80"]["upper"][0]))

            if len(y_list) >= 20:  # 太少就不报告
                y = np.array(y_list); p = np.array(p_list); lo=np.array(lo_list); hi=np.array(hi_list)
                print(f"cutoff={cutoff:02d} h={h:02d} n={len(y_list):4d} MAE={mae(y,p):.2f} cov80={coverage(y,lo,hi):.3f}")

if __name__ == "__main__":
    run_backtest(max_h=9, alpha=0.2, min_base_month=3)

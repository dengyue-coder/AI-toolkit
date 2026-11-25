#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sop-ecom-toolkit 环境自检 —— 一次跑完 8 个脚本，确认这份工具箱在本机能用。

用法（在 toolkit 根目录）:
    python tools/smoke_test.py
    python tools/smoke_test.py -v        # 打印每个脚本的前 6 行输出

说明:
  · 只读仓库自带样本数据，不修改任何源文件
  · 判定标准：进程能跑完且没有 Traceback（部分脚本用非 0 退出码表示"有告警"，属正常）
  · 依赖：python 3.9+；04 模块需要 Pillow；01 模块 XLSX 需要 openpyxl（CSV 不需要）
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

CASES = [
    (
        "01 数据标准化",
        ["Agents/01_Market_Research_Agent/scripts/shaduola_parser.py",
         "Agents/01_Market_Research_Agent/samples/sample_patinete_eletrico.csv", "--profile"],
    ),
    (
        "01 市场指标",
        ["Agents/01_Market_Research_Agent/scripts/market_metrics.py",
         "Agents/01_Market_Research_Agent/samples/sample_patinete_eletrico.normalized.json",
         "--bins", "8"],
    ),
    (
        "02 SKU 定价",
        ["Agents/02_Product_Strategy_Agent/scripts/sku_pricing.py", "calc",
         "--platform", "shopee_br", "--cost", "935", "--price", "2199"],
    ),
    (
        "03 标题校验",
        ["Agents/03_Listing_Creative_Agent/scripts/title_lint.py",
         "Patinete Elétrico 500W Dobrável Pneu 8.5 Bateria 48V Adulto",
         "--platform", "shopee", "--keywords", "patinete,eletrico,500w"],
    ),
    (
        "03 参数一致性",
        ["Agents/03_Listing_Creative_Agent/scripts/spec_consistency.py",
         "--spec", "Agents/03_Listing_Creative_Agent/examples/spec_table.csv",
         "--title", "Carregador Portátil 20000mAh 45W com 2 Saídas USB",
         "--allow", "2026,110,2"],
    ),
    (
        "04 主图合规",
        ["Agents/04_Product_Image_Agent/scripts/check_main_image.py",
         "Agents/04_Product_Image_Agent/tests/shopee_fix.png", "--platform", "shopee"],
    ),
    (
        "05 视频时长",
        ["Agents/05_Product_Video_Agent/scripts/video_timing.py",
         "--script", "Agents/05_Product_Video_Agent/examples/narration_airfryer.txt",
         "--target", "30"],
    ),
    (
        "06 广告诊断",
        ["Agents/06_Advertising_Optimization_Agent/scripts/ad_metrics.py", "diagnose",
         "--file", "Agents/06_Advertising_Optimization_Agent/examples/sample-ad-report.csv",
         "--price", "113.40", "--product-cost", "55", "--commission", "14",
         "--return", "2", "--tax", "0", "--target-acos", "25"],
    ),
    (
        "07 评论统计",
        ["Agents/07_Review_Analysis_Agent/scripts/review_stats.py",
         "--file", "Agents/07_Review_Analysis_Agent/examples/sample-reviews.csv",
         "--points", "Agents/07_Review_Analysis_Agent/examples/sample-selling-points.csv"],
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    ok = 0
    failed = []
    for name, argv in CASES:
        script = ROOT / argv[0]
        cmd = [PY, str(script), *argv[1:]]
        print(f"\n{'=' * 60}\n▶ {name}  ({Path(argv[0]).name})")
        try:
            proc = subprocess.run(
                cmd, cwd=str(ROOT), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  ❌ 启动失败: {exc}")
            failed.append((name, str(exc)))
            continue

        out = (proc.stdout or "") + (proc.stderr or "")
        crashed = "Traceback (most recent call last)" in out or proc.returncode not in (0, 1)
        if crashed:
            print(f"  ❌ 失败（exit={proc.returncode}）")
            print("\n".join(out.strip().splitlines()[-8:]))
            failed.append((name, f"exit={proc.returncode}"))
            continue

        ok += 1
        note = "（有告警/退出码 1，属脚本设计行为）" if proc.returncode == 1 else ""
        print(f"  ✅ 通过 {note}")
        if args.verbose:
            for line in out.strip().splitlines()[:6]:
                print(f"     {line}")

    print(f"\n{'=' * 60}\n结果：{ok}/{len(CASES)} 通过")
    if failed:
        print("未通过：")
        for name, why in failed:
            print(f"  · {name} —— {why}")
        return 1
    print("环境完好，7 个模块的 9 个脚本全部可跑。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

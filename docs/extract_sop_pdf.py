#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/电商运营SOP总框架.pdf 提取为可检索的 Markdown 纯文本。

用法:
    python extract_sop_pdf.py            # 输出 docs/电商运营SOP总框架.md
    python extract_sop_pdf.py --out xxx.md

依赖: pypdf (pip install pypdf)
说明: PDF 为 38 页图片+文字混排的手册，本脚本只取文字层；
      若某页文字层为空（纯图片页），会在对应页码处标记 [本页无文字层]。
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import unicodedata
from pathlib import Path

logging.getLogger("pypdf").setLevel(logging.CRITICAL)

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("需要 pypdf：pip install pypdf")


def clean(text: str) -> str:
    # PDF 字体子集常把中文映射到 CJK 兼容表意文字区（U+2F00/F900），NFKC 归一到常用汉字
    text = unicodedata.normalize("NFKC", text)
    # 去掉页眉页脚重复行（"电商运营 SOP 总框架" / "电商平台"）
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if s in {"电商运营 SOP 总框架", "电商平台", "电商运营SOP总框架"}:
            continue
        lines.append(s)
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def main() -> None:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=str(here / "电商运营SOP总框架.pdf"))
    ap.add_argument("--out", default=str(here / "电商运营SOP总框架.md"))
    args = ap.parse_args()

    reader = PdfReader(args.pdf)
    chunks = [
        "# 电商运营 SOP 总框架（PDF 文字层提取）\n",
        f"> 源文件：`{Path(args.pdf).name}` ｜ 共 {len(reader.pages)} 页 ｜ "
        "由 `extract_sop_pdf.py` 自动提取，仅供检索阅读；正式排版请以 PDF 原文为准。\n",
    ]
    empty = []
    for i, page in enumerate(reader.pages, 1):
        try:
            text = clean(page.extract_text() or "")
        except Exception as exc:  # noqa: BLE001
            text = f"[提取失败: {exc}]"
        if len(text) < 20:
            empty.append(i)
            text = "[本页无文字层，请查看 PDF 原页]"
        chunks.append(f"\n\n---\n\n## 第 {i} 页\n\n{text}")

    Path(args.out).write_text("".join(chunks) + "\n", encoding="utf-8")
    print(f"✅ 已写入 {args.out}")
    print(f"   页数 {len(reader.pages)}｜无文字层页：{empty or '无'}")


if __name__ == "__main__":
    main()

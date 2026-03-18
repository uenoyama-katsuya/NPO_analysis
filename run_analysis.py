#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""個別分析CLI: python run_analysis.py <analysis_name>"""

import argparse
import warnings
warnings.filterwarnings('ignore')

from config import setup_matplotlib, OUTPUT_DIR
from src.loader import load_data
from analyses import ANALYSES, get_analysis


def main():
    parser = argparse.ArgumentParser(description='NPO法人データ 個別分析実行')
    parser.add_argument('name', nargs='?', help='分析名（例: distribution, correlation）')
    parser.add_argument('--list', action='store_true', help='利用可能な分析の一覧を表示')
    args = parser.parse_args()

    if args.list or args.name is None:
        print("利用可能な分析:")
        print("-" * 50)
        for a in ANALYSES:
            print(f"  {a.name:<25} {a.description}")
        print("-" * 50)
        print(f"\n使用法: python run_analysis.py <分析名>")
        return

    analysis = get_analysis(args.name)
    if analysis is None:
        print(f"エラー: '{args.name}' は存在しない分析名です。")
        print("利用可能な分析名:")
        for a in ANALYSES:
            print(f"  {a.name}")
        return

    setup_matplotlib()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"データ読み込み中...")
    df = load_data()

    # 依存関係の解決: summary_dashboard は field_hypothesis の結果が必要
    shared_data = {}
    if analysis.name == 'summary_dashboard':
        from analyses import get_analysis as _get
        fh = _get('field_hypothesis')
        print(f"依存分析 '{fh.name}' を先に実行中...")
        result = fh.run(df)
        if result:
            shared_data.update(result)

    print(f"\n分析 '{analysis.name}' を実行中...")
    analysis.run(df, **shared_data)
    print("完了！")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全分析実行スクリプト"""

import warnings
warnings.filterwarnings('ignore')

from config import setup_matplotlib, OUTPUT_DIR
from src.loader import load_data
from analyses import ANALYSES


def main():
    setup_matplotlib()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NPO法人データ分析 開始")
    print("=" * 60)

    df = load_data()

    print(f"\n=== データ概要 ===")
    print(f"総法人数: {len(df)}")
    print(f"カラム: {df.columns.tolist()}")
    print(f"\n数値カラムの基本統計:")
    print(df[['総収入_百万円', '寄付会費比_pct', '事業収益_百万円']].describe())

    # 分析間の受け渡しデータ
    shared_data = {}

    for analysis in ANALYSES:
        print(f"\n{'=' * 60}")
        print(f"{analysis.description}")
        print("=" * 60)
        result = analysis.run(df, **shared_data)
        if result:
            shared_data.update(result)

    # CSVとして分野別統計も出力
    if 'field_agg' in shared_data:
        csv_path = OUTPUT_DIR / 'field_statistics.csv'
        shared_data['field_agg'].to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✓ field_statistics.csv を保存")

    print(f"\n{'=' * 60}")
    print("全分析完了！出力ファイル:")
    for analysis in ANALYSES:
        for f in analysis.output_files:
            print(f"  {OUTPUT_DIR / f}")
    if 'field_agg' in shared_data:
        print(f"  {OUTPUT_DIR / 'field_statistics.csv'}")
    print("=" * 60)


if __name__ == '__main__':
    main()

"""データ読込: CSV読込・前処理"""

import csv

import pandas as pd
import numpy as np

from config import DATA_DIR
from src.mappings import REGION_MAP, FIELD_SHORT


def load_data(csv_path=None):
    """CSVを読み込んで前処理済みDataFrameを返す

    Args:
        csv_path: CSVファイルのパス。Noneの場合はDATA_DIR/npo_data.csvを使用

    Returns:
        pd.DataFrame: 前処理済みのDataFrame
    """
    if csv_path is None:
        csv_path = DATA_DIR / 'npo_data.csv'

    col_names = [
        '順位', '法人名', '総収入_百万円', 'ステージ',
        '寄付会費_百万円', '寄付会費比_pct',
        '受取寄附金_百万円', '受取会費_百万円', '受取助成金等_百万円',
        '事業収益_百万円', '経常費用_百万円', '有給職員数',
        '事業年度', '認定状況', '所在地', '活動分野'
    ]

    # ヘッダーが複数行にまたがるCSVなので、行をスキャンしてデータ開始行を見つける
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # データ行を特定（数値で始まる行がデータ行）
    data_start = None
    for i, row in enumerate(rows):
        if len(row) > 0:
            try:
                int(row[0])
                if data_start is None:
                    data_start = i
            except (ValueError, IndexError):
                pass

    # データ行のみ抽出
    data_rows = []
    for row in rows[data_start:]:
        if len(row) >= 10:
            try:
                int(row[0])
                data_rows.append(row[:16])
            except (ValueError, IndexError):
                continue

    df = pd.DataFrame(data_rows, columns=col_names)

    # 数値カラムの変換
    numeric_cols = ['順位', '総収入_百万円', '寄付会費_百万円', '寄付会費比_pct',
                    '受取寄附金_百万円', '受取会費_百万円', '受取助成金等_百万円',
                    '事業収益_百万円', '経常費用_百万円', '有給職員数']

    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(',', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 認定状況のクリーニング
    df['認定'] = df['認定状況'].str.strip().apply(lambda x: '認定' if x == '○' else '未認定')

    # 所在地の広域分類
    df['所在地_clean'] = df['所在地'].str.strip()
    df['地域'] = df['所在地_clean'].map(REGION_MAP).fillna('その他')

    # 活動分野を展開（1団体が複数分野を持つ）
    df['活動分野_list'] = df['活動分野'].str.split('、')

    # 異常値処理：寄付比率は0-100%の範囲に制限
    df.loc[df['寄付会費比_pct'] > 100, '寄付会費比_pct'] = np.nan
    df.loc[df['寄付会費比_pct'] < 0, '寄付会費比_pct'] = np.nan

    return df

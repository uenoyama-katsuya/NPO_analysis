#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NPO法人データ分析スクリプト
目的:
  ① 分野/エリア/規模別の法人数分布
  ② 収益の寄付比率とサイズの相関分析
  ③ 分野別の分散度と寄付比率からの課題仮説・打ち手仮説
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import rcParams
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
rcParams['font.family'] = 'Hiragino Sans'
rcParams['axes.unicode_minus'] = False
rcParams['font.size'] = 10

OUTPUT_DIR = '/Users/k_uenoyama/NPO_analysis/output'
import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========================================
# データ読み込みと前処理
# ========================================
def load_data():
    """CSVを読み込んで前処理"""
    df = pd.read_csv(
        '/Users/k_uenoyama/NPO_analysis/npo_data.csv',
        skiprows=2,  # 最初の2行はタイトル行
        header=[0, 1],  # ヘッダーが2行にまたがる
        encoding='utf-8'
    )

    # マルチインデックスをフラットに
    # 実際のカラム名を確認して手動で設定
    df_raw = pd.read_csv(
        '/Users/k_uenoyama/NPO_analysis/npo_data.csv',
        skiprows=0,
        header=None,
        encoding='utf-8'
    )

    # ヘッダー行を確認
    print("=== Raw header rows ===")
    for i in range(5):
        print(f"Row {i}: {df_raw.iloc[i].tolist()}")

    # データは3行目(0-indexed)からヘッダー、実データは行12あたりから
    # CSVの構造上、ヘッダーが複数行にまたがっているので手動でカラム名を設定

    # 実データを直接読み込む
    # ヘッダー行をスキップしてデータ部分のみ読む
    col_names = [
        '順位', '法人名', '総収入_百万円', 'ステージ',
        '寄付会費_百万円', '寄付会費比_pct',
        '受取寄附金_百万円', '受取会費_百万円', '受取助成金等_百万円',
        '事業収益_百万円', '経常費用_百万円', '有給職員数',
        '事業年度', '認定状況', '所在地', '活動分野'
    ]

    # ヘッダーが複数行にまたがるCSVなので、行をスキャンしてデータ開始行を見つける
    data_rows = []
    with open('/Users/k_uenoyama/NPO_analysis/npo_data.csv', 'r', encoding='utf-8') as f:
        import csv
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

    print(f"\nData starts at row: {data_start}")
    print(f"Total rows: {len(rows)}")
    print(f"Sample data row: {rows[data_start][:5]}")

    # データ行のみ抽出
    data_rows = []
    for row in rows[data_start:]:
        if len(row) >= 10:
            try:
                int(row[0])
                data_rows.append(row[:16])  # 最大16カラム
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
    region_map = {
        '北海道': '北海道・東北', '青森県': '北海道・東北', '岩手県': '北海道・東北',
        '宮城県': '北海道・東北', '秋田県': '北海道・東北', '山形県': '北海道・東北',
        '福島県': '北海道・東北', '仙台市': '北海道・東北',
        '茨城県': '関東', '栃木県': '関東', '群馬県': '関東', '埼玉県': '関東',
        'さいたま市': '関東', '千葉県': '関東', '千葉市': '関東',
        '東京都': '東京', '横浜市': '関東', '川崎市': '関東', '相模原市': '関東',
        '神奈川県': '関東',
        '新潟県': '中部', '富山県': '中部', '石川県': '中部', '福井県': '中部',
        '山梨県': '中部', '長野県': '中部', '岐阜県': '中部', '静岡県': '中部',
        '静岡市': '中部', '浜松市': '中部', '愛知県': '中部', '名古屋市': '中部',
        '新潟市': '中部',
        '三重県': '近畿', '滋賀県': '近畿', '京都府': '近畿', '京都市': '近畿',
        '大阪府': '近畿', '大阪市': '近畿', '堺市': '近畿',
        '兵庫県': '近畿', '神戸市': '近畿', '奈良県': '近畿', '和歌山県': '近畿',
        '鳥取県': '中国・四国', '島根県': '中国・四国', '岡山県': '中国・四国',
        '岡山市': '中国・四国', '広島県': '中国・四国', '広島市': '中国・四国',
        '山口県': '中国・四国', '徳島県': '中国・四国', '香川県': '中国・四国',
        '愛媛県': '中国・四国', '高知県': '中国・四国',
        '福岡県': '九州・沖縄', '福岡市': '九州・沖縄', '北九州市': '九州・沖縄',
        '佐賀県': '九州・沖縄', '長崎県': '九州・沖縄', '熊本県': '九州・沖縄',
        '熊本市': '九州・沖縄', '大分県': '九州・沖縄', '宮崎県': '九州・沖縄',
        '鹿児島県': '九州・沖縄', '沖縄県': '九州・沖縄',
    }
    df['所在地_clean'] = df['所在地'].str.strip()
    df['地域'] = df['所在地_clean'].map(region_map).fillna('その他')

    # 活動分野を展開（1団体が複数分野を持つ）
    df['活動分野_list'] = df['活動分野'].str.split('、')

    # 分野の短縮名マッピング
    field_short = {
        '保健・医療・福祉': '保健医療福祉',
        '社会教育': '社会教育',
        'まちづくり': 'まちづくり',
        '観光': '観光',
        '農山漁村・中山間地域': '農山漁村',
        '学術・文化・芸術・スポーツ': '学術文化スポーツ',
        '環境の保全': '環境保全',
        '災害救援': '災害救援',
        '地域安全': '地域安全',
        '人権の擁護・平和': '人権・平和',
        '国際協力・交流': '国際協力',
        '男女共同参画': '男女共同参画',
        '子どもの健全育成': '子ども育成',
        '情報化社会の発展': '情報化社会',
        '科学技術の振興': '科学技術',
        '経済活動の活性化': '経済活性化',
        '職業能力・雇用機会': '職業・雇用',
        'NPO支援': 'NPO支援',
        '消費者の保護': '消費者保護',
        '条例指定': '条例指定',
    }

    # 異常値処理：寄付比率は0-100%の範囲に制限（総収入0の法人で計算式エラーあり）
    df.loc[df['寄付会費比_pct'] > 100, '寄付会費比_pct'] = np.nan
    df.loc[df['寄付会費比_pct'] < 0, '寄付会費比_pct'] = np.nan

    print(f"\n=== データ概要 ===")
    print(f"総法人数: {len(df)}")
    print(f"カラム: {df.columns.tolist()}")
    print(f"\n数値カラムの基本統計:")
    print(df[['総収入_百万円', '寄付会費比_pct', '事業収益_百万円']].describe())

    return df, field_short


def analysis_1_distribution(df, field_short):
    """① 分野/エリア/規模別の法人数分布"""

    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('① NPO法人の分布分析', fontsize=18, fontweight='bold', y=0.98)

    # --- 1a: ステージ（規模）別の法人数 ---
    ax = axes[0, 0]
    stage_order = ['30億～', '10億～', '5億～', '3億～', '1億～', '5千万～', '1千万～', '1千万未満']
    stage_counts = df['ステージ'].value_counts()
    # ステージ順に並べ替え
    stage_counts_ordered = stage_counts.reindex([s for s in stage_order if s in stage_counts.index])
    colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(stage_counts_ordered)))
    bars = ax.barh(range(len(stage_counts_ordered)), stage_counts_ordered.values, color=colors)
    ax.set_yticks(range(len(stage_counts_ordered)))
    ax.set_yticklabels(stage_counts_ordered.index, fontsize=11)
    ax.set_xlabel('法人数', fontsize=12)
    ax.set_title('規模（ステージ）別の法人数', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    for bar, val in zip(bars, stage_counts_ordered.values):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                f'{val} ({val/len(df)*100:.1f}%)', va='center', fontsize=10)

    # --- 1b: 地域別の法人数 ---
    ax = axes[0, 1]
    region_order = ['東京', '関東', '近畿', '中部', '九州・沖縄', '北海道・東北', '中国・四国', 'その他']
    region_counts = df['地域'].value_counts()
    region_counts_ordered = region_counts.reindex([r for r in region_order if r in region_counts.index])
    colors2 = plt.cm.Blues(np.linspace(0.3, 0.9, len(region_counts_ordered)))
    bars = ax.barh(range(len(region_counts_ordered)), region_counts_ordered.values, color=colors2)
    ax.set_yticks(range(len(region_counts_ordered)))
    ax.set_yticklabels(region_counts_ordered.index, fontsize=11)
    ax.set_xlabel('法人数', fontsize=12)
    ax.set_title('地域別の法人数', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    for bar, val in zip(bars, region_counts_ordered.values):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                f'{val} ({val/len(df)*100:.1f}%)', va='center', fontsize=10)

    # --- 1c: 活動分野別の法人数（複数分野持ちを展開） ---
    ax = axes[1, 0]
    all_fields = []
    for fields in df['活動分野_list'].dropna():
        for f in fields:
            f_clean = f.strip()
            all_fields.append(field_short.get(f_clean, f_clean))
    field_counts = Counter(all_fields)
    field_df = pd.DataFrame(field_counts.items(), columns=['分野', '法人数']).sort_values('法人数', ascending=True)
    colors3 = plt.cm.Greens(np.linspace(0.3, 0.9, len(field_df)))
    bars = ax.barh(range(len(field_df)), field_df['法人数'].values, color=colors3)
    ax.set_yticks(range(len(field_df)))
    ax.set_yticklabels(field_df['分野'].values, fontsize=9)
    ax.set_xlabel('法人数（延べ）', fontsize=12)
    ax.set_title('活動分野別の法人数（複数分野重複カウント）', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, field_df['法人数'].values):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                f'{val}', va='center', fontsize=9)

    # --- 1d: 地域×ステージのヒートマップ ---
    ax = axes[1, 1]
    # 主要ステージと地域のクロス集計
    stage_simple = ['30億～', '10億～', '5億～', '3億～', '1億～', '5千万～', '1千万～', '1千万未満']
    cross = pd.crosstab(df['地域'], df['ステージ'])
    cross = cross.reindex(columns=[s for s in stage_simple if s in cross.columns],
                          index=[r for r in region_order if r in cross.index])
    sns.heatmap(cross, annot=True, fmt='d', cmap='YlOrRd', ax=ax, linewidths=0.5)
    ax.set_title('地域 × 規模 の法人数ヒートマップ', fontsize=14, fontweight='bold')
    ax.set_xlabel('規模ステージ', fontsize=12)
    ax.set_ylabel('地域', fontsize=12)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{OUTPUT_DIR}/01_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ 01_distribution.png を保存")


def analysis_2_correlation(df):
    """② 収益の寄付比率とサイズの相関分析"""

    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('② 寄付比率とサイズの相関分析', fontsize=18, fontweight='bold', y=0.98)

    # データのフィルタリング（有効データのみ）
    df_valid = df.dropna(subset=['総収入_百万円', '寄付会費比_pct']).copy()
    df_valid = df_valid[df_valid['総収入_百万円'] > 0]
    df_valid['log_収入'] = np.log10(df_valid['総収入_百万円'])

    # --- 2a: 散布図（寄付比率 vs 総収入、対数スケール） ---
    ax = axes[0, 0]
    scatter = ax.scatter(df_valid['総収入_百万円'], df_valid['寄付会費比_pct'],
                        alpha=0.4, s=20, c=df_valid['寄付会費比_pct'],
                        cmap='RdYlBu_r', edgecolors='none')
    ax.set_xscale('log')
    ax.set_xlabel('総収入（百万円・対数スケール）', fontsize=12)
    ax.set_ylabel('寄付+会費比率（%）', fontsize=12)
    ax.set_title('総収入 vs 寄付+会費比率', fontsize=14, fontweight='bold')
    ax.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='寄付比率50%ライン')
    ax.legend(fontsize=10)
    plt.colorbar(scatter, ax=ax, label='寄付比率(%)')

    # 相関係数
    corr = df_valid['log_収入'].corr(df_valid['寄付会費比_pct'])
    ax.text(0.05, 0.95, f'相関係数(log収入 vs 寄付比率): {corr:.3f}',
            transform=ax.transAxes, fontsize=11, va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # --- 2b: ステージ別の寄付比率の箱ひげ図 ---
    ax = axes[0, 1]
    stage_order = ['30億～', '10億～', '5億～', '3億～', '1億～', '5千万～', '1千万～', '1千万未満']
    stage_present = [s for s in stage_order if s in df_valid['ステージ'].unique()]
    df_box = df_valid[df_valid['ステージ'].isin(stage_present)]

    box_data = [df_box[df_box['ステージ'] == s]['寄付会費比_pct'].dropna().values
                for s in stage_present]
    bp = ax.boxplot(box_data, labels=stage_present, patch_artist=True, showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='red', markersize=6))
    colors = plt.cm.YlOrRd(np.linspace(0.2, 0.8, len(stage_present)))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xlabel('規模ステージ', fontsize=12)
    ax.set_ylabel('寄付+会費比率（%）', fontsize=12)
    ax.set_title('規模別 寄付+会費比率の分布', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=30)

    # 各ステージの中央値を表示
    for i, data in enumerate(box_data):
        if len(data) > 0:
            median_val = np.median(data)
            mean_val = np.mean(data)
            ax.text(i+1, ax.get_ylim()[1]*0.97,
                    f'中央値:{median_val:.1f}%\n平均:{mean_val:.1f}%',
                    ha='center', va='top', fontsize=8,
                    bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # --- 2c: 認定状況別の寄付比率 ---
    ax = axes[1, 0]
    for label, color in [('認定', '#2196F3'), ('未認定', '#FF9800')]:
        subset = df_valid[df_valid['認定'] == label]
        ax.scatter(subset['総収入_百万円'], subset['寄付会費比_pct'],
                  alpha=0.4, s=20, c=color, label=f'{label} (n={len(subset)})', edgecolors='none')
    ax.set_xscale('log')
    ax.set_xlabel('総収入（百万円・対数スケール）', fontsize=12)
    ax.set_ylabel('寄付+会費比率（%）', fontsize=12)
    ax.set_title('認定状況別：総収入 vs 寄付比率', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)

    # 認定/未認定の統計
    for label in ['認定', '未認定']:
        subset = df_valid[df_valid['認定'] == label]
        print(f"  {label}: 平均寄付比率={subset['寄付会費比_pct'].mean():.1f}%, "
              f"中央値={subset['寄付会費比_pct'].median():.1f}%, "
              f"平均総収入={subset['総収入_百万円'].mean():.1f}百万円")

    # --- 2d: 収入規模帯ごとの寄付比率ヒストグラム ---
    ax = axes[1, 1]
    bins_donation = [0, 10, 20, 30, 50, 80, 100]
    # 大規模(5億以上) vs 中規模(1-5億) vs 小規模(1億未満)
    size_groups = {
        '大規模（5億以上）': df_valid[df_valid['総収入_百万円'] >= 500],
        '中規模（1～5億）': df_valid[(df_valid['総収入_百万円'] >= 100) & (df_valid['総収入_百万円'] < 500)],
        '小規模（1億未満）': df_valid[df_valid['総収入_百万円'] < 100],
    }
    colors_hist = ['#E53935', '#FB8C00', '#43A047']
    for (label, subset), color in zip(size_groups.items(), colors_hist):
        ax.hist(subset['寄付会費比_pct'].dropna(), bins=20, alpha=0.5,
                label=f'{label} (n={len(subset)})', color=color, density=True)
    ax.set_xlabel('寄付+会費比率（%）', fontsize=12)
    ax.set_ylabel('密度', fontsize=12)
    ax.set_title('規模別の寄付比率の分布（密度）', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{OUTPUT_DIR}/02_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ 02_correlation.png を保存")


def analysis_3_field_hypothesis(df, field_short):
    """③ 分野別の分散度と寄付比率からの課題仮説・打ち手仮説"""

    # 分野ごとの統計を計算
    field_stats = []

    for idx, row in df.iterrows():
        if not isinstance(row['活動分野_list'], list) or pd.isna(row['総収入_百万円']):
            continue
        for field in row['活動分野_list']:
            f_clean = field.strip()
            f_short = field_short.get(f_clean, f_clean)
            field_stats.append({
                '分野': f_short,
                '総収入_百万円': row['総収入_百万円'],
                '寄付会費比_pct': row['寄付会費比_pct'],
                '事業収益_百万円': row['事業収益_百万円'],
                '認定': row['認定'],
            })

    fs_df = pd.DataFrame(field_stats)

    # 分野別集計
    field_agg = fs_df.groupby('分野').agg(
        法人数=('総収入_百万円', 'count'),
        平均収入=('総収入_百万円', 'mean'),
        中央値収入=('総収入_百万円', 'median'),
        収入標準偏差=('総収入_百万円', 'std'),
        収入変動係数=('総収入_百万円', lambda x: x.std() / x.mean() if x.mean() > 0 else 0),
        平均寄付比率=('寄付会費比_pct', 'mean'),
        中央値寄付比率=('寄付会費比_pct', 'median'),
        寄付比率標準偏差=('寄付会費比_pct', 'std'),
        認定比率=('認定', lambda x: (x == '認定').sum() / len(x) * 100),
        総収入合計=('総収入_百万円', 'sum'),
    ).reset_index()

    # ジニ係数の計算
    def gini(values):
        values = np.sort(values)
        n = len(values)
        if n == 0 or values.sum() == 0:
            return 0
        index = np.arange(1, n + 1)
        return (2 * np.sum(index * values) - (n + 1) * values.sum()) / (n * values.sum())

    field_agg['ジニ係数'] = fs_df.groupby('分野')['総収入_百万円'].apply(
        lambda x: gini(x.dropna().values)
    ).values

    print("\n=== 分野別統計 ===")
    print(field_agg.sort_values('法人数', ascending=False).to_string(index=False))

    # --- 可視化 ---
    fig, axes = plt.subplots(2, 2, figsize=(22, 18))
    fig.suptitle('③ 分野別の分散度と寄付比率：課題仮説・打ち手仮説', fontsize=18, fontweight='bold', y=0.98)

    # --- 3a: バブルチャート（寄付比率 vs ジニ係数、バブルサイズ=法人数） ---
    ax = axes[0, 0]
    bubble = ax.scatter(
        field_agg['平均寄付比率'],
        field_agg['ジニ係数'],
        s=field_agg['法人数'] * 0.8,
        c=field_agg['認定比率'],
        cmap='RdYlGn',
        alpha=0.7,
        edgecolors='gray',
        linewidth=0.5
    )
    for _, row in field_agg.iterrows():
        ax.annotate(row['分野'], (row['平均寄付比率'], row['ジニ係数']),
                   fontsize=8, ha='center', va='bottom',
                   textcoords='offset points', xytext=(0, 8))
    ax.set_xlabel('平均寄付+会費比率（%）', fontsize=12)
    ax.set_ylabel('収入のジニ係数（格差度）', fontsize=12)
    ax.set_title('分野別：寄付比率 vs 収入格差（バブルサイズ=法人数）', fontsize=14, fontweight='bold')
    plt.colorbar(bubble, ax=ax, label='認定NPO比率(%)')

    # 4象限の区切り線
    median_donation = field_agg['平均寄付比率'].median()
    median_gini = field_agg['ジニ係数'].median()
    ax.axvline(x=median_donation, color='gray', linestyle='--', alpha=0.5)
    ax.axhline(y=median_gini, color='gray', linestyle='--', alpha=0.5)

    # 象限ラベル
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ax.text(xlim[1]*0.85, ylim[1]*0.95, '寄付高×格差大\n「一極集中型」',
            fontsize=9, ha='center', va='top', color='red', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    ax.text(xlim[0]+2, ylim[1]*0.95, '寄付低×格差大\n「寡占型」',
            fontsize=9, ha='center', va='top', color='orange', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    ax.text(xlim[1]*0.85, ylim[0]+0.02, '寄付高×格差小\n「健全成長型」',
            fontsize=9, ha='center', va='bottom', color='green', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    ax.text(xlim[0]+2, ylim[0]+0.02, '寄付低×格差小\n「事業依存型」',
            fontsize=9, ha='center', va='bottom', color='blue', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

    # --- 3b: 分野別の寄付比率と事業収益比率の比較 ---
    ax = axes[0, 1]
    fa_sorted = field_agg.sort_values('平均寄付比率', ascending=True)
    y_pos = range(len(fa_sorted))
    ax.barh(y_pos, fa_sorted['平均寄付比率'].values, color='#2196F3', alpha=0.7, label='平均寄付+会費比率')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(fa_sorted['分野'].values, fontsize=9)
    ax.set_xlabel('平均寄付+会費比率（%）', fontsize=12)
    ax.set_title('分野別の平均寄付+会費比率', fontsize=14, fontweight='bold')
    ax.axvline(x=field_agg['平均寄付比率'].mean(), color='red', linestyle='--', alpha=0.7, label='全体平均')
    ax.legend(fontsize=10)

    # --- 3c: 分野別のジニ係数（格差度）---
    ax = axes[1, 0]
    fa_gini_sorted = field_agg.sort_values('ジニ係数', ascending=True)
    colors_gini = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(fa_gini_sorted)))
    bars = ax.barh(range(len(fa_gini_sorted)), fa_gini_sorted['ジニ係数'].values, color=colors_gini)
    ax.set_yticks(range(len(fa_gini_sorted)))
    ax.set_yticklabels(fa_gini_sorted['分野'].values, fontsize=9)
    ax.set_xlabel('ジニ係数（0=完全平等、1=完全不平等）', fontsize=12)
    ax.set_title('分野別の収入格差（ジニ係数）', fontsize=14, fontweight='bold')
    ax.axvline(x=field_agg['ジニ係数'].mean(), color='red', linestyle='--', alpha=0.7)

    # --- 3d: 課題仮説・打ち手マトリクス（テキスト） ---
    ax = axes[1, 1]
    ax.axis('off')

    # 象限分類
    quadrants = {
        '寄付高×格差大\n（一極集中型）': [],
        '寄付低×格差大\n（寡占型）': [],
        '寄付高×格差小\n（健全成長型）': [],
        '寄付低×格差小\n（事業依存型）': [],
    }

    for _, row in field_agg.iterrows():
        if row['平均寄付比率'] >= median_donation and row['ジニ係数'] >= median_gini:
            quadrants['寄付高×格差大\n（一極集中型）'].append(row['分野'])
        elif row['平均寄付比率'] < median_donation and row['ジニ係数'] >= median_gini:
            quadrants['寄付低×格差大\n（寡占型）'].append(row['分野'])
        elif row['平均寄付比率'] >= median_donation and row['ジニ係数'] < median_gini:
            quadrants['寄付高×格差小\n（健全成長型）'].append(row['分野'])
        else:
            quadrants['寄付低×格差小\n（事業依存型）'].append(row['分野'])

    hypotheses = {
        '寄付高×格差大\n（一極集中型）': {
            '課題': '大手に寄付が集中し中小が伸び悩む',
            '打ち手': '中小NPOへのファンドレイジング支援\n共同キャンペーン/プラットフォーム構築',
        },
        '寄付低×格差大\n（寡占型）': {
            '課題': '事業収益依存かつ大手寡占で新規参入困難',
            '打ち手': '業界全体の寄付文化醸成\n中小の認知度向上・連携促進',
        },
        '寄付高×格差小\n（健全成長型）': {
            '課題': '寄付は集まるが規模拡大の壁がある',
            '打ち手': '成功モデルの横展開\n大口寄付者の開拓・遺贈寄付の推進',
        },
        '寄付低×格差小\n（事業依存型）': {
            '課題': '寄付が集まりにくく事業収益に依存',
            '打ち手': '社会的インパクト評価の導入\n寄付者へのストーリーテリング強化',
        },
    }

    text_content = "【分野別 課題仮説と打ち手仮説マトリクス】\n\n"
    for quad, fields in quadrants.items():
        hyp = hypotheses[quad]
        text_content += f"■ {quad}\n"
        text_content += f"  分野: {', '.join(fields) if fields else 'なし'}\n"
        text_content += f"  課題仮説: {hyp['課題']}\n"
        text_content += f"  打ち手仮説: {hyp['打ち手']}\n\n"

    ax.text(0.05, 0.95, text_content, transform=ax.transAxes,
            fontsize=10, va='top', ha='left', fontfamily='Hiragino Sans',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
            linespacing=1.6)
    ax.set_title('課題仮説と打ち手仮説', fontsize=14, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{OUTPUT_DIR}/03_field_hypothesis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ 03_field_hypothesis.png を保存")

    return field_agg


def create_summary_dashboard(df, field_agg, field_short):
    """総合サマリーダッシュボード"""

    fig, axes = plt.subplots(2, 3, figsize=(24, 14))
    fig.suptitle('NPO法人データ 分析サマリーダッシュボード', fontsize=20, fontweight='bold', y=0.99)

    df_valid = df.dropna(subset=['総収入_百万円', '寄付会費比_pct']).copy()

    # --- KPIカード ---
    ax = axes[0, 0]
    ax.axis('off')
    kpis = [
        ('総法人数', f'{len(df):,}'),
        ('総収入合計', f'{df["総収入_百万円"].sum():,.0f} 百万円'),
        ('平均寄付比率', f'{df_valid["寄付会費比_pct"].mean():.1f}%'),
        ('中央値寄付比率', f'{df_valid["寄付会費比_pct"].median():.1f}%'),
        ('認定NPO比率', f'{(df["認定"]=="認定").sum()/len(df)*100:.1f}%'),
        ('活動分野数', f'{len(field_agg)}'),
    ]
    for i, (label, value) in enumerate(kpis):
        y = 0.9 - i * 0.15
        ax.text(0.1, y, label, fontsize=12, va='center', fontweight='bold')
        ax.text(0.9, y, value, fontsize=14, va='center', ha='right', color='#1565C0')
    ax.set_title('主要KPI', fontsize=14, fontweight='bold')

    # --- 収入分布（対数ヒストグラム） ---
    ax = axes[0, 1]
    log_income = np.log10(df_valid['総収入_百万円'].clip(lower=0.1))
    ax.hist(log_income, bins=30, color='#42A5F5', alpha=0.8, edgecolor='white')
    ax.set_xlabel('log10(総収入 百万円)', fontsize=11)
    ax.set_ylabel('法人数', fontsize=11)
    ax.set_title('総収入の分布（対数スケール）', fontsize=13, fontweight='bold')
    # x軸ラベルを実際の金額に
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels(['1百万', '10百万', '100百万\n(1億)', '1,000百万\n(10億)', '10,000百万\n(100億)'], fontsize=8)

    # --- 寄付比率の分布 ---
    ax = axes[0, 2]
    ax.hist(df_valid['寄付会費比_pct'], bins=20, color='#66BB6A', alpha=0.8, edgecolor='white')
    ax.set_xlabel('寄付+会費比率（%）', fontsize=11)
    ax.set_ylabel('法人数', fontsize=11)
    ax.set_title('寄付+会費比率の分布', fontsize=13, fontweight='bold')
    ax.axvline(x=df_valid['寄付会費比_pct'].mean(), color='red', linestyle='--', label=f'平均: {df_valid["寄付会費比_pct"].mean():.1f}%')
    ax.axvline(x=df_valid['寄付会費比_pct'].median(), color='orange', linestyle='--', label=f'中央値: {df_valid["寄付会費比_pct"].median():.1f}%')
    ax.legend(fontsize=9)

    # --- Top分野の収入構成 ---
    ax = axes[1, 0]
    top_fields = field_agg.nlargest(10, '法人数')
    y_pos = range(len(top_fields))
    ax.barh(y_pos, top_fields['平均寄付比率'], color='#42A5F5', alpha=0.8, label='寄付+会費')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_fields['分野'], fontsize=9)
    ax.set_xlabel('平均寄付+会費比率（%）', fontsize=11)
    ax.set_title('主要分野の平均寄付比率（Top10）', fontsize=13, fontweight='bold')
    ax.invert_yaxis()

    # --- 地域別の総収入シェア ---
    ax = axes[1, 1]
    region_revenue = df.groupby('地域')['総収入_百万円'].sum().sort_values(ascending=False)
    colors_pie = plt.cm.Set3(np.linspace(0, 1, len(region_revenue)))
    wedges, texts, autotexts = ax.pie(
        region_revenue.values, labels=region_revenue.index,
        autopct='%1.1f%%', colors=colors_pie, startangle=90,
        textprops={'fontsize': 9}
    )
    ax.set_title('地域別の総収入シェア', fontsize=13, fontweight='bold')

    # --- 認定 vs 未認定の比較 ---
    ax = axes[1, 2]
    cert_stats = df_valid.groupby('認定').agg(
        平均収入=('総収入_百万円', 'mean'),
        平均寄付比率=('寄付会費比_pct', 'mean'),
        法人数=('総収入_百万円', 'count')
    ).reset_index()
    x = range(len(cert_stats))
    width = 0.35
    bars1 = ax.bar([i - width/2 for i in x], cert_stats['平均寄付比率'], width,
                   label='平均寄付比率(%)', color='#42A5F5', alpha=0.8)
    ax2 = ax.twinx()
    bars2 = ax2.bar([i + width/2 for i in x], cert_stats['平均収入'], width,
                    label='平均収入(百万円)', color='#FF7043', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cert_stats['認定'], fontsize=11)
    ax.set_ylabel('平均寄付比率(%)', fontsize=11, color='#42A5F5')
    ax2.set_ylabel('平均収入(百万円)', fontsize=11, color='#FF7043')
    ax.set_title('認定状況別の比較', fontsize=13, fontweight='bold')
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{OUTPUT_DIR}/00_summary_dashboard.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ 00_summary_dashboard.png を保存")


# ========================================
# メイン実行
# ========================================
if __name__ == '__main__':
    print("=" * 60)
    print("NPO法人データ分析 開始")
    print("=" * 60)

    df, field_short = load_data()

    print("\n" + "=" * 60)
    print("分析① 分野/エリア/規模別の法人数分布")
    print("=" * 60)
    analysis_1_distribution(df, field_short)

    print("\n" + "=" * 60)
    print("分析② 収益の寄付比率とサイズの相関分析")
    print("=" * 60)
    analysis_2_correlation(df)

    print("\n" + "=" * 60)
    print("分析③ 分野別の分散度と寄付比率からの課題仮説")
    print("=" * 60)
    field_agg = analysis_3_field_hypothesis(df, field_short)

    print("\n" + "=" * 60)
    print("サマリーダッシュボード作成")
    print("=" * 60)
    create_summary_dashboard(df, field_agg, field_short)

    # CSVとして分野別統計も出力
    field_agg.to_csv(f'{OUTPUT_DIR}/field_statistics.csv', index=False, encoding='utf-8-sig')
    print(f"\n✓ field_statistics.csv を保存")

    print("\n" + "=" * 60)
    print("全分析完了！出力ファイル:")
    print(f"  {OUTPUT_DIR}/00_summary_dashboard.png")
    print(f"  {OUTPUT_DIR}/01_distribution.png")
    print(f"  {OUTPUT_DIR}/02_correlation.png")
    print(f"  {OUTPUT_DIR}/03_field_hypothesis.png")
    print(f"  {OUTPUT_DIR}/field_statistics.csv")
    print("=" * 60)

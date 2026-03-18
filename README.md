# NPO法人データ分析

NPO法人 収入上位 2,324 団体の財務データを分析するプロジェクト。規模・地域・活動分野ごとの分布、寄付比率と収入規模の相関、分野別の課題仮説を可視化する。

## セットアップ

```bash
pip install -r requirements.txt
```

Python 3.9 以上を推奨。日本語フォント（Hiragino Sans）が必要。

## 実行方法

```bash
# 全分析を一括実行（output/ に結果が出力される）
python run_all.py

# 個別分析の実行
python run_analysis.py distribution        # 分布分析
python run_analysis.py correlation         # 相関分析
python run_analysis.py field_hypothesis    # 分野別仮説分析
python run_analysis.py summary_dashboard   # サマリーダッシュボード

# 利用可能な分析の一覧
python run_analysis.py --list

# テスト
pytest tests/
```

## 分析内容

| 分析 | 概要 |
|---|---|
| **分布分析** | 規模（ステージ）別の法人数、地域別分布、活動分野別の法人数、地域×規模のクロス集計ヒートマップ |
| **相関分析** | 総収入 vs 寄付+会費比率の散布図（対数スケール）、規模別の箱ひげ図、認定/未認定別の比較 |
| **分野別仮説分析** | 平均寄付比率×収入ジニ係数のバブルチャートによる 4 象限分類（一極集中型・寡占型・健全成長型・事業依存型） |
| **サマリーダッシュボード** | 上記分析の KPI・主要チャートを 1 枚に集約 |

## 出力ファイル

`output/` に以下が生成される。

| ファイル | 内容 |
|---|---|
| `00_summary_dashboard.png` | サマリーダッシュボード |
| `01_distribution.png` | 分布分析チャート |
| `02_correlation.png` | 相関分析チャート |
| `03_field_hypothesis.png` | 分野別仮説バブルチャート |
| `field_statistics.csv` | 分野別統計（法人数、平均収入、ジニ係数等） |
| `index.html` | 静的チャート一覧ページ |

`dashboard.html`（プロジェクトルート）は Chart.js ベースのインタラクティブダッシュボード。地域・分野・規模・認定状況でフィルタリングできる。

## プロジェクト構成

```
├── config.py                    # パス設定・matplotlib初期化
├── run_all.py                   # 全分析実行
├── run_analysis.py              # 個別分析CLI
├── src/
│   ├── loader.py                # CSV読込・前処理
│   ├── mappings.py              # 地域マッピング・分野短縮名等の定数
│   ├── stats.py                 # ジニ係数等の統計関数
│   └── plot_utils.py            # 描画ヘルパー
├── analyses/
│   ├── base.py                  # BaseAnalysis 抽象クラス
│   ├── a00_summary_dashboard.py
│   ├── a01_distribution.py
│   ├── a02_correlation.py
│   └── a03_field_hypothesis.py
├── data/                        # 入力データ（CSV/JSON）
├── output/                      # 生成物（PNG/CSV/HTML）
├── tests/                       # テスト
├── dashboard.html               # インタラクティブダッシュボード
└── requirements.txt
```

## 分析の追加

1. `analyses/a04_xxx.py` を作成し `BaseAnalysis` を継承
2. `analyses/__init__.py` の `ANALYSES` リストに追加

`run_all.py` と `run_analysis.py` の両方で即利用可能になる。

## データ

`data/npo_data.csv` — NPO法人 収入ランキング 2,324 団体。主なカラム:

- 順位 / 法人名 / 総収入（百万円） / ステージ（規模帯）
- 寄付+会費（百万円） / 寄付+会費比（%）
- 受取寄附金 / 受取会費 / 受取助成金等 / 事業収益 / 経常費用
- 有給職員数 / 事業年度 / 認定状況 / 所在地 / 活動分野

## 技術スタック

pandas / numpy / matplotlib / seaborn / Chart.js / pytest

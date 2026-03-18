"""分野別仮説分析: 分野別の分散度と寄付比率からの課題仮説・打ち手仮説"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from analyses.base import BaseAnalysis
from src.mappings import FIELD_SHORT
from src.stats import gini_coefficient
from src.plot_utils import save_figure


class FieldHypothesisAnalysis(BaseAnalysis):
    name = 'field_hypothesis'
    description = '分野別の分散度と寄付比率からの課題仮説・打ち手仮説'
    output_files = ['03_field_hypothesis.png']

    def run(self, df, **kwargs):
        # 分野ごとの統計を計算
        field_stats = []

        for idx, row in df.iterrows():
            if not isinstance(row['活動分野_list'], list) or pd.isna(row['総収入_百万円']):
                continue
            for field in row['活動分野_list']:
                f_clean = field.strip()
                f_short = FIELD_SHORT.get(f_clean, f_clean)
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
        field_agg['ジニ係数'] = fs_df.groupby('分野')['総収入_百万円'].apply(
            lambda x: gini_coefficient(x.dropna().values)
        ).values

        print("\n=== 分野別統計 ===")
        print(field_agg.sort_values('法人数', ascending=False).to_string(index=False))

        # --- 可視化 ---
        fig, axes = plt.subplots(2, 2, figsize=(22, 18))
        fig.suptitle('③ 分野別の分散度と寄付比率：課題仮説・打ち手仮説', fontsize=18, fontweight='bold', y=0.98)

        # --- 3a: バブルチャート ---
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

        median_donation = field_agg['平均寄付比率'].median()
        median_gini = field_agg['ジニ係数'].median()
        ax.axvline(x=median_donation, color='gray', linestyle='--', alpha=0.5)
        ax.axhline(y=median_gini, color='gray', linestyle='--', alpha=0.5)

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

        # --- 3b: 分野別の寄付比率 ---
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

        # --- 3c: 分野別のジニ係数 ---
        ax = axes[1, 0]
        fa_gini_sorted = field_agg.sort_values('ジニ係数', ascending=True)
        colors_gini = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(fa_gini_sorted)))
        bars = ax.barh(range(len(fa_gini_sorted)), fa_gini_sorted['ジニ係数'].values, color=colors_gini)
        ax.set_yticks(range(len(fa_gini_sorted)))
        ax.set_yticklabels(fa_gini_sorted['分野'].values, fontsize=9)
        ax.set_xlabel('ジニ係数（0=完全平等、1=完全不平等）', fontsize=12)
        ax.set_title('分野別の収入格差（ジニ係数）', fontsize=14, fontweight='bold')
        ax.axvline(x=field_agg['ジニ係数'].mean(), color='red', linestyle='--', alpha=0.7)

        # --- 3d: 課題仮説マトリクス ---
        ax = axes[1, 1]
        ax.axis('off')

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
        save_figure('03_field_hypothesis.png')

        return {'field_agg': field_agg}

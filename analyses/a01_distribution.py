"""分布分析: 分野/エリア/規模別の法人数分布"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

from analyses.base import BaseAnalysis
from src.mappings import FIELD_SHORT, STAGE_ORDER, REGION_ORDER
from src.plot_utils import save_figure


class DistributionAnalysis(BaseAnalysis):
    name = 'distribution'
    description = '分野/エリア/規模別の法人数分布'
    output_files = ['01_distribution.png']

    def run(self, df, **kwargs):
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle('① NPO法人の分布分析', fontsize=18, fontweight='bold', y=0.98)

        # --- 1a: ステージ（規模）別の法人数 ---
        ax = axes[0, 0]
        stage_counts = df['ステージ'].value_counts()
        stage_counts_ordered = stage_counts.reindex([s for s in STAGE_ORDER if s in stage_counts.index])
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
        region_counts = df['地域'].value_counts()
        region_counts_ordered = region_counts.reindex([r for r in REGION_ORDER if r in region_counts.index])
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
                all_fields.append(FIELD_SHORT.get(f_clean, f_clean))
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
        cross = pd.crosstab(df['地域'], df['ステージ'])
        cross = cross.reindex(columns=[s for s in STAGE_ORDER if s in cross.columns],
                              index=[r for r in REGION_ORDER if r in cross.index])
        sns.heatmap(cross, annot=True, fmt='d', cmap='YlOrRd', ax=ax, linewidths=0.5)
        ax.set_title('地域 × 規模 の法人数ヒートマップ', fontsize=14, fontweight='bold')
        ax.set_xlabel('規模ステージ', fontsize=12)
        ax.set_ylabel('地域', fontsize=12)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        save_figure('01_distribution.png')

        return {}

"""相関分析: 収益の寄付比率とサイズの相関"""

import numpy as np
import matplotlib.pyplot as plt

from analyses.base import BaseAnalysis
from src.mappings import STAGE_ORDER
from src.plot_utils import save_figure


class CorrelationAnalysis(BaseAnalysis):
    name = 'correlation'
    description = '収益の寄付比率とサイズの相関分析'
    output_files = ['02_correlation.png']

    def run(self, df, **kwargs):
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

        corr = df_valid['log_収入'].corr(df_valid['寄付会費比_pct'])
        ax.text(0.05, 0.95, f'相関係数(log収入 vs 寄付比率): {corr:.3f}',
                transform=ax.transAxes, fontsize=11, va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        # --- 2b: ステージ別の寄付比率の箱ひげ図 ---
        ax = axes[0, 1]
        stage_present = [s for s in STAGE_ORDER if s in df_valid['ステージ'].unique()]
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

        for label in ['認定', '未認定']:
            subset = df_valid[df_valid['認定'] == label]
            print(f"  {label}: 平均寄付比率={subset['寄付会費比_pct'].mean():.1f}%, "
                  f"中央値={subset['寄付会費比_pct'].median():.1f}%, "
                  f"平均総収入={subset['総収入_百万円'].mean():.1f}百万円")

        # --- 2d: 収入規模帯ごとの寄付比率ヒストグラム ---
        ax = axes[1, 1]
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
        save_figure('02_correlation.png')

        return {}

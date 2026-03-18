"""サマリーダッシュボード: 総合KPIと主要指標の概観"""

import numpy as np
import matplotlib.pyplot as plt

from analyses.base import BaseAnalysis
from src.plot_utils import save_figure


class SummaryDashboardAnalysis(BaseAnalysis):
    name = 'summary_dashboard'
    description = '総合サマリーダッシュボード'
    output_files = ['00_summary_dashboard.png']

    def run(self, df, **kwargs):
        field_agg = kwargs.get('field_agg')
        if field_agg is None:
            raise ValueError("summary_dashboard requires field_agg from field_hypothesis analysis")

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
        save_figure('00_summary_dashboard.png')

        return {}

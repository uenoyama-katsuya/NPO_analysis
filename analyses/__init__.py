"""分析レジストリ: 全分析モジュールの登録と取得"""

from analyses.a01_distribution import DistributionAnalysis
from analyses.a02_correlation import CorrelationAnalysis
from analyses.a03_field_hypothesis import FieldHypothesisAnalysis
from analyses.a00_summary_dashboard import SummaryDashboardAnalysis

ANALYSES = [
    DistributionAnalysis(),
    CorrelationAnalysis(),
    FieldHypothesisAnalysis(),
    SummaryDashboardAnalysis(),
]


def get_analysis(name):
    """CLI用識別名から分析インスタンスを取得する

    Args:
        name: 分析の識別名

    Returns:
        BaseAnalysis: 該当する分析インスタンス。見つからない場合はNone
    """
    for analysis in ANALYSES:
        if analysis.name == name:
            return analysis
    return None

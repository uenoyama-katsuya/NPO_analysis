"""分析の共通インターフェース"""

from abc import ABC, abstractmethod


class BaseAnalysis(ABC):
    """全分析クラスの基底クラス"""

    name: str              # CLI用識別名
    description: str       # 日本語説明
    output_files: list     # 出力ファイル一覧

    @abstractmethod
    def run(self, df, **kwargs):
        """分析実行

        Args:
            df: 前処理済みDataFrame
            **kwargs: 前段の分析からの受け渡しデータ

        Returns:
            dict: 後続分析への受け渡しデータ（不要な場合は空dict）
        """

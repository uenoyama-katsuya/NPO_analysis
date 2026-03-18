"""src/loader.py のユニットテスト"""

import pytest

from src.loader import load_data
from config import DATA_DIR


class TestLoadData:
    @pytest.fixture(scope='class')
    def df(self):
        """テスト用にデータを一度だけ読み込む"""
        return load_data()

    def test_returns_dataframe(self, df):
        """DataFrameが返される"""
        import pandas as pd
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self, df):
        """必須カラムが存在する"""
        required = ['法人名', '総収入_百万円', 'ステージ', '寄付会費比_pct',
                     '認定', '地域', '活動分野_list']
        for col in required:
            assert col in df.columns, f"カラム '{col}' が見つかりません"

    def test_has_data_rows(self, df):
        """データ行が存在する"""
        assert len(df) > 0

    def test_numeric_columns_are_numeric(self, df):
        """数値カラムがnumeric型"""
        numeric_cols = ['総収入_百万円', '寄付会費比_pct']
        for col in numeric_cols:
            assert df[col].dtype in ['float64', 'int64'], f"カラム '{col}' がnumeric型ではありません"

    def test_donation_ratio_range(self, df):
        """寄付比率が0-100%またはNaN"""
        valid = df['寄付会費比_pct'].dropna()
        assert (valid >= 0).all(), "寄付比率に負の値があります"
        assert (valid <= 100).all(), "寄付比率に100%超の値があります"

    def test_region_mapping(self, df):
        """地域マッピングが適用されている"""
        valid_regions = {'東京', '関東', '近畿', '中部', '九州・沖縄',
                         '北海道・東北', '中国・四国', 'その他'}
        assert set(df['地域'].unique()).issubset(valid_regions)

    def test_custom_csv_path(self):
        """カスタムパスでも読み込める"""
        csv_path = DATA_DIR / 'npo_data.csv'
        df = load_data(csv_path=csv_path)
        assert len(df) > 0

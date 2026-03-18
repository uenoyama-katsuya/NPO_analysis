"""src/mappings.py のユニットテスト"""

from src.mappings import REGION_MAP, FIELD_SHORT, STAGE_ORDER, REGION_ORDER


class TestRegionMap:
    def test_tokyo_mapping(self):
        """東京都→東京"""
        assert REGION_MAP['東京都'] == '東京'

    def test_all_values_are_valid_regions(self):
        """全てのマッピング先が有効な地域名"""
        valid_regions = {'東京', '関東', '近畿', '中部', '九州・沖縄',
                         '北海道・東北', '中国・四国'}
        for pref, region in REGION_MAP.items():
            assert region in valid_regions, f"'{pref}' のマッピング先 '{region}' が不正"

    def test_designated_cities_mapped(self):
        """政令指定都市もマッピングされている"""
        cities = ['横浜市', '大阪市', '名古屋市', '福岡市', '京都市', '神戸市']
        for city in cities:
            assert city in REGION_MAP, f"政令指定都市 '{city}' がマッピングにありません"


class TestFieldShort:
    def test_has_entries(self):
        """短縮名が定義されている"""
        assert len(FIELD_SHORT) > 0

    def test_values_are_shorter(self):
        """短縮名が元の名前以下の長さ"""
        for full, short in FIELD_SHORT.items():
            assert len(short) <= len(full), f"'{short}' が '{full}' より長い"


class TestStageOrder:
    def test_has_stages(self):
        """ステージ順序が定義されている"""
        assert len(STAGE_ORDER) > 0

    def test_starts_with_largest(self):
        """最大規模から始まる"""
        assert STAGE_ORDER[0] == '30億～'

    def test_ends_with_smallest(self):
        """最小規模で終わる"""
        assert STAGE_ORDER[-1] == '1千万未満'


class TestRegionOrder:
    def test_has_regions(self):
        """地域順序が定義されている"""
        assert len(REGION_ORDER) > 0

    def test_starts_with_tokyo(self):
        """東京から始まる"""
        assert REGION_ORDER[0] == '東京'

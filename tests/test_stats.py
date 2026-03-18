"""src/stats.py のユニットテスト"""

import numpy as np
import pytest

from src.stats import gini_coefficient


class TestGiniCoefficient:
    def test_perfect_equality(self):
        """全員同じ値ならジニ係数≈0"""
        values = np.array([100, 100, 100, 100])
        assert gini_coefficient(values) == pytest.approx(0.0, abs=0.01)

    def test_perfect_inequality(self):
        """1人だけが全てを持つ場合、ジニ係数≈1"""
        values = np.array([0, 0, 0, 1000])
        result = gini_coefficient(values)
        assert result > 0.7

    def test_empty_array(self):
        """空配列はジニ係数0"""
        values = np.array([])
        assert gini_coefficient(values) == 0

    def test_all_zeros(self):
        """全てゼロならジニ係数0"""
        values = np.array([0, 0, 0])
        assert gini_coefficient(values) == 0

    def test_moderate_inequality(self):
        """中程度の不平等"""
        values = np.array([10, 20, 30, 40, 100])
        result = gini_coefficient(values)
        assert 0.0 < result < 1.0

    def test_single_value(self):
        """単一値"""
        values = np.array([42])
        result = gini_coefficient(values)
        assert result == pytest.approx(0.0, abs=0.01)

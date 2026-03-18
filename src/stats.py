"""共有統計関数"""

import numpy as np


def gini_coefficient(values):
    """ジニ係数を計算する

    Args:
        values: 数値の配列（numpy array）

    Returns:
        float: ジニ係数（0=完全平等、1=完全不平等）
    """
    values = np.sort(values)
    n = len(values)
    if n == 0 or values.sum() == 0:
        return 0
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * values) - (n + 1) * values.sum()) / (n * values.sum())

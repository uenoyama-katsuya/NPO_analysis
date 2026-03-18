"""設定の一元管理: パス定義・matplotlib初期化"""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import rcParams

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'


def setup_matplotlib():
    """日本語フォント設定とmatplotlib初期化"""
    rcParams['font.family'] = 'Hiragino Sans'
    rcParams['axes.unicode_minus'] = False
    rcParams['font.size'] = 10

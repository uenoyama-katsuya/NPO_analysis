"""共有描画ヘルパー"""

import matplotlib.pyplot as plt

from config import OUTPUT_DIR


def add_bar_labels(ax, bars, values, fmt='{val}', fontsize=10, offset=5, va='center', direction='h'):
    """棒グラフにラベルを追加する

    Args:
        ax: matplotlib Axes
        bars: barプロットの戻り値
        values: 表示する値のリスト
        fmt: フォーマット文字列（{val}がプレースホルダ）
        fontsize: フォントサイズ
        offset: バーからのオフセット
        va: 垂直方向のアラインメント
        direction: 'h'=横棒、'v'=縦棒
    """
    for bar, val in zip(bars, values):
        if direction == 'h':
            ax.text(bar.get_width() + offset, bar.get_y() + bar.get_height() / 2,
                    fmt.format(val=val), va=va, fontsize=fontsize)
        else:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + offset,
                    fmt.format(val=val), ha='center', va='bottom', fontsize=fontsize)


def save_figure(filename, dpi=150):
    """図をOUTPUT_DIRに保存してcloseする

    Args:
        filename: 保存ファイル名（例: '01_distribution.png'）
        dpi: 解像度
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    plt.savefig(filepath, dpi=dpi, bbox_inches='tight')
    plt.close()
    print(f"✓ {filename} を保存")

import colorsys
import hashlib

from src.components.charts.menu_analysis.PieUtils import OTHER_LABEL

# 少数項目をまとめた「その他」スライス用の固定色（無彩色）。
# 個々の商品と紛れないよう、ハッシュ生成の対象から外して固定にする。
_OTHER_COLOR = "#a0a0a0"


def color_for_label(label: str) -> str:
    """ラベル文字列から決定的な色を1つ生成する（同じラベルなら常に同じ色）。

    カテゴリ一覧をJSON側で管理する方針のため、Python側に
    「カテゴリ名→色」の対応表を手動で持たせない。ハッシュ値から色相を
    決めるだけなので、カテゴリが増減してもコード変更は不要。
    """
    if label == OTHER_LABEL:
        return _OTHER_COLOR

    digest = hashlib.md5(label.encode("utf-8")).hexdigest()
    hue = int(digest[:8], 16) % 360 / 360
    r, g, b = colorsys.hls_to_rgb(hue, 0.55, 0.55)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def colors_for_labels(labels: list[str]) -> list[str]:
    """labels の順番に対応する色リストを返す。"""
    return [color_for_label(label) for label in labels]

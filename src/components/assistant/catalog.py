"""チャートカタログ。

「AIに聞く」が選べるグラフと、その引数の選択肢を定義する。Jev への質問、LLM のツール定義、
LLM 出力の検証は、すべてここから作る。

- 期間（年月）は引数に含めない。期間はコード側（period_parser）が解釈する
- 説明文は、引数名ではなく中身の意味で書く（Jev・LLM がこの文を読んで選ぶ）
- `render` は描画関数。既存ページからの切り出しが済んだチャートから順に設定する
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

# 日報の列。月別・曜日別の「項目」の選択肢になる
_DAILY_ITEMS = {
    "売上(昼)": "昼の営業の売上",
    "客数(昼)": "昼の営業の客数",
    "客単価(昼)": "昼の営業の客単価",
    "売上(夜)": "夜の営業の売上",
    "客数(夜)": "夜の営業の客数",
    "客単価(夜)": "夜の営業の客単価",
    "1日総売上": "昼と夜を合わせた1日の売上",
    "1日総客数": "昼と夜を合わせた1日の客数",
    "1日客単価": "1日全体の客単価",
}
_SUM_ITEMS = {k: v for k, v in _DAILY_ITEMS.items() if "客単価" not in k}

_WEEKDAYS = {
    "全体": "曜日を分けず、すべての曜日の平均",
    "水": "水曜日",
    "木": "木曜日",
    "金": "金曜日",
    "土": "土曜日",
    "日": "日曜日",
}
_SLOTS = {
    "昼": "昼の営業のラーメン",
    "夜": "夜の営業のラーメン",
    "深夜": "深夜の営業のラーメン",
    "全体": "昼・夜・深夜を合わせたラーメン全体",
}
_RAMEN_MODES = {"販売数": "売れた杯数", "売上": "売上金額"}


@dataclass(frozen=True)
class ArgSpec:
    name: str
    description: str  # 何を選ぶ引数か
    options: Dict[str, str]  # 値 -> その値の意味
    default: str  # 質問で指定されていないときに使う値


@dataclass(frozen=True)
class ChartSpec:
    id: str
    description: str
    args: Tuple[ArgSpec, ...]
    render: Optional[Callable[..., Any]] = None


def _chart(id_: str, description: str, *args: ArgSpec) -> ChartSpec:
    for a in args:
        assert a.default in a.options, (id_, a.name)
    return ChartSpec(id_, description, tuple(args))


_METRIC_SALES_GUESTS = {"売上": "売上金額", "客数": "来店客数"}

CHARTS: Tuple[ChartSpec, ...] = (
    _chart(
        "daily_bar",
        "ある1か月の、1日ごとの推移を棒グラフで見る。どの日に多く、どの日に少なかったかが分かる",
        ArgSpec("metric", "見る指標", {**_METRIC_SALES_GUESTS, "客単価": "お客さん1人あたりの金額"}, "売上"),
    ),
    _chart(
        "hourly_bar",
        "ある1か月の、時間帯ごとの推移を見る。何時台が混んでいるか、売れているかが分かる",
        ArgSpec("metric", "見る指標", _METRIC_SALES_GUESTS, "客数"),
        ArgSpec("weekday", "対象の曜日", _WEEKDAYS, "全体"),
    ),
    _chart(
        "hourly_compare",
        "2つの条件（月と曜日の組み合わせ）で、時間帯ごとの推移を重ねて比べる",
        ArgSpec("metric", "比べる指標", _METRIC_SALES_GUESTS, "客数"),
        ArgSpec("weekday_a", "1つ目の条件の曜日", _WEEKDAYS, "全体"),
        ArgSpec("weekday_b", "2つ目の条件の曜日", _WEEKDAYS, "全体"),
    ),
    _chart(
        "monthly_sum",
        "月ごとの合計値の推移を、全期間にわたって見る。長期的な伸びや落ち込みが分かる",
        ArgSpec("item", "合計する項目", _SUM_ITEMS, "1日総売上"),
    ),
    _chart(
        "monthly_mean",
        "月ごとの1日あたりの平均値の推移を、全期間にわたって見る。客単価の推移もここで見る",
        ArgSpec("item", "平均する項目", _DAILY_ITEMS, "1日総売上"),
    ),
    _chart(
        "weekly_compare",
        "2つの月を、曜日ごとに並べて比べる。前の月や前の年の同じ月と比べて、どの曜日が増減したかが分かる",
        ArgSpec("item", "比べる項目", _DAILY_ITEMS, "1日総売上"),
    ),
    _chart(
        "yearly_bar",
        "年ごとの合計・平均を比べる。年単位での伸びや落ち込みが分かる",
        ArgSpec(
            "metric",
            "見る指標",
            {
                "合計客数": "その年の客数の合計",
                "合計売上": "その年の売上の合計",
                "平均客数": "1日あたりの平均客数",
                "平均売上": "1日あたりの平均売上",
                "平均客単価": "1日あたりの平均客単価",
            },
            "合計売上",
        ),
    ),
    _chart(
        "ramen_pie",
        "ラーメンの種類ごとの割合を円グラフで見る。どのラーメンが売れているかが分かる",
        ArgSpec("slot", "対象の営業時間帯", _SLOTS, "全体"),
        ArgSpec("mode", "割合の基準", _RAMEN_MODES, "販売数"),
    ),
    _chart(
        "ramen_weekday_bar",
        "ラーメンの曜日ごとの販売状況を棒グラフで見る。どの曜日によく売れるかが分かる",
        ArgSpec("slot", "対象の営業時間帯", _SLOTS, "全体"),
        ArgSpec("mode", "見る基準", _RAMEN_MODES, "販売数"),
    ),
    _chart(
        "lunch_pie",
        "ランチメニューの割合を円グラフで見る。カテゴリごとの人気や、セットメニューの中身が分かる",
        ArgSpec(
            "breakdown",
            "何の内訳を見るか",
            {"カテゴリ別": "ランチのカテゴリごとの割合", "セットメニュー内訳": "セットメニューの中身ごとの割合"},
            "カテゴリ別",
        ),
        ArgSpec("mode", "割合の基準", _RAMEN_MODES, "販売数"),
    ),
    _chart(
        "alcohol_trend",
        "アルコール（ビール・日本酒の秋鹿・ワイン）の月ごとの推移を見る",
        ArgSpec(
            "kind",
            "対象のお酒",
            {
                "アルコール合計": "すべてのアルコールの合計",
                "ビール": "ビール",
                "秋鹿": "日本酒の秋鹿",
                "若尾ワイン": "若尾ワイン",
            },
            "アルコール合計",
        ),
        ArgSpec("metric", "見る指標", {"平均杯数": "1日あたりの平均杯数", "合計売上": "月の売上の合計"}, "平均杯数"),
    ),
)

CATALOG: Dict[str, ChartSpec] = {c.id: c for c in CHARTS}

# 強調の種類。強調する点そのものはコードが算出し、モデルは種類だけを選ぶ
HIGHLIGHTS: Dict[str, str] = {
    "max": "最大の点（「一番多い」「最も売れた」など）",
    "min": "最小の点（「一番少ない」「落ち込んでいる」など）",
    "biggest_change": "前と比べて変化が最も大きい点（「伸びた」「減った」など）",
    "none": "特に目立たせたい点はない",
}

# 「どのグラフも当てはまらない」を表す選択肢（判定方式の比較用。5.4 章）
NONE_OF_THESE = "none_of_these"
NONE_OF_THESE_DESC = "どのグラフも当てはまらない、または複数のグラフが必要で1つに決められない"


def validate_request(chart_id: str, args: Dict[str, str]) -> Optional[str]:
    """チャート ID と引数がカタログに収まっているかを検査する。問題があれば理由を返し、なければ None。"""
    spec = CATALOG.get(chart_id)
    if spec is None:
        return f"未知の chart_id: {chart_id!r}"
    expected = {a.name for a in spec.args}
    if set(args) != expected:
        return f"{chart_id} の引数は {sorted(expected)} のはずが {sorted(args)}"
    for a in spec.args:
        if args[a.name] not in a.options:
            return f"{chart_id}.{a.name} の値が範囲外: {args[a.name]!r}"
    return None

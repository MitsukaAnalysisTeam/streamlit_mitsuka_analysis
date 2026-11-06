"""カタログのチャートを実際に描画する。

既存の分析ページ（pages/analytics.py）と同じ部品を、画面の選択ボックスの代わりに
引数（args）と期間から呼ぶ。ページ側の関数はまだ手を付けていないので、本実装でここと統合する。
analytics は読み込みが重い（スプレッドシートの取得）ので、描画のときに初めて読み込む。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import streamlit as st

from src.components.assistant.highlight import intercept
from src.components.assistant.period import Month, Period, clamp_to_available, month_key, shift


def _analytics():
    from src.components.pages import analytics

    return analytics


@dataclass
class Ctx:
    """描画に必要な、解釈済みの期間。"""

    start: Month
    end: Month
    compare_shift: Optional[int] = None  # 比べる相手の月（基準の月から何か月ずれるか）。None は前の月
    notes: List[str] = field(default_factory=list)

    @property
    def end_key(self) -> str:
        return month_key(self.end)

    @property
    def start_key(self) -> str:
        return month_key(self.start)

    @property
    def prev_key(self) -> str:
        return month_key(shift(self.end, self.compare_shift or -1))

    @property
    def compare_label(self) -> str:
        return "去年の同じ月との比較" if self.compare_shift == -12 else "前の月との比較"


def _ym(key: str) -> str:
    y, m = key.split("_")
    return f"{y}年{m}月"


def _daily_bar(a, args, ctx: Ctx):
    metric = args["metric"]
    data = a.dailyReportAnalysisUtils.get_df_from_dic(ctx.end_key)
    st.write(f"{_ym(ctx.end_key)}の日単位の{metric}データ")
    if metric == "客単価":
        a.dailyReportAnalysisCharts.daily_price_per_customer_bar(data)
    else:
        label = "売上額 (¥)" if metric == "売上" else "客数 (人)"
        a.dailyReportAnalysisCharts.lunch_night_stacked_bar(data, metric + "(昼)", metric + "(夜)", label)


def _hourly_data(a, month, metric):
    data = a.hourlyReportAnalysisUtils.get_df_from_dic(month, kind=metric)
    if data.empty:
        return None
    return a.hourlyReportAnalysisUtils.get_week_groupby_mean(data)


def _hourly_bar(a, args, ctx: Ctx):
    metric, weekday = args["metric"], args["weekday"]
    data = _hourly_data(a, ctx.end_key, metric)
    if data is None:
        st.warning("該当月のデータがありません")
        return
    st.write(f"{_ym(ctx.end_key)}の時間別の{metric}データ（{weekday}）")
    a.hourlyReportAnalysisCharts.week_comp_bar(data, "売上額 (¥)" if metric == "売上" else "客数 (人)", weekday)


def _hourly_compare(a, args, ctx: Ctx):
    metric = args["metric"]
    first, second = ctx.prev_key, ctx.end_key
    d1, d2 = _hourly_data(a, first, metric), _hourly_data(a, second, metric)
    if d1 is None or d2 is None:
        st.warning("比べる月のどちらかにデータがありません")
        return
    wa, wb = args["weekday_a"], args["weekday_b"]
    a.hourlyReportAnalysisCharts.compare_two_data(
        d1, d2, "売上額 (¥)" if metric == "売上" else "客数 (人)",
        f"{_ym(first)} ({wa})", f"{_ym(second)} ({wb})",
        None if wa == "全体" else wa, None if wb == "全体" else wb,
    )
    ctx.notes.append(f"{_ym(first)} と {_ym(second)} を比べています（{ctx.compare_label}）")


def _monthly_sum(a, args, ctx: Ctx):
    st.write(f"月ごとの {args['item']} の合計（全期間）")
    a.dailyReportAnalysisCharts.monthly_transfer_sum_bar(df_dic=a.dailyReportAnalysisUtils.df_dic, str1=args["item"])


def _monthly_mean(a, args, ctx: Ctx):
    st.write(f"月ごとの {args['item']} の1日平均（全期間）")
    a.dailyReportAnalysisCharts.monthly_transfer_mean_bar(df_dic=a.dailyReportAnalysisUtils.df_dic, str1=args["item"])


def _weekly_compare(a, args, ctx: Ctx):
    left, right = ctx.prev_key, ctx.end_key
    weekly = a.dailyReportAnalysisUtils.get_all_weekly_report_dic()
    try:
        df_left = weekly[left[:4]][left[5:]]
        df_right = weekly[right[:4]][right[5:]]
    except KeyError:
        st.warning("比べる月のどちらかにデータがありません")
        return
    a.dailyReportAnalysisCharts.weekly_comparison_bar(df_left, df_right, args["item"], left, right)
    ctx.notes.append(f"{_ym(left)} と {_ym(right)} を比べています（{ctx.compare_label}）")


_YEARLY = {
    "合計客数": ("年の合計客数 (人)", dict(people=True)),
    "合計売上": ("年の合計売上 (円)", dict(currency=True)),
    "平均客数": ("日次平均客数 (人)", dict(people=True)),
    "平均売上": ("日次平均売上 (円)", dict(currency=True)),
    "平均客単価": ("日次平均客単価 (円)", dict(currency=True)),
}


def _yearly_bar(a, args, ctx: Ctx):
    metric = args["metric"]
    yearly = a.yearlyReportAnalysisUtils.build_yearly_summary(a.dailyReportAnalysisUtils.df_dic, start_year=2022)
    if yearly.empty:
        st.warning("年間分析に利用できるデータがありません。")
        return
    label, kw = _YEARLY[metric]
    st.write(f"年ごとの {metric}")
    a.yearlyReportAnalysisCharts.plot_yearly_bar(yearly, metric, label, **kw)


def _ramen_frames(a, mode):
    dl = a.lunchAnalysisUtils.prepare_ramen_df_num(a.ramenAnalysisFacade.get_slot_dict("昼", mode))
    dm = a.midnightAnalysisUtils.prepare_midnight_df_num(a.ramenAnalysisFacade.get_slot_dict("深夜", mode))
    dd = a.dinerAnalysisUtils.prepare_diner_df_num(a.ramenAnalysisFacade.get_slot_dict("夜", mode))
    return dl, dd, dm


def _ramen_pie(a, args, ctx: Ctx):
    slot, mode = args["slot"], args["mode"]
    dl, dd, dm = _ramen_frames(a, mode)
    st.subheader(f"ラーメン{mode}割合（{slot}・{_ym(ctx.start_key)}〜{_ym(ctx.end_key)}）")
    a.ramenAnalysisCharts.pie_ramen_ratio_by_time(
        dl, dd, dm, time_filter=slot, month_start=ctx.start_key, month_end=ctx.end_key, mode=mode)


def _ramen_weekday_bar(a, args, ctx: Ctx):
    slot, mode = args["slot"], args["mode"]
    dl, dd, dm = _ramen_frames(a, mode)
    st.subheader(f"曜日別ラーメン{mode}（{slot}・{_ym(ctx.start_key)}〜{_ym(ctx.end_key)}）")
    a.ramenAnalysisCharts.bar_ramen_by_weekday(
        dl, dd, dm, time_filter=slot, month_start=ctx.start_key, month_end=ctx.end_key, mode=mode)


def _lunch_pie(a, args, ctx: Ctx):
    mode = args["mode"]
    target = a.lunchAnalysisFacade.get_lunch_dict(mode)
    if args["breakdown"] == "カテゴリ別":
        st.subheader(f"昼カテゴリ別{mode}割合（{_ym(ctx.end_key)}）")
        a.lunchAnalysisCharts.pie_lunch_category(target, ctx.end_key, mode)
    else:
        st.subheader(f"セットメニュー{mode}内訳（{_ym(ctx.end_key)}）")
        a.lunchAnalysisCharts.pie_set_menu(target, ctx.end_key, mode)


def _alcohol_trend(a, args, ctx: Ctx):
    kind, metric = args["kind"], args["metric"]
    st.write(f"月単位の{kind}（{metric}）")
    df_dict = a.alcoholAnalysisFacade.get_alcohol_dict(metric)
    df = a.alcoholAnalysisUtils.prepare_alcohol_df_num(df_dict).reset_index()
    u, c = a.alcoholAnalysisUtils, a.alcoholAnalysisCharts
    if kind == "アルコール合計":
        c.alchol_graph(u.get_alchol_data(df))
    elif kind == "ビール":
        c.beer_graph(u.get_beer_data(df))
    elif kind == "秋鹿":
        c.akishika_graph(u.get_akishika_data(df))
    else:
        c.wine_graph(u.get_wine_data(df))


RENDERERS: Dict[str, Callable] = {
    "daily_bar": _daily_bar,
    "hourly_bar": _hourly_bar,
    "hourly_compare": _hourly_compare,
    "monthly_sum": _monthly_sum,
    "monthly_mean": _monthly_mean,
    "weekly_compare": _weekly_compare,
    "yearly_bar": _yearly_bar,
    "ramen_pie": _ramen_pie,
    "ramen_weekday_bar": _ramen_weekday_bar,
    "lunch_pie": _lunch_pie,
    "alcohol_trend": _alcohol_trend,
}

# 期間を使わず、全期間を見るチャート
_ALL_PERIOD = {"monthly_sum", "monthly_mean", "yearly_bar", "alcohol_trend"}


def render(chart_id: str, args: Dict[str, str], period: Optional[Period], highlight: Optional[str],
           compare_shift: Optional[int] = None) -> List[str]:
    """チャートを描画する。画面に添える説明（期間の解釈・強調の内容）を返す。"""
    a = _analytics()
    available = a.dailyReportAnalysisUtils.get_month_list()
    notes: List[str] = []

    if period is None:
        last = tuple(int(x) for x in available[-1].split("_"))
        ctx = Ctx(start=last, end=last, compare_shift=compare_shift)  # type: ignore[arg-type]
        if chart_id not in _ALL_PERIOD:
            notes.append(f"期間の指定がないため、最新の {last[0]}年{last[1]}月 を使います")
    else:
        start, end, note = clamp_to_available(period, available)
        ctx = Ctx(start=start, end=end, compare_shift=compare_shift)
        notes.append(f"期間: {period.label}")
        if note:
            notes.append(note)
    if chart_id in _ALL_PERIOD:
        notes = ["このグラフは全期間を表示します（期間の指定は使いません）"]

    hl_notes: List[str] = []
    try:
        with intercept(highlight, hl_notes):
            RENDERERS[chart_id](a, args, ctx)
    except Exception as e:  # noqa: BLE001
        st.error(f"描画でエラーが発生しました: {e}")
    notes.extend(ctx.notes)
    if highlight and highlight != "none":
        notes.append("強調: " + (" / ".join(hl_notes) if hl_notes else "このグラフでは強調できませんでした"))
    return notes

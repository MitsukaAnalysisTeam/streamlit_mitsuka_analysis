import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.components.charts.menu_analysis.ColorPalette import colors_for_labels
from src.components.charts.menu_analysis.PieUtils import (
    OTHER_LABEL,
    group_minor_slices,
    legend_hint_annotation,
    other_slice_legend_label,
)
from src.components.utils.menu_analysis.s2_classification.CategoryUnifyMap import CategoryUnifyMap


class LunchAnalysisCharts:
    def __init__(self, category_unify_map: CategoryUnifyMap = None):
        self._category_unify_map = category_unify_map or CategoryUnifyMap()

    def pie_lunch_category(
        self,
        df_dict: dict,
        selected_month: str,
        mode: str = "販売数"
    ) -> None:
        year  = int(selected_month[:4])
        month = int(selected_month.split('_')[1])

        def _sum_key(key: str) -> float:
            df = df_dict[key].copy()
            if not pd.api.types.is_datetime64_any_dtype(df.index):
                df.index = pd.to_datetime(df.index)

            # 指定年月のデータを抽出
            target_df = df[(df.index.year == year) & (df.index.month == month)]
            # 全カラムの合計を合算して返す
            return float(pd.to_numeric(target_df.values.flatten(), errors='coerce').sum())

        # df_dictはLunchAnalysisFacadeが既に「昼ページに出すべきカテゴリ」に
        # 絞り込み・リネーム済みなので、キーをそのまま対象にする
        totals_dict = {key: _sum_key(key) for key in df_dict.keys()}
        totals = pd.Series(totals_dict)
        totals = totals[totals > 0].sort_values(ascending=False)

        if totals.empty:
            st.warning(f"{year}年{month}月のデータがありません。")
            return

        # 全体に占める割合が3%未満のスライスは「その他」に合算する
        other_legend_label = other_slice_legend_label(totals)
        grouped = group_minor_slices(totals)
        display_labels = grouped.index.tolist()
        # 凡例・ホバーには「その他」の中身を表示し、スライス上の文字は短いままにする
        legend_labels = [
            other_legend_label if lbl == OTHER_LABEL and other_legend_label else lbl
            for lbl in display_labels
        ]
        values = grouped.values.tolist()

        fig = go.Figure(go.Pie(
            labels=legend_labels,
            values=values,
            text=display_labels,
            textinfo="text+percent",
            textfont=dict(size=11),
            insidetextorientation='horizontal',
            hole=0.3,
            sort=False, # 割合順の自動並び替えをしない（「その他」を必ず最後にするため）
            direction='clockwise',
            rotation=0,
            marker_colors=colors_for_labels(display_labels),
            # 円グラフ自体を上78%に収め、下22%をヒント表示用に空けておく
            domain=dict(y=[0.22, 1]),
        ))
        fig.update_layout(
            title_text=f"{year}年{month}月 昼カテゴリ別{mode}割合",
            margin=dict(l=50, r=50, t=80, b=90),
            height=670,
            legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
            annotations=[legend_hint_annotation(y=0.02)], # 円グラフ(上78%)と凡例(マイナス側)の間の空白に配置
        )
        st.plotly_chart(fig, use_container_width=True)

    def pie_set_menu(
        self,
        df_dict: dict,
        selected_month: str,
        mode: str = "販売数"
    ) -> None:
        # セット系(flag=2)のうち、実際にdf_dictに存在するキーを対象にする。
        # 'セット'はLunchAnalysisFacadeが'昼セット'をリネームして作る
        # このページ固有の表示名（menu.json上のカテゴリ名ではない）なので、
        # flagでは判定できず明示的に含める。
        set_keys = [
            key for key in df_dict.keys()
            if key == "セット" or "2" in self._category_unify_map.flags(key)
        ]

        year = int(selected_month[:4])
        month = int(selected_month.split('_')[1])

        def _sum_by_item(key: str) -> pd.Series:
            df = df_dict[key].copy()
            if not pd.api.types.is_datetime64_any_dtype(df.index):
                df.index = pd.to_datetime(df.index)
            df = df[(df.index.year == year) & (df.index.month == month)]
            return df.apply(pd.to_numeric, errors='coerce').sum()

        if not set_keys:
            st.warning("該当月のセットデータがありません")
            return

        combined = pd.concat([_sum_by_item(k) for k in set_keys]).fillna(0)
        combined = combined[combined > 0]

        if combined.empty:
            st.warning("該当月のセットデータがありません")
            return

        # 全体に占める割合が3%未満のスライスは「その他」に合算する。
        # 'その他'以外は降順、'その他'は並び替えの対象から外して常に末尾に固定する。
        other_legend_label = other_slice_legend_label(combined)
        combined = combined.sort_values(ascending=False)
        combined = group_minor_slices(combined)

        display_labels = combined.index.tolist()
        # 凡例・ホバーには「その他」の中身を表示し、スライス上の文字は短いままにする
        legend_labels = [
            other_legend_label if lbl == OTHER_LABEL and other_legend_label else lbl
            for lbl in display_labels
        ]
        values = combined.values.tolist()

        fig = go.Figure(go.Pie(
            labels=legend_labels,
            values=values,
            text=display_labels,
            textinfo="text+percent",
            textfont=dict(size=11),
            insidetextorientation='horizontal',
            hole=0.3,
            sort=False, # 割合順の自動並び替えをしない（「その他」を必ず最後にするため）
            direction='clockwise',
            rotation=0,
            marker_colors=colors_for_labels(display_labels),
            # 円グラフ自体を上78%に収め、下22%をヒント表示用に空けておく
            domain=dict(y=[0.22, 1]),
        ))

        fig.update_layout(
            title_text=f"{year}年{month}月 セットメニュー{mode}内訳",
            title_font_size=16,
            margin=dict(l=50, r=50, t=80, b=90),
            height=590,
            showlegend=True,
            legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
            annotations=[legend_hint_annotation(y=0.02)], # 円グラフ(上78%)と凡例(マイナス側)の間の空白に配置
        )
        st.plotly_chart(fig, use_container_width=True)

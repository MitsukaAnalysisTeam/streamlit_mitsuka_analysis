import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


class LunchAnalysisCharts:
    def __init__(self):
        pass

    def pie_lunch_category(
        self,
        df_dict: dict,
        selected_month: str,
    ) -> None:
        TARGET_KEYS = [
            "カリー", "カリーつけ麺", "海老みそ", "焦がし海老味噌",
            "ベジ味噌", "白味噌", "温玉カレーラーメン", "油そば",
            "発酵唐揚げプレート",
            "発酵御膳",
            "キッズ"
        ]

        year  = int(selected_month[:4])
        month = int(selected_month.split('_')[1])

        def _sum_key(key: str) -> float:
            # 部分一致をやめ、直接指定に変更
            if key not in df_dict:
                return 0.0
            
            df = df_dict[key].copy()
            if not pd.api.types.is_datetime64_any_dtype(df.index):
                df.index = pd.to_datetime(df.index)
            
            # 指定年月のデータを抽出
            target_df = df[(df.index.year == year) & (df.index.month == month)]
            # 全カラムの合計を合算して返す
            return float(pd.to_numeric(target_df.values.flatten(), errors='coerce').sum())

        totals_dict = {key: _sum_key(key) for key in TARGET_KEYS}
        totals = pd.Series(totals_dict)
        totals = totals[totals > 0].sort_values(ascending=False)

        if totals.empty:
            st.warning(f"{year}年{month}月のデータがありません。")
            return

        fig = go.Figure(go.Pie(
            labels=totals.index.tolist(),
            values=totals.values.tolist(),
            textinfo="label+percent",
            hole=0.3,
            sort=True, # グラフを降順にする
            direction='clockwise',
            rotation=0,
        ))
        fig.update_layout(
            title_text=f"{year}年{month}月 昼カテゴリ別提供数",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    def pie_set_menu(
        self,
        df_dict: dict,
        selected_month: str,
    ) -> None:
        SET_KEYS = ["セット", "ラーメンセット"]
        year = int(selected_month[:4])
        month = int(selected_month.split('_')[1])

        def _sum_by_item(key: str) -> pd.Series:
            if key not in df_dict: return pd.Series(dtype=float)
            df = df_dict[key].copy()
            if not pd.api.types.is_datetime64_any_dtype(df.index):
                df.index = pd.to_datetime(df.index)
            df = df[(df.index.year == year) & (df.index.month == month)]
            return df.apply(pd.to_numeric, errors='coerce').sum()

        combined = pd.concat([_sum_by_item(k) for k in SET_KEYS]).fillna(0)
        combined = combined[combined > 0]

        if combined.empty:
            st.warning("該当月のセットデータがありません")
            return

        combined = combined.sort_index(ascending=True)

        fig = go.Figure(go.Pie(
            labels=combined.index.tolist(),
            values=combined.values.tolist(),
            textinfo="label+percent",
            hole=0.3,
            sort=True, 
            direction='clockwise',
            rotation=0,
            marker_colors=px.colors.qualitative.Set2,
        ))

        fig.update_layout(
            title_text=f"{year}年{month}月 セットメニュー内訳",
            title_font_size=16,
            margin=dict(l=20, r=20, t=60, b=20),
            height=420,
            showlegend=True 
        )
        st.plotly_chart(fig, use_container_width=True)
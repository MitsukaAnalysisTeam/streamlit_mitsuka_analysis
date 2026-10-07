import pandas as pd


class YearlyReportAnalysisUtils:
    """
    年別分析用の集計ユーティリティ。
    DailyReportAnalysisUtils.df_dic（年->月->DataFrame）を受け取り、
    年ごとの合計/平均指標を作成する。
    """

    REQUIRED_COLUMNS = ["1日総客数", "1日総売上", "1日客単価"]

    def build_yearly_summary(self, df_dic: dict, start_year: int = 2022) -> pd.DataFrame:
        yearly_rows: list[dict] = []

        for year in sorted(df_dic.keys(), key=int):
            year_int = int(year)
            if year_int < start_year:
                continue

            monthly_frames = []
            for month_df in df_dic.get(year, {}).values():
                if month_df is None or month_df.empty:
                    continue
                if not set(self.REQUIRED_COLUMNS).issubset(month_df.columns):
                    continue
                monthly_frames.append(month_df[self.REQUIRED_COLUMNS].copy())

            if not monthly_frames:
                continue

            yearly_df = pd.concat(monthly_frames, axis=0)
            if yearly_df.empty:
                continue

            # 文字列混在を考慮して数値化
            for col in self.REQUIRED_COLUMNS:
                yearly_df[col] = pd.to_numeric(yearly_df[col], errors="coerce")

            yearly_df = yearly_df.dropna(subset=["1日総客数", "1日総売上", "1日客単価"], how="all")
            if yearly_df.empty:
                continue

            yearly_rows.append(
                {
                    "year": str(year_int),
                    "合計客数": yearly_df["1日総客数"].sum(skipna=True),
                    "合計売上": yearly_df["1日総売上"].sum(skipna=True),
                    "平均客数": yearly_df["1日総客数"].mean(skipna=True),
                    "平均売上": yearly_df["1日総売上"].mean(skipna=True),
                    "平均客単価": yearly_df["1日客単価"].mean(skipna=True),
                }
            )

        if not yearly_rows:
            return pd.DataFrame()

        result_df = pd.DataFrame(yearly_rows).set_index("year")
        return result_df

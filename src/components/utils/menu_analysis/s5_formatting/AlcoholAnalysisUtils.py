import pandas as pd

from src.components.utils.menu_analysis.s2_classification.CategoryUnifyMap import CategoryUnifyMap


class AlcoholAnalysisUtils:
    def __init__(self, category_unify_map: CategoryUnifyMap = None):
        self._category_unify_map = category_unify_map or CategoryUnifyMap()

    def _columns_by_flag(self, flag: str) -> list:
        return list(self._category_unify_map.items_by_flag(flag).keys())

    def get_wine_data(
            self,
            df: pd.DataFrame
            )-> pd.DataFrame:
        cols = self._columns_by_flag("4.3")
        return df[["日付"] + cols]


    def get_akishika_data(
            self,
            df: pd.DataFrame
            )-> pd.DataFrame:
        cols = self._columns_by_flag("4.2")
        return df[["日付"] + cols]

    def get_beer_data(
            self,
            df: pd.DataFrame
            )-> pd.DataFrame:
        cols = self._columns_by_flag("4.1")
        return df[["日付"] + cols]

    def get_alchol_data(
            self,
            data_type: str
            ) -> pd.DataFrame:
        data_beer = self.get_beer_data(data_type)
        data_akishika = self.get_akishika_data(data_type)
        data_wine = self.get_wine_data(data_type)

        dates = data_beer["日付"]

        sum_beer = data_beer.drop(columns=["日付"]).sum(axis=1)
        sum_akishika = data_akishika.drop(columns=["日付"]).sum(axis=1)
        sum_wine = data_wine.drop(columns=["日付"]).sum(axis=1)


        summary_df = pd.DataFrame({
            "日付": dates,
            "ビール": sum_beer,
            "秋鹿": sum_akishika,
            "ワイン": sum_wine
        })

        return summary_df

    def prepare_alcohol_df_num(self, df_dict: dict) -> pd.DataFrame:
        """
        カテゴリ別に集計済みのDataFrame辞書から、日々の売上合計を算出して
        一つのDataFrameにまとめる関数。
        """
        alcohol_keys = self._columns_by_flag("4")

        alcohol_series_list = []
        for key in alcohol_keys:
            if key in df_dict:
                series_sum = df_dict[key].sum(axis=1).rename(key)
                alcohol_series_list.append(series_sum)
            else:
                # データがないカテゴリについては警告を出す（任意）
                print(f"Warning: Category '{key}' not found in df_dict")

        # データが一つもなかった場合は、空のDataFrameを返す
        if not alcohol_series_list:
            return pd.DataFrame()

        # リストに格納したすべてのSeriesを一度に連結する
        alcohol_df = pd.concat(alcohol_series_list, axis=1)

        # NaN（対象の日に売上がなかった商品など）を0で埋める
        alcohol_df = alcohol_df.fillna(0)

        return alcohol_df

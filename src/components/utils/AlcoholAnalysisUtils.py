import os
import pandas as pd
import streamlit as st

class AlcoholAnalysisUtils:
    def get_wine_data(
            self,
            df: pd.DataFrame
            )-> pd.DataFrame: 
        
        df = df[["日付","一升瓶ワイン","ボトルワイン"]]
        return df
    

    def get_akishika_data(
            self,
            df: pd.DataFrame
            )-> pd.DataFrame: 
        
        df = df[["日付", "秋鹿", "ハイボール", "りんごカクテル", "りんごと熱燗", "梅酒"]]
        return df

    def get_beer_data(
            self,
            df: pd.DataFrame
            )-> pd.DataFrame: 
        
        df = df[["日付", "ドラフト", "リアル", "ボトル", "ハッピーアワー", "オリゼ", "ビール祭り", "スタッフ"]]
        return df

    def get_alchol_data(
            sef,
            data_type: str
            ) -> pd.DataFrame:
        alcoholAnalysisUtils = AlcoholAnalysisUtils()

        data_beer = alcoholAnalysisUtils.get_beer_data(data_type)
        data_akishika = alcoholAnalysisUtils.get_akishika_data(data_type)
        data_wine = alcoholAnalysisUtils.get_wine_data(data_type)

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
        alcohol_keys = self.__get_alcohol_list()
        
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
    
    def __get_alcohol_list(self):
        alcohol_list = [
            "ドラフト",
            "リアル",
            "ボトル",
            "ハッピーアワー",
            "オリゼ",
            "ビール祭り",
            "スタッフ",
            "一升瓶ワイン",
            "ボトルワイン",
            "秋鹿",
            "ハイボール",
            "りんごカクテル",
            "りんごと熱燗",
            "梅酒"
        ]
        return alcohol_list
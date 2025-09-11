import pandas as pd
import numpy as np
import japanize_matplotlib
import src.components.utils.SpreadSheets as SpreadSheets
japanize_matplotlib.japanize()

class GetByProductDf:
    def __init__(self):
        self.df_all_val = self.get_all_val_num()
        self.df_all_sale = self.get_all_val_sale()

    def get_all_val_num(
            self
            ) -> pd.DataFrame: 
        return self.get_df_from_ss("シート1",folder_id="1PcE7B214T7bm-BaRqOlmH2WjI2WjI2PjyA88",spreadsheet_name="バリエーション別販売数_all")
    

    def get_all_val_sale(
        self
        ) -> pd.DataFrame: 
        return self.get_df_from_ss("シート1",folder_id="1PcE7B214T7bm-BaRqOlmH2WjI2WjI2PjyA88",spreadsheet_name="バリエーション別売上_all")


    def get_df_from_ss(self,
                       sheet_name:str,
                       folder_id: str,
                       spreadsheet_name: str
                       ) -> pd.DataFrame:
        try:
            spreadsheet = SpreadSheets.SpreadSheets()
            ss_id = spreadsheet.get_spreadsheet_id_by_name(
                folder_id=folder_id,
                spreadsheet_name=spreadsheet_name
            )
            ss = spreadsheet.get_spreadsheet_by_id(ss_id)
            worksheet = ss.worksheet(sheet_name)
            df = spreadsheet.get_df_from_worksheet(worksheet)

            if "日付" in df.columns:
                # フォーマット指定を外して自動判別に任せる
                df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
                df = df.dropna(subset=["日付"])   # 変換失敗行を除去
                df = df.set_index("日付")
            df = df.replace(r"^\s*$", np.nan, regex=True)
            # print(df)
            return df
        except Exception as e:
            print(f"get_df_from_ss でエラー: {e}")
            return pd.DataFrame()

    def json_to_df_dict(self, 
                 df_all: pd.DataFrame,
                 json_dict: dict
                 ) -> dict:
        '''
        jsonのキーをもとに、df_allから対応するDataFrameを抽出して辞書で返す
        '''
        df_dict = {}
        for key, value in json_dict.items():
            df_dict[key] = df_all[value].fillna(0).astype(int)
        print(df_dict)
        return df_dict
        

import pandas as pd

from src.components.utils.common.SpreadSheets import SpreadSheets

WEEKDAY_MAP = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}

# 会計別データ(2026-06-01〜)を溜めているスプレッドシート。
# Airレジの生エクスポートを月別に整形→結合したものを、この1シートに
# 全期間分まとめてもらう運用（data/raw/transaction/の会計別_*.csvに代わるもの）。
FOLDER_ID = "1Mo_iHgAY_hywn2liUfZ07N636EMpcPC8"
SPREADSHEET_NAME = "会計別_全期間まとめ"
SHEET_NAME = "シート1"


class LoaderAfter202606:
    def __init__(
        self,
        folder_id: str = FOLDER_ID,
        spreadsheet_name: str = SPREADSHEET_NAME,
        sheet_name: str = SHEET_NAME,
        spread_sheets: SpreadSheets = None,
    ):
        self._folder_id = folder_id
        self._spreadsheet_name = spreadsheet_name
        self._sheet_name = sheet_name
        self._spread_sheets = spread_sheets or SpreadSheets()
        # 旧データ(LoaderBefore202606)と同じく、インスタンス生成時に一度だけ
        # スプレッドシートを取得してキャッシュする（呼び出しのたびに毎回
        # 取得し直していたのを解消するため）。
        self._transactions = self._load_transactions()

    def get_transactions(self) -> pd.DataFrame:
        return self._transactions

    def _load_transactions(self) -> pd.DataFrame:
        df = self._read_spreadsheet()
        if df.empty:
            return df

        df["会計日"] = pd.to_datetime(df["会計日"], format="%Y/%m/%d").dt.date
        df["会計時間"] = pd.to_datetime(df["会計時間"], format="%H:%M:%S").dt.time
        df["曜日"] = pd.to_datetime(df["会計日"]).dt.weekday.map(WEEKDAY_MAP)
        # スプレッドシートのセルは文字列で返ってくるため、計算前に数値へ変換する
        df["価格"] = pd.to_numeric(df["価格"], errors="coerce")
        df["注文数量"] = pd.to_numeric(df["注文数量"], errors="coerce")
        df["明細金額"] = df["価格"] * df["注文数量"]

        return df

    def _read_spreadsheet(self) -> pd.DataFrame:
        spreadsheet_id = self._spread_sheets.get_spreadsheet_id_by_name(
            self._folder_id, self._spreadsheet_name
        )
        if not spreadsheet_id:
            return pd.DataFrame()

        spreadsheet = self._spread_sheets.get_spreadsheet_by_id(spreadsheet_id)
        worksheet = self._spread_sheets.get_worksheet_by_name(spreadsheet, self._sheet_name)
        if worksheet is None:
            return pd.DataFrame()

        return self._spread_sheets.get_df_from_worksheet(worksheet)

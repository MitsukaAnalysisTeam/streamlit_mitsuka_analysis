import datetime

LUNCH_START = datetime.time(11, 30)
LUNCH_END = datetime.time(14, 30)
SUNSET_END = datetime.time(17, 30)
DINNER_END = datetime.time(22, 0)

LUNCH_WEEKDAYS = {"水", "木", "金", "土"}


def classify(checkout_time: datetime.time, weekday: str) -> str:
    """会計時間と曜日('月'..'日')から時間帯を返す。
    返り値: '昼' | 'サンセット' | '夜' | '深夜'

    日曜日は営業時間が11:30-22:00で、昼・夜の内容が通常のディナーメニューになる
    という店舗ルールがあるが、時間帯の判定自体は時計上の時間でのみ行う。
    ラーメン系集計での日曜除外は is_lunch_weekday() を別途使うこと。
    """
    if checkout_time < LUNCH_START:
        # 0時台など早朝 = 前日深夜の扱い（TODO: 要確認）
        return "深夜" if weekday != "日" else "夜"
    if checkout_time < LUNCH_END:
        return "昼"
    if checkout_time < SUNSET_END:
        return "サンセット"
    if checkout_time < DINNER_END:
        return "夜"
    # 22:00以降
    return "夜" if weekday == "日" else "深夜"


def is_lunch_weekday(weekday: str) -> bool:
    """昼(ランチ)時間帯の集計に含めてよい曜日かどうか。
    日曜日の昼はレギュラーのディナーメニューが提供されるため除外する。
    """
    return weekday in LUNCH_WEEKDAYS

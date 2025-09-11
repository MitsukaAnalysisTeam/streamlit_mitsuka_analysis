import json

# JSONファイルを読み込む
def read_json_file(filepath: str
                    ) -> list:
    with open(filepath, 'r', encoding='-utf-8') as f:
        data = json.load(f)
    menu_dict = data
    return menu_dict

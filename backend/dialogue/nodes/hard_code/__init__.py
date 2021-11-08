import importlib
from config import global_config

PROJECT_NAME = global_config["project_name"]

if PROJECT_NAME == "wang_zheng_tong":
    from . import wang_zheng_tong
    hard_code_intent = {
        "1455788106113400834": wang_zheng_tong.IntentLocationNoGuangDong()
    }
    hard_code_entities = {
        "@sys.recent_intent_and_says": wang_zheng_tong.recent_intent_and_syas
    }
else:
    hard_code_intent = {}
    hard_code_entities = {}
     
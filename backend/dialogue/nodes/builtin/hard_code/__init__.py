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
elif PROJECT_NAME == "guangdong_prison":
    from . import guangdong_prison
    hard_code_intent = {}
    hard_code_entities = {
        "@sys.guangdong_prison.prison": guangdong_prison.prison,
        "@sys.guangdong_prison.prison_area": guangdong_prison.prison_area,
        "@sys.guangdong_prison.prison_dormitory": guangdong_prison.prison_dormitory,
        "@sys.guangdong_prison.floor": guangdong_prison.floor,
        "@sys.guangdong_prison.number": guangdong_prison.number,
        "@sys.person": guangdong_prison.person,
    }
else:
    hard_code_intent = {}
    hard_code_entities = {}
     
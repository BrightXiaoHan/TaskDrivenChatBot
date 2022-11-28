from config import global_config

PROJECT_NAME = global_config["project_name"]

hard_code_intent = {}
hard_code_entities = {}


if "shejiao" in PROJECT_NAME:
    from . import shejiao

    hard_code_intent.update(
        {"1455788106113400834": shejiao.IntentLocationNoGuangDong()}
    )
    hard_code_entities.update(
        {"@sys.recent_intent_and_says": shejiao.recent_intent_and_syas}
    )
if "guangdong_prison" in PROJECT_NAME:
    from . import guangdong_prison

    hard_code_entities.update(
        {
            "@sys.guangdong_prison.prison": guangdong_prison.prison,
            "@sys.guangdong_prison.prison_area": guangdong_prison.prison_area,
            "@sys.guangdong_prison.prison_dormitory": guangdong_prison.prison_dormitory,
            "@sys.guangdong_prison.floor": guangdong_prison.floor,
            "@sys.guangdong_prison.number": guangdong_prison.number,
            "@sys.person": guangdong_prison.person,
        }
    )

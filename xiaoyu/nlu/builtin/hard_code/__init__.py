from typing import Callable, Dict, Optional

from config import global_config

PROJECT_NAME: Optional[str] = global_config.get("project_name", None)

hard_code_intent: Dict[str, Callable] = {}
hard_code_entities: Dict[str, Callable] = {}


if "shejiao" == PROJECT_NAME or "all" == PROJECT_NAME:
    from . import shejiao

    hard_code_intent.update({"1455788106113400834": shejiao.shejiao_intent_location_no_guangdong})
if "guangdong_prison" in PROJECT_NAME or "all" == PROJECT_NAME:
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

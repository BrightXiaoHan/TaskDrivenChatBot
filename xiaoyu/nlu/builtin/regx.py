import re
from typing import TYPE_CHECKING, Dict, List

import cn2an

if TYPE_CHECKING:
    from xiaoyu.nlu.interpreter import Message

internal_regx_ability: Dict[str, List[str]] = {
    "@sys.plates": ["[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]{1}[A-Z查叉插]{1}-?[A-Z0-9查叉插]{4}[A-Z0-9挂学警港澳查叉插]{1}[A-Z0-9查叉插]?"],
    "@sys.phone": [r"(?:(?:\+|00)86)?1[3-9]\d{9}"],
    "@sys.tel": [r"(?:(?:\d{3}-)?\d{8}|^(?:\d{4}-)?\d{7,8})(?:-\d+)?"],
}

internal_regx_ability: Dict[str, List[re.Pattern]] = {
    key: [re.compile(item) for item in value] for key, value in internal_regx_ability.items()
}


def builtin_regx(msg: Message) -> None:
    # 解析内置能力正则
    text = cn2an.transform(msg.text, "cn2an")
    for k, vs in internal_regx_ability.items():
        for v in vs:
            regx_values = v.findall(text)
            if regx_values:
                msg.add_entities(k, regx_values)

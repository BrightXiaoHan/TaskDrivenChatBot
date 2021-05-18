import re

internal_regx_ability = {
    "@sys.plates": ["[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]{1}[A-Z查叉插]{1}-?[A-Z0-9查叉插]{4}[A-Z0-9挂学警港澳查叉插]{1}[A-Z0-9查叉插]?"],
    "@sys.phone": ["/^(?:(?:\+|00)86)?1[3-9]\d{9}$/",
                   "/^(?:(?:\d{3}-)?\d{8}|^(?:\d{4}-)?\d{7,8})(?:-\d+)?$/"]
}

internal_regx_ability = {key: [re.compile(item) for item in value]
                         for key, value in internal_regx_ability.items()}


def builtin_regx(msg):
    # 解析内置能力正则
    for k, vs in internal_regx_ability.items():
        for v in vs:
            regx_values = v.findall(msg.text)
            if regx_values:
                msg.add_entities(k, regx_values)
    return
    yield None

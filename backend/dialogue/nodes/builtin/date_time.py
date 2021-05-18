"""
识别并标准化日期和时间
"""
from pyunit_time import Time

__all__ = ["builtin_date_time"]


def normalize_date_time(text):
    result = Time().parse(text)
    if len(result) == 0:
        return None, None
    key_time = result[0]["keyDate"].split()[1]
    base_time = result[0]["baseDate"].split()[1]
    result_time = key_time.split(":")[0]
    for t1, t2 in zip(key_time.split(":")[1:], base_time.split(":")[1:]):
        if t1 == t2:
            result_time += ":00"
        else:
            result_time += ":" + t1

    date = result[0]["keyDate"].split()[0]
    return date, result_time


def builtin_date_time(msg):
    date, ctime = normalize_date_time(msg.text)
    if date:
        msg.add_entities("@sys.date", date)
    if ctime:
        msg.add_entities("@sys.time", ctime)

    return
    yield None


if __name__ == "__main__":
        while True:
            text = input("请输入待识别的文字: ")
            print(normalize_date_time(text))
"""
内置的定制化识别能力
"""
from .asr_car_number import AsrCarnumber
from .whether import WhetherNode

builtin_nodes = {
    "@sys.asr_carnumber": AsrCarnumber()
}

builtin_intent = {
    "@sys.intent.confirm": WhetherNode(),
    "@sys.intent.deny": WhetherNode()
}
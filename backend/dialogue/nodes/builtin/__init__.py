"""
内置的定制化识别能力
"""
from .asr_car_number import AsrCarnumber

builtin_nodes = {
    "@sys.asr_carnumber": AsrCarnumber()
}

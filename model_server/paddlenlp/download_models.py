from paddlenlp import Taskflow

cls = Taskflow("zero_shot_text_classification")
del cls

ie = Taskflow("information_extraction")
del ie

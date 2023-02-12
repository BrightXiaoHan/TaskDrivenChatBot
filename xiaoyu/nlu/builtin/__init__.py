"""
内置的定制化识别能力
"""
from typing import Callable, Dict

from .asr_car_number import AsrCarnumber
from .date_time import builtin_date_time
from .hard_code import hard_code_entities, hard_code_intent
from .intent_slot import (
    builtin_recent_intent,
    builtin_recent_usersays,
    recent_intent_and_syas,
)
from .paddle_ner import builtin_paddle_ner
from .regx import builtin_regx
from .spacy_ner import builtin_spacy_ner
from .whether import builtin_whether

builtin_intent: Dict[str, Callable] = {"@sys.intent.confirm": builtin_whether, "@sys.intent.deny": builtin_whether}

builtin_entities: Dict[str, Callable] = {
    "@sys.recent_intent": builtin_recent_intent,
    "@sys.recent_usersays": builtin_recent_usersays,
    "@sys.recent_intent_and_says": recent_intent_and_syas,
    # date_time.py
    "@sys.date": builtin_date_time,
    "@sys.time": builtin_date_time,
    "@sys.datetime": builtin_date_time,
    # regx.py
    "@sys.plates": builtin_regx,
    "@sys.phone": builtin_regx,
    # spacy_ner.py
    "@sys.num": builtin_spacy_ner,
    "@sys.event": builtin_spacy_ner,
    "@sys.language": builtin_spacy_ner,
    "@sys.law": builtin_spacy_ner,
    "@sys.money": builtin_spacy_ner,
    "@sys.norp": builtin_spacy_ner,
    "@sys.ordinal": builtin_spacy_ner,
    "@sys.org": builtin_spacy_ner,
    "@sys.percent": builtin_spacy_ner,
    "@sys.product": builtin_spacy_ner,
    "@sys.quantity": builtin_spacy_ner,
    "@sys.work_of_art": builtin_spacy_ner,
    # paddle_ner.py
    "@sys.loc": builtin_paddle_ner,
    "@sys.gpe": builtin_paddle_ner,
    "@sys.person": builtin_paddle_ner,
    # asr_car_number.py
    "@sys.asr_carnumber": AsrCarnumber(),
}


ne_extract_funcs = list(hard_code_entities.values())


def builtin_ne_extract(msg, name):
    if name in builtin_entities:
        builtin_entities[name](msg)

    if name in hard_code_entities:
        hard_code_entities[name](msg)


def buitin_intent_classify(msg, name):
    if name in builtin_intent:
        builtin_intent[name](msg)

    if name in hard_code_intent:
        hard_code_intent[name](msg)

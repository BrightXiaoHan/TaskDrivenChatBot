"""
用于将最近一次对话的intent存入词槽中
"""
from typing import TYPE_CHECKING

from utils.define import UNK

if TYPE_CHECKING:
    from xiaoyu.nlu.interpreter import Message


def builtin_recent_intent(msg: Message) -> None:
    if msg.intent != UNK:
        intent_id = msg.intent
    elif msg.intent_ranking:
        intent_id = max(msg.intent_ranking, key=lambda key: msg.intent_ranking[key])
    else:
        intent_id = UNK
    intent_name = msg.get_intent_name_by_id(intent_id)
    msg.add_entities("@sys.recent_intent", intent_name)


def builtin_recent_usersays(msg: Message) -> None:
    msg.add_entities("@sys.recent_usersays", msg.text_without_modal)


def recent_intent_and_syas(msg: Message) -> None:
    if msg.intent == UNK:
        msg.add_entities("@sys.recent_intent_and_says", msg.text_without_modal)
    else:
        intent_name = msg.get_intent_name_by_id(msg.intent)
        msg.add_entities("@sys.recent_intent_and_says", intent_name)

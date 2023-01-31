"""
用于将最近一次对话的intent存入词槽中
"""
from utils.define import UNK


def builtin_recent_intent(msg):
    if msg.intent != UNK:
        intent_id = msg.intent
    elif msg.intent_ranking:
        intent_id = max(msg.intent_ranking, key=lambda key: msg.intent_ranking[key])
    else:
        intent_id = UNK
    intent_name = msg.get_intent_name_by_id(intent_id)
    msg.add_entities("@sys.recent_intent", intent_name)
    return iter(())


def builtin_recent_usersays(msg):
    msg.add_entities("@sys.recent_usersays", msg.text_without_modal)
    return iter(())

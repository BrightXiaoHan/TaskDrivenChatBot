from utils.define import UNK
from backend.dialogue.nodes.builtin.paddle_ner import builtin_paddle_ner
from backend.nlu.interpreter import Message


class IntentLocationNoGuangDong(object):

    def on_process_msg(self, msg: Message, node):
        if "@sys.intent.location_no_dongguan" in node.config["node_name"]:
            try:
                next(builtin_paddle_ner(msg))
            except StopIteration:
                pass
            if ("@sys.loc" in msg.entities or "@sys.gpe" in msg.entities) and "东莞" not in msg.text:
                msg.add_intent_ranking("1455788106113400834", 1)


def recent_intent_and_syas(msg: Message, node):
    if msg.intent == UNK:
        msg.add_entities("@sys.recent_intent_and_says", msg.text)
    else:
        intent_name = msg.get_intent_name_by_id(msg.intent)
        msg.add_entities("@sys.recent_intent_and_says", intent_name)
    return
    yield None

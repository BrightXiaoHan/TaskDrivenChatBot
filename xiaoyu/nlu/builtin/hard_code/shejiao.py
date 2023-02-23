from __future__ import annotations

from typing import TYPE_CHECKING

from xiaoyu.nlu.builtin.paddle_ner import builtin_paddle_ner

if TYPE_CHECKING:
    from xiaoyu.nlu.interpreter import Message


class IntentLocationNoGuangDong(object):
    def __call__(self, msg: Message) -> None:
        builtin_paddle_ner(msg)
        if ("@sys.loc" in msg.entities or "@sys.gpe" in msg.entities) and "东莞" not in msg.text:
            msg.add_intent_ranking("1455788106113400834", 1)


shejiao_intent_location_no_guangdong = IntentLocationNoGuangDong()

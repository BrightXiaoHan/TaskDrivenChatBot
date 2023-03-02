from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from xiaoyu_interface.call import NERInputExample, NEROutputExample, ner

if TYPE_CHECKING:
    from xiaoyu.nlu.interpreter import Message


async def paddle_ner(text: str) -> Dict[str, list]:
    # TODO rpc
    ents = {}

    example = NERInputExample(text=text)
    ner_output: NEROutputExample = await ner(example)

    if "人物类_实体" in ner_output.entities:
        ents.update({"@sys.person": [item.text for item in ner_output.entities["人物类_实体"]]})

    if "世界地区类" in ner_output.entities or "世界地区类_国家" in ner_output.entities or "世界地区类_区划概念" in ner_output.entities:
        ents.update(
            {
                "@sys.location": [item.text for item in ner_output.entities.get("世界地区类", [])]
                + [item.text for item in ner_output.entities.get("世界地区类_国家", [])]
                + [item.text for item in ner_output.entities.get("世界地区类_区划概念", [])]
            }
        )

    if "世界地区类_地理概念" in ner_output.entities:
        ents.update({"@sys.gpe": [item.text for item in ner_output.entities["世界地区类_地理概念"]]})

    return ents


async def builtin_paddle_ner(msg: Message) -> None:
    entities = await paddle_ner(msg.text)
    for key, value in entities.items():
        msg.add_entities(key, value)


if __name__ == "__main__":
    while True:
        text = input("请输入待识别的文字: ")
        print(paddle_ner(text))

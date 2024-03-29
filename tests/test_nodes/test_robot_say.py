import pytest

from backend.dialogue.nodes.say import RobotSayNode
from utils.exceptions import DialogueStaticCheckException


@pytest.fixture
def config_base():
    """节点RobotSayNode的基本配置"""
    config = {
        "node_id": "节点ID",
        "node_name": "回复市政府地址",
        "node_type": "机器人说节点",
        "content": ["市政府的地址是xxx"],
        "life_cycle": 2,
        "callback_words": ["拉回对话的话术"],
    }
    return config


@pytest.fixture
def config_intent():
    """机器人说节点意图跳转配置"""
    config = {
        "node_id": "节点ID",
        "node_name": "回复市政府地址",
        "node_type": "机器人说节点",
        "life_cycle": 2,
        "callback_words": ["拉回对话的话术"],
        "branchs": [
            {
                "content": ["回复话术"],
                "conditions": [
                    [
                        {"type": "intent", "operator": "==", "value": "描述地址"},
                        {
                            "type": "entity",
                            "name": "city",
                            "operator": "!=",
                            "value": "广州",
                        },
                    ],
                    [
                        {
                            "type": "global",
                            "name": "词槽名称",
                            "operator": "==",
                            "value": "是",
                        }
                    ],
                ],
            }
        ],
    }
    return config


@pytest.fixture
def config_option():
    """机器人说节点选项跳转配置"""
    config = {
        "node_id": "节点ID",
        "node_name": "回复市政府地址",
        "node_type": "机器人说节点",
        "content": ["市政府的地址是xxx"],
        "options": ["选项名称1", "选项名称2", "选项名称3"],
        "life_cycle": 2,
        "callback_words": ["拉回对话的话术"],
    }
    return config


@pytest.mark.asyncio
async def test_base(context, msg, config_base):
    """节点RobotSayNode的测试用例"""
    node = RobotSayNode(config_base)
    msg.intent = "test_intent"
    node.add_child(node, "test_line_id", intent_id=msg.intent)
    await msg.perform_faq()

    # 应当首先返回回复内容，再返回`life_cycle`次拉回话术
    expected = (
        config_base["content"]
        + config_base["callback_words"] * config_base["life_cycle"]
    )
    expected.append(node)

    i = 0
    async for reply in node(context):
        assert reply == expected[i]
        i += 1


def test_with_intent(context, config_intent):
    """节点RobotSayNode的测试用例"""
    pass


def test_with_option(context, config_option):
    """节点RobotSayNode的测试用例"""
    pass


def test_checker(config_base, config_intent):
    """测试机器人说节点的静态检查器"""
    config_base.pop("callback_words")
    with pytest.raises(DialogueStaticCheckException) as e:
        node = RobotSayNode(config_base)
        node.static_check()
    assert e.value.key == "callback_words, life_cycle"

    config_intent.pop("branchs")
    with pytest.raises(DialogueStaticCheckException) as e:
        node = RobotSayNode(config_intent)
        node.static_check()
    assert e.value.key == "content, branchs"

import pytest



@pytest.fixture(scope="fucntion")
def config_base(config_intent):
    """节点RobotSayNode的基本配置"""
    config = {
        "node_id": "节点ID",
        "node_name": "回复市政府地址",
        "node_type": "机器人说节点",
        "content": ["市政府的地址是${市政府地址}"],
        "life_cycle": 3,
        "callback_words": ["拉回对话的话术"],
    }
    return config


@pytest.fixture(scope="function")
def config_intent():
    """机器人说节点意图跳转配置"""
    config = {
        "node_id": "节点ID",
        "node_name": "回复市政府地址",
        "node_type": "机器人说节点",
        "life_cycle": 3,
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


@pytest.fixture(scope="function")
def config_option():
    """机器人说节点选项跳转配置"""
    config = {
        "node_id": "节点ID",
        "node_name": "回复市政府地址",
        "node_type": "机器人说节点",
        "content": ["市政府的地址是${市政府地址}"],
        "options": ["选项名称1", "选项名称2", "选项名称3"],
        "life_cycle": 3,
        "callback_words": ["拉回对话的话术"],
    }
    return config


def test_base(config_base):
    """节点RobotSayNode的测试用例"""
    pass


def test_with_intent(config_intent):
    """节点RobotSayNode的测试用例"""
    pass


def test_with_option(config_option):
    """节点RobotSayNode的测试用例"""
    pass


def test_checker():
    """测试机器人说节点的静态检查器"""
    pass

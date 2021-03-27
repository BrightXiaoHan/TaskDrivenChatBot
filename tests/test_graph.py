"""
测试项目对话流程配置管理相关api
"""
import os
import json
import backend.dialogue.graph_parser as graph_parser


def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    robot_code = "_test"
    with open(os.path.join(cwd, 'assets/dialogue_graph.json')) as f:
        data_one = json.load(f)
    data_one["id"] = "test_graph_id_one"
    data_one["test_flag"] = "one"

    data_two = data_one.copy()
    data_two["id"] = "test_graph_id_two"
    data_two["test_flag"] = "two"

    data_three = data_one.copy()
    data_three["id"] = "test_graph_id_two"
    data_three["test_flag"] = "three"

    # 向该机器人添加两个版本的数据
    graph_parser.update_dialogue_graph(robot_code, "v0.1", data_one)
    graph_parser.update_dialogue_graph(robot_code, "v0.1", data_two)
    graph_parser.update_dialogue_graph(robot_code, "v0.2", data_three)

    graphs = graph_parser.get_graph_data(robot_code)
    assert graphs["test_graph_id_one"]["test_flag"] == "one"
    assert graphs["test_graph_id_two"]["test_flag"] == "three"

    graph_parser.checkout(robot_code, "v0.1")
    graphs = graph_parser.get_graph_data(robot_code)
    assert graphs["test_graph_id_two"]["test_flag"] == "two"

    graph_parser.delete_robot(robot_code)


if __name__ == '__main__':
    main()

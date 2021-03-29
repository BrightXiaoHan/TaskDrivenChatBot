import time
from itertools import chain

from backend.dialogue.context import StateTracker
from backend.dialogue import nodes
from utils.exceptions import (ConversationNotFoundException,
                              ModelBrokenException)
from utils.define import MODEL_TYPE_DIALOGUE
from config import global_config

conversation_expired_time = global_config['conversation_expired_time']

TYPE_NODE_MAPPING = {
    node.NODE_NAME: node for node in [nodes.UserInputNode,
                                      nodes.FillSlotsNode,
                                      nodes.FunctionNode,
                                      nodes.RPCNode,
                                      nodes.JudgeNode,
                                      nodes.ReplyNode,
                                      nodes.SayNode,
                                      nodes.SwitchNode]
}

__all__ = ["Agent"]


class Agent(object):
    """
    会话管理类

    Attributes:
        robot_code (str): 机器人唯一标识
        interpreter (backend.nlu.interpreter.CustormInterpreter): nlu语义理解器
        graphs (dict): 对话流程配置，key为graph的id，value为该graph的具体配置
        user_store (dict): 会话状态存储字典。key为会话id，value为 `StateTracker`对象
        graphs (dict): 机器人主导的对话流程图集合。key为graph的id，value为该graph的起始节点
        robot_ledding_graphs (dict): 用户主导的对话起始节点集合
        user_ledding_graphs (dict): 机器人主导的对话流程配置

    """

    def __init__(
        self,
        robot_code,
        interpreter,
        graphs
    ):
        self.robot_code = robot_code
        self.interpreter = interpreter
        self.graph_configs = graphs
        # save the user states in memory
        self.user_store = dict()

        self.graphs = {graph_id: self.build_graph(graph) for
                       graph_id, graph in self.graph_configs.items()}
        self.robot_ledding_graphs = {}
        self.user_ledding_graphs = {}
        self.slots_abilities = {}
        self._init_graphs()

    def _init_graphs(self):
        for graph_id, graph in self.graphs.items():
            if isinstance(graph[0], nodes.SayNode):
                self.robot_ledding_graphs[graph_id] = graph
            else:
                self.user_ledding_graphs[graph_id] = graph
            self.slots_abilities.update(self.graph_configs[graph_id]["global_slots"])

    def build_graph(self, graph):
        """
        将对话流程配置构造成节点图
        """
        nodes_mapping = {}
        for node_meta in graph["nodes"]:
            node_type = node_meta["node_type"]
            node_id = node_meta["node_id"]
            node_class = TYPE_NODE_MAPPING[node_type]
            nodes_mapping[node_id] = node_class(node_meta)

        for conn in graph["connections"]:
            source_node = nodes_mapping[conn["source_id"]]
            target_node = nodes_mapping[conn["target_id"]]
            branch_id = conn.get("branch_id", None)
            intent_id = conn.get("intent_id", None)
            source_node.add_child(target_node, branch_id, intent_id)

        start_nodes = [nodes_mapping[node_id]
                       for node_id in graph["start_nodes"]]

        # 静态验证对话流程结构
        say_node_count = 0
        input_node_count = 0
        other_count = 0

        for node in start_nodes:
            if isinstance(node, nodes.SayNode):
                say_node_count += 1
            elif isinstance(node, nodes.UserInputNode):
                input_node_count += 1
            else:
                other_count += 1

        if say_node_count + input_node_count == 0 or other_count > 0:
            raise ModelBrokenException(
                self.robot_code, graph["version"],
                MODEL_TYPE_DIALOGUE, "对话流程配置开始节点中必须是用户输入节点、机器人说节点其中之一")
        elif (say_node_count > 0 and input_node_count > 0) \
                or say_node_count > 1:
            raise ModelBrokenException(
                self.robot_code, graph["version"],
                MODEL_TYPE_DIALOGUE, "对话流程配置开始节点中配置机器人说节点时，不能存在其他节点")

        return start_nodes

    def update_dialogue_graph(self, graph):
        """
        更新Agent中的nlu解释器和对话流程配置，此操作会清空所有的缓存对话
        """
        graph_id = graph["id"]
        self.graph_configs[graph_id] = graph
        self.graphs[graph_id] = self.build_graph(graph)
        self._init_graphs()
        # 清空所有会话缓存
        self.user_store = {}

    def update_interpreter(self, interpreter):
        self.interpreter = interpreter
        # 清空所有会话的缓存
        self.user_store = {}

    def establish_connection(self, sender_id, params):
        """
        建立会话连接

        Args:
            sender_id (str) 会话id
            params (dict): 全局参数
        Returns:
            str: 小语机器人答复用户的内容
        """
        self._clear_expired_session()
        state_tracker = StateTracker(self, sender_id, params)
        self.user_store[sender_id] = state_tracker
        return state_tracker.establish_connection()

    def handle_message(
        self,
        message,
        sender_id
    ):
        """回复用户

        Args:
            message (str): 用户说话的内容
            sender_id (str): 会话id

        Returns:
            str: 小语机器人答复用户的内容
        """
        self._clear_expired_session()
        if sender_id not in self.user_store:
            raise ConversationNotFoundException(self.robot_code, sender_id)
        state_tracker = self.user_store[sender_id]
        raw_message = self.interpreter.parse(message)
        response = state_tracker.handle_message(raw_message)
        return response

    def _clear_expired_session(self):
        """清理过期的会话"""
        expired_list = []
        for uid, context in self.user_store.items():
            if time.time() - context.start_time > conversation_expired_time:
                expired_list.append(uid)

        for uid in expired_list:
            del self.user_store[uid]

    def get_latest_xiaoyu_pack(self, uid):

        if uid not in self.user_store:
            raise ConversationNotFoundException(self.robot_code, uid)
        return self.user_store.get(uid).get_latest_xiaoyu_pack()

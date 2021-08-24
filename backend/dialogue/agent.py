import time

from backend.dialogue.context import StateTracker
from backend.dialogue import nodes
from utils.exceptions import (ConversationNotFoundException,
                              DialogueStaticCheckException)
from config import global_config

conversation_expired_time = global_config['conversation_expired_time']

TYPE_NODE_MAPPING = {
    node.NODE_NAME: node
    for node in [
        nodes.FillSlotsNode, nodes.FunctionNode, nodes.RPCNode, nodes.UserInputNode,
        nodes.JudgeNode, nodes.RobotSayNode, nodes.StartNode, nodes.SwitchNode
    ]
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
    """
    def __init__(self, robot_code, interpreter, graphs):
        self.robot_code = robot_code
        self.interpreter = interpreter
        self.graph_configs = graphs
        # save the user states in memory
        self.user_store = dict()

        self.graphs = {
            graph_id: self.build_graph(graph)
            for graph_id, graph in self.graph_configs.items()
        }
        self.slots_abilities = {}
        self._init_graphs()

    def _init_graphs(self):
        internal_abilities = set()
        for graph_id in self.graphs.keys():
            self.slots_abilities.update(
                self.graph_configs[graph_id]["global_slots"])

            internal_abilities.update(
                self.graph_configs[graph_id]["global_slots"].values())

    def build_graph(self, graph):
        """
        将对话流程配置构造成节点图
        """
        nodes_mapping = {}
        for node_meta in graph["nodes"]:
            node_type = node_meta["node_type"]
            node_id = node_meta["node_id"]
            if node_type not in TYPE_NODE_MAPPING:
                raise DialogueStaticCheckException("node_type",
                                                   "没有这种类型的节点: {}".format(node_type), 
                                                   node_id)
            node_class = TYPE_NODE_MAPPING[node_type]
            nodes_mapping[node_id] = node_class(node_meta)
            # 静态检查节点
            try:
                nodes_mapping[node_id].static_check()
            except DialogueStaticCheckException as e:
                e.update_optional_params(robot_code=self.robot_code,
                                         graph_id=graph.get("id", "unknown"))
                raise e

        for conn in graph["connections"]:
            if "source_id" not in conn or "target_id" not in conn:
                raise DialogueStaticCheckException(
                    conn.get("line_id", "unkown"),
                    reason="连接线必须有source_id和target_id字段",
                    robot_code=self.robot_code,
                    graph_id=graph.get("graph_id", "unknown"),
                    node_id=conn.get("line_id", "未知（连接线没有line_id字段）"))
            source_node = nodes_mapping[conn["source_id"]]
            target_node = nodes_mapping[conn["target_id"]]
            line_id = conn["line_id"]
            branch_id = conn.get("branch_id", None)
            intent_id = conn.get("intent_id", None)
            option_id = conn.get("options", None)
            if branch_id and intent_id:
                raise DialogueStaticCheckException(
                    conn.get("line_id", "unkown"),
                    "连接线不能同时指定branch_id, intent_id参数",
                    robot_code=self.robot_code,
                    graph_id=graph.get("graph_id", "unknown"),
                    node_id=conn.get("line_id", "未知（连接线没有line_id字段）"))
            source_node.add_child(target_node, line_id, branch_id, intent_id, option_id)

        start_nodes = [
            nodes_mapping[node_id] for node_id in graph["start_nodes"]
        ]

        for node in start_nodes:
            if not isinstance(node, nodes.StartNode):
                raise DialogueStaticCheckException("node_type",
                                                   "对话流程根节点的类型必须是开始节点",
                                                   node.config.get("node_id", "未知"))
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

    def handle_message(self, message, sender_id, params={}):
        """回复用户

        Args:
            message (str): 用户说话的内容
            sender_id (str): 会话id
            params (dict): 建立连接时的参数，一般是首次发起会话时会传递此参数

        Returns:
            str: 小语机器人答复用户的内容
        """
        self._clear_expired_session()
        if sender_id not in self.user_store:
            self._clear_expired_session()
            state_tracker = StateTracker(self, sender_id, params)
            self.user_store[sender_id] = state_tracker
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

    def session_exists(self, sender_id):
        """
        判断当前会话是否存在

        Args:
            sender_id (str): 会话id
        
        Return:
            bool: 会话存在返回True，反之返回False
        """
        return sender_id in self.user_store

    def get_latest_xiaoyu_pack(self, uid):

        if uid not in self.user_store:
            raise ConversationNotFoundException(self.robot_code, uid)
        return self.user_store.get(uid).get_latest_xiaoyu_pack()


    def get_graph_meta_by_id(self, graph_id, key):
        """
        通过对话流程id获得相应对话流程的名字，如果未找到对应的id或者对应的配置中没有name字段，则返回unknown
        """
        if graph_id not in self.graph_configs or key not in self.graph_configs[graph_id]:
            return "unknown"

        return self.graph_configs[graph_id][key]
        
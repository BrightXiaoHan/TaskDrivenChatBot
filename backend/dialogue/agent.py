from backend.dialogue.context import StateTracker
from backend.dialogue import nodes
from utils.exceptions import ConversationNotFoundException

TYPE_NODE_MAPPING = {
    "用户输入节点": nodes.UserInputNode,
    "填槽节点": nodes.FillSlotsNode,
    "服务调用": nodes.FunctionNode,  # 这里比较奇怪，按文档来。函数节点为RPC，服务调用节点为调用代码
    "函数节点": nodes.RPCNode,
    "判断节点": nodes.JudgeNode,
    "回复节点": nodes.ReplyNode,
    "机器人说节点": nodes.SayNode
}

__all__ = ["Agent"]


class Agent(object):
    """
    会话管理类

    Attributes:
        robot_code (str): 机器人唯一标识
        interpreter (backend.nlu.interpreter.CustormInterpreter): nlu语义理解器
        dialogue_graph (dict): 对话流程配置
        user_store (dict): 会话状态存储字典。key为会话id，value为 `StateTracker`对象
        start_nodes (list): 对话流程图启始节点列表
    """

    def __init__(
        self,
        robot_code,
        interpreter,
        dialogue_graph
    ):
        self.robot_code = robot_code
        self.interpreter = interpreter
        self.dialogue_graph = dialogue_graph
        # save the user states in memory
        self.user_store = dict()
        self.start_nodes = self.build_graph()

    def build_graph(self):
        """
        将对话流程配置构造成节点图
        """
        nodes_mapping = {}
        for node_meta in self.dialogue_graph["nodes"]:
            node_type = node_meta["node_type"]
            node_id = node_meta["node_id"]
            node_class = TYPE_NODE_MAPPING[node_type]
            nodes_mapping[node_id] = node_class(node_meta)

        for conn in self.dialogue_graph["connections"]:
            source_node = nodes_mapping[conn["source_id"]]
            target_node = nodes_mapping[conn["target_id"]]
            branch_id = nodes_mapping.get("branch_id", None)
            intent_id = nodes_mapping.get("intent_id", None)
            source_node.add_child(target_node, branch_id, intent_id)

        start_nodes = [nodes_mapping[node_id]
                       for node_id in node_meta["start_nodes"]]
        return start_nodes

    def update(self, interpreter=None, dialogue_graph=None):
        """
        更新Agent中的nlu解释器和对话流程配置，此操作会清空所有的缓存对话
        """
        if interpreter:
            self.interpreter = interpreter
        if dialogue_graph:
            self.dialogue_graph = dialogue_graph
            self.start_nodes = self.build_graph()
        # 清空所有会话缓存
        self.user_store = {}

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
        state_tracker = self._get_user_state_tracker(sender_id)
        raw_message = self.interpreter.parse(message)
        response = state_tracker.handle_message(raw_message)
        return response

    def _get_user_state_tracker(self, sender_id):
        if sender_id not in self.user_store:
            slots = self.dialogue_graph["global_slots"]
            params = self.dialogue_graph["global_params"]
            tracker = StateTracker(
                sender_id, self.robot_code, self.start_nodes, slots, params)
            self.user_store.update({sender_id: tracker})

        return self.user_store.get(sender_id)

    def get_logger(self, uid):
        if uid not in self.user_store:
            raise ConversationNotFoundException(self.robot_code, uid)
        return self.user_store.get(uid).get_logger()

    def hang_up(self, uid):
        if uid not in self.user_store:
            raise ConversationNotFoundException(self.robot_code, uid)
        self.user_store.get(uid).hang_up()

    def get_xiaoyu_pack(self, uid):
        if uid not in self.user_store:
            raise ConversationNotFoundException(self.robot_code, uid)
        return self.user_store.get(uid).get_xiaoyu_pack()

    def get_latest_xiaoyu_pack(self, uid):

        if uid not in self.user_store:
            raise ConversationNotFoundException(self.robot_code, uid)
        return self.user_store.get(uid).get_latest_xiaoyu_pack()

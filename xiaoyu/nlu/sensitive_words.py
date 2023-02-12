import glob
import os
import re

import pypinyin

from xiaoyu.config import global_config
from xiaoyu.nlu.train import get_model_path

model_storage_folder = global_config["model_storage_folder"]

__all__ = [
    "WordsSearch",
    "get_sensitive_words_searcher",
    "save_sensitive_words_to_file",
    "load_all_sensitive_words_searcher",
]


class TrieNode:
    def __init__(self):
        self.Index = 0
        self.Index = 0
        self.Layer = 0
        self.End = False
        self.Char = ""
        self.Results = []
        self.m_values = {}
        self.Failure = None
        self.Parent = None

    def Add(self, c):
        if c in self.m_values:
            return self.m_values[c]
        node = TrieNode()
        node.Parent = self
        node.Char = c
        self.m_values[c] = node
        return node

    def SetResults(self, index):
        if not self.End:
            self.End = True
        self.Results.append(index)


class TrieNode2:
    def __init__(self):
        self.End = False
        self.Results = []
        self.m_values = {}

    def Add(self, c, node3):
        self.m_values[c] = node3

    def SetResults(self, index):
        if not self.End:
            self.End = True
        if index not in self.Results:
            self.Results.append(index)

    def HasKey(self, c):
        return c in self.m_values

    def TryGetValue(self, c):
        if c in self.m_values:
            return self.m_values[c]
        return None


class WordsSearch:
    def __init__(self):
        self._first = {}
        self._keywords = []
        self._indexs = []

    def SetKeywords(self, keywords):
        self._keywords = keywords
        self._indexs = []
        for i in range(len(keywords)):
            self._indexs.append(i)

        root = TrieNode()
        allNodeLayer = {}

        for i in range(len(self._keywords)):
            p = self._keywords[i]
            nd = root
            for j in range(len(p)):
                nd = nd.Add(pypinyin.lazy_pinyin(p[j], v_to_u=True)[0])
                if nd.Layer == 0:
                    nd.Layer = j + 1
                    if nd.Layer in allNodeLayer:
                        allNodeLayer[nd.Layer].append(nd)
                    else:
                        allNodeLayer[nd.Layer] = []
                        allNodeLayer[nd.Layer].append(nd)
            nd.SetResults(i)

        allNode = []
        allNode.append(root)
        for key in allNodeLayer.keys():
            for nd in allNodeLayer[key]:
                allNode.append(nd)
        allNodeLayer = None

        for i in range(len(allNode)):
            if i == 0:
                continue
            nd = allNode[i]
            nd.Index = i
            r = nd.Parent.Failure
            c = nd.Char
            while r is not None and c not in r.m_values:
                r = r.Failure
            if r is None:
                nd.Failure = root
            else:
                nd.Failure = r.m_values[c]
                for key2 in nd.Failure.Results:
                    nd.SetResults(key2)
        root.Failure = root

        allNode2 = []
        for i in range(len(allNode)):
            allNode2.append(TrieNode2())

        for i in range(len(allNode2)):
            oldNode = allNode[i]
            newNode = allNode2[i]

            for key in oldNode.m_values:
                index = oldNode.m_values[key].Index
                newNode.Add(key, allNode2[index])

            for index in range(len(oldNode.Results)):
                item = oldNode.Results[index]
                newNode.SetResults(item)

            oldNode = oldNode.Failure
            while oldNode != root:
                for key in oldNode.m_values:
                    if not newNode.HasKey(key):
                        index = oldNode.m_values[key].Index
                        newNode.Add(key, allNode2[index])
                for index in range(len(oldNode.Results)):
                    item = oldNode.Results[index]
                    newNode.SetResults(item)
                oldNode = oldNode.Failure
        allNode = None
        root = None

        self._first = allNode2[0]

    def FindAll(self, text, mask_char="*", strict=True):
        words = self._find_all_strictly(text)
        if not strict:
            for item in words:
                item["word"] = text[item["start"] : item["end"]]
        else:
            strict_result = []
            for item in words:
                if text[item["start"] : item["end"]] == item["word"]:
                    strict_result.append(item)
            words = strict_result

        masked_text = ""
        start = 0

        for item in sorted(words, key=lambda x: x["start"]):
            masked_text += text[start : item["start"]]
            masked_text += mask_char * len(item["word"])
            start = item["end"]

        masked_text += text[start:]

        return words, masked_text

    def _find_all_strictly(self, text):
        ptr = None
        words = []

        for index in range(len(text)):
            t = pypinyin.lazy_pinyin(text[index], v_to_u=True)[0]
            tn = None
            if ptr is None:
                tn = self._first.TryGetValue(t)
            else:
                tn = ptr.TryGetValue(t)
                if tn is None:
                    tn = self._first.TryGetValue(t)

            if tn is not None:
                if tn.End:
                    for j in range(len(tn.Results)):
                        item = tn.Results[j]
                        keyword = self._keywords[item]
                        words.append(
                            {
                                "word": keyword,
                                "end": index + 1,
                                "start": index + 1 - len(keyword),
                            }
                        )
            ptr = tn

        return words


def load_all_sensitive_words_searcher():
    searchers = {}
    all_files = glob.glob(os.path.join(model_storage_folder, "*", "sensitive_words_*.txt"))
    for file in all_files:
        robot_code = os.path.basename(os.path.dirname(file))
        label = re.match(r"sensitive_words_(.*).txt", os.path.basename(file)).group(1)
        searcher = get_sensitive_words_searcher(robot_code, label)
        if robot_code not in searchers:
            searchers[robot_code] = {}
        searchers[robot_code][label] = searcher

    return searchers


def save_sensitive_words_to_file(robot_code, words, label):
    """
    将词典保存到模型中

    Args:
        robot_code (str): 机器人代码
        words (list): 词典
        label (str): 敏感词标签
    """
    nlu_model_path = get_model_path(robot_code)
    if not os.path.exists(nlu_model_path):
        os.makedirs(nlu_model_path)
    with open(
        os.path.join(nlu_model_path, f"sensitive_words_{label}.txt"),
        "w",
        encoding="utf-8",
    ) as f:
        for word in words:
            f.write(word + "\n")


def get_sensitive_words_searcher(robot_code, label):
    """
    获取WordSearch 对象

    Args:
        robot_code (str): 机器人编码
        label (str): 敏感词组标签

    Returns:
        WordsSearch: WordsSearch 对象，每个机器人对应一个，直接从模型文件中加载
    """
    searcher = WordsSearch()
    nlu_model_path = get_model_path(robot_code)
    if not os.path.exists(nlu_model_path):
        return searcher

    words = []
    with open(
        os.path.join(nlu_model_path, f"sensitive_words_{label}.txt"),
        "r",
        encoding="utf-8",
    ) as f:
        for word in f:
            words.append(word.strip())
    searcher.SetKeywords(words)
    return searcher

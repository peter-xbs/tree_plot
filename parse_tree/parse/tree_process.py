# -*- coding:utf-8 -*-
from tornado.log import access_log
from parse_tree.parse.entity_process import EntityProcess
from parse_tree.parse.fsm_process import FsmProcess, FsmModel


class TreeProcess(object):

    def __init__(self, entity_relationship, tree):
        self.entity_list = {}  # 存储一棵树生成的实体,key:id,value:实体对象
        self.entity_relationship = entity_relationship  # 存储多棵树实体关系的对象
        self.tree = tree  # 树

    def process(self):
        """
        依存关系树解析流程：
        :return:
        """
        try:
            # 1、解析每棵树
            self.parse_tree(self.tree)
            # 对实体排序
            sorted(self.entity_list.items(), key=lambda start: start[1].get('start_index'))
            return self.entity_list.values()
        except Exception as ex:
            access_log.error('解析树出现异常')

    def parse_tree(self, tree):
        """
        解析每棵树
        :return:
        """
        if tree is None:
            return

        # 中序遍历每棵树
        result = []  # 中序遍历结果
        tree.in_order_traverse(tree.root, result)

        # 生成实体列表
        ep = EntityProcess(self.entity_list, self.entity_relationship)
        for token in result:
            ep.token_entity_process(token)

        # 依赖于act对的间接关系建立
        model = FsmModel()
        try:
            FsmProcess.build_relationship(tree, self.entity_list, self.entity_relationship, model)
        except Exception as ex:
            print(ex)

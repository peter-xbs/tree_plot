# -*- coding:utf-8 -*-
from tornado.log import access_log
from kernel_nlp.kernel_nlp_config import KernelNLPConfig
from kernel_nlp.entity_process.fill_attribute_optimize import FillAttribute as fab
from kernel_nlp.entity_process.entity_process import EntityProcess as ep


class EntityProcess(object):

    def __init__(self, entity_list, entity_relationship):
        self.entity_list = entity_list  # 一棵树实体列表
        self.entity_relationship = entity_relationship  # 全局实体关系
        self.not_spec_proc_type = {"adj", "pos"}

    def token_entity_process(self, token):
        """
        依据树节点生成实体对象并填充属性建立关系：
            1、建实体对象、直接关系的属性、关系建立
            2、总结的依存树规则修正实体列表及关系
        :return:
        """
        try:
            # 1、建实体对象、直接关系的属性、关系建立
            self.generate_entity_atb_relation(token)

            # 2、总结的依存树规则修正实体列表及关系
            #
            return
        except Exception as ex:
            access_log.error('生成实体列表出现问题')

    def generate_entity_atb_relation(self, token):
        """
        操作树节点：是目标实体，生成实体对象，更新token，属性填充，关系建立
        :param token:
        :return:
        """
        if token is None or token.word == 'root':
            return

        # 是目标实体，生成实体对象，更新token，属性填充，关系建立
        if token.tag in KernelNLPConfig.tag_label_list:
            entity_obj = self.set_target_entity_obj(token)
            if entity_obj:
                token.entity_id = entity_obj.get('id')  # 更新token对应的实体id
                self.fill_atb_in_direct_relation(token, entity_obj)  # 填充属性
                self.fill_atb_copy_parent_act_atb(token, entity_obj)  # 属性补充，将act属性copy到其子孩子实体上
                self.fill_atb_in_juxt(token, entity_obj)  # 若当前为并列实体修正属性
                self.entity_list[token.entity_id] = entity_obj  # 当前实体添加到实体字典
                self.build_relation_in_direct_relation(token, entity_obj)  # 建立关系
                self.amend_relation_in_juxt(token, entity_obj)  # 并列修正关系
                self.build_indirect_rel_by_act(token, entity_obj)

    @staticmethod
    def set_target_entity_obj(token):
        """
        节点如果为目标实体则生成目标实体对象
        :return:
        """
        tag_entity = None
        if token.tag in KernelNLPConfig.tag_label_list:  # 属于目标实体
            value = token.word
            father_value = value
            tag_entity = KernelNLPConfig.make_tag_entity(token.tag)
            tag_entity['original'] = value
            tag_entity['father_value'] = father_value
            tag_entity['start_index'] = token.offset[0]
            tag_entity['end_index'] = token.offset[1]

        return tag_entity

    @staticmethod
    def fill_atb_in_direct_relation(token, entity_obj):
        """
        填充直接属性，仅选择与当前节点有直接关系的子节点属性填充
        :return:
        """
        def get_dat_jutx(token_):
            """
            处理属性时，日期需特殊处理，因为日期不作结构体化，依存于当前日期节点的日期必定和当前
            日期节点并列，回收起来一块填充至当期日期节点所依存的目标实体节点
            """
            jutx_dat_tokens = []
            if not token_.tag == 'dat':
                return
            token_children = token_.left_child + token_.right_child
            for token_child in token_children:
                if token_child.tag == "dat":
                    jutx_dat_tokens.append(token_child)

            return jutx_dat_tokens

        attribute = KernelNLPConfig.atb_label_list

        token_children = token.left_child + token.right_child
        for node in token_children:
            if node.tag in attribute:
                fab.fill_atb_for_single_tag(entity_obj, node.tag, node.word)
                if node.tag == "dat":
                    jutx_dat_nodes = get_dat_jutx(node)
                    if not jutx_dat_nodes:
                        continue
                    for jutx_node in jutx_dat_nodes:
                        fab.fill_atb_for_single_tag(entity_obj, jutx_node.tag, jutx_node.word)

    def fill_atb_in_juxt(self, token, entity_obj):
        """
        并列节点处理：若当前节点为并列实体，则拷贝父节点实体的属性（仅拷贝当前节点不存在的父节点属性值）
        :param token:
        :param entity_obj:
        :return:
        """
        if token.parent is None or token.parent.word == 'root' or token.parent.entity_id is None:
            return

        if token.parent.tag == token.tag:  # 并列节点
            parent_entity = self.entity_list.get(token.parent.entity_id)
            ep._amend_attribute(parent_entity, entity_obj)

    def fill_atb_copy_parent_act_atb(self, token, entity_obj):
        """
        实体属性补充：act实体的属性copy到依存act的子孩子的目标实体上(除pos\adj)
        :return:
        """
        if token.tag in self.not_spec_proc_type:
            return

        if token.parent is None or token.parent.entity_id is None or token.parent.tag != 'act':
            return

        parent_entity = self.entity_list.get(token.parent.entity_id)
        EntityProcess.copy_atb_first_to_second_entity(parent_entity, entity_obj)  # act属性copy

    @staticmethod
    def copy_atb_first_to_second_entity(first_entity, second_entity):
        """
        使用前一个实体修正后一个实体的属性（允许两实体标签不同），即将前一个实体属性copy到后一个实体上，不管对应的属性标签是否存在值
        :param first_entity:
        :param second_entity:
        :return:
        """

        if not (first_entity and second_entity):
            return

        first_atb_list = first_entity.get('attribute')
        second_atb_list = second_entity.get('attribute')
        for f_label, f_value in first_atb_list.items():
            if f_label in second_atb_list and f_value:
                second_atb_list[f_label].extend(f_value)

    def build_relation_in_direct_relation(self, token, entity_obj):
        """
        建立直接关系，仅选择与当前节点有直接关系的父节点、左子节点实体对象建立关系
        :param token:
        :param entity_obj:
        :return:
        """
        def direct_rel_process(par_ent_obj, child_ent_obj, token_, et_relship, not_spec_proc_type):
            """并列首元素操作及建立实体间直接关系"""
            par_label = par_ent_obj.get("label")
            child_label, child_ent_id = child_ent_obj.get("label"), child_ent_obj.get("id")
            if child_label == par_label and par_label not in not_spec_proc_type:
                token_.jutx_child.append(child_ent_id)
            else:
                relation_type = KernelNLPConfig.get_entity_relation_type(par_label, child_label)
                if relation_type:
                    et_relship.add_entity_relationship(par_ent_obj, child_ent_obj, relation_type)

        # 与直接左孩子建立关系
        if token.left_child:
            for node in token.left_child:
                if node.entity_id is None:
                    continue
                left_entity = self.entity_list.get(node.entity_id)
                direct_rel_process(entity_obj, left_entity, token, self.entity_relationship,
                                   self.not_spec_proc_type)

        # 与直接父节点建立关系
        if token.parent is None:
            return
        if not token.parent.entity_id:
            return
        # 根据节点entity_id找对应的实体对象
        parent_entity = self.entity_list.get(token.parent.entity_id)

        direct_rel_process(parent_entity, entity_obj, token.parent, self.entity_relationship,
                           self.not_spec_proc_type)

    def amend_relation_in_juxt(self, token, entity_obj):
        """
        补充并列关系，并列内所有元素打包与其他建立关系
        :return:
        """
        def create_relation(all_relation_entity, is_juxt=True):
            """建立关系：1、与所有实体建立关系；2、与所有实体id对应的实体建立关系"""
            if is_juxt:
                for entity in all_relation_entity:
                    entity_label = entity.get('label')
                    if entity_label in self.not_spec_proc_type:
                        continue
                    relation_type = KernelNLPConfig.get_entity_relation_type(entity_label, token.tag)
                    if relation_type:
                        self.entity_relationship.add_entity_relationship(entity, entity_obj, relation_type)
            else:
                for entity_id in all_relation_entity:
                    cur_juxt_entity = self.entity_list.get(entity_id)
                    cur_juxt_entity_label = cur_juxt_entity.get('label')
                    relation_type = KernelNLPConfig.get_entity_relation_type(cur_juxt_entity_label, token.tag)
                    if relation_type:
                        self.entity_relationship.add_entity_relationship(cur_juxt_entity, entity_obj, relation_type)

        # 检查left_child
        if token.left_child:
            for left_token in token.left_child:
                if left_token.tag in self.not_spec_proc_type:
                    continue
                if not left_token.entity_id or not left_token.jutx_child:
                    continue
                left_token_entity = self.entity_list.get(left_token.entity_id)
                is_exist_relation = self.entity_relationship.has_relationship(left_token_entity, entity_obj)
                if is_exist_relation:
                    create_relation(left_token.jutx_child, is_juxt=False)

        # 检查parent
        if token.parent is None:
            return
        if not token.parent.entity_id or token.parent.tag in self.not_spec_proc_type:
            return
        parent_entity = self.entity_list.get(token.parent.entity_id)

        if token.tag == token.parent.tag:  # 当前token与parent是并列
            # 获取与parent有关系的实体与当前token实体建立关系
            all_parent_relation_entity = self.entity_relationship.get_related_entities(parent_entity)
            create_relation(all_parent_relation_entity, is_juxt=True)
        else:  # 当前token与parent不是并列
            is_exist_relation = self.entity_relationship.has_relationship(parent_entity, entity_obj)  # 判断当前实体与父实体是否存在关系
            if is_exist_relation:
                # 若父节点是并列元素，获取parent实体的并列实体列表
                if token.parent.jutx_child:
                    create_relation(token.parent.jutx_child, is_juxt=False)

    def build_indirect_rel_by_act(self, token, entity_obj):
        """
        通过总结规则，利用act实体的传导性能建立间接关系
        :param token:
        :param entity_obj:
        :return:
        """
        def build_relship(prev_ent_obj, cur_ent_obj, et_relship):
            prev_label, cur_label = prev_ent_obj.get("label"), cur_ent_obj.get("label")
            rel_type = KernelNLPConfig.get_entity_relation_type(prev_label, cur_label)
            if rel_type:
                et_relship.add_entity_relationship(prev_ent_obj, cur_ent_obj, rel_type)

        if token.tag in self.not_spec_proc_type:  # 当前实体为adj/pos时，不作后续处理
            return

        # 当前节点左孩子节点包含act的情况
        left_children = token.left_child
        for left_child_token in left_children:
            if not left_child_token.tag == 'act':
                continue
            cc_tokens = left_child_token.left_child + left_child_token.right_child
            for cc_token in cc_tokens:
                if not cc_token.tag in KernelNLPConfig.tag_label_list:
                    continue
                cc_ent_obj = self.entity_list.get(cc_token.entity_id)
                build_relship(entity_obj, cc_ent_obj, self.entity_relationship)
                if not cc_token.jutx_child:
                    continue
                for cc_jutx_child_id in cc_token.jutx_child:
                    cc_jutx_ent_obj = self.entity_list.get(cc_jutx_child_id)
                    build_relship(entity_obj, cc_jutx_ent_obj, self.entity_relationship)

        # 当前节点父节点为act的情况
        if token.parent is None:
            return
        if token.parent.tag == 'act':
            pp_token = token.parent.parent
            if pp_token is None:
                return

            if pp_token.tag in KernelNLPConfig.tag_label_list and pp_token.entity_id is not None:
                pp_ent_obj = self.entity_list.get(pp_token.entity_id)
                build_relship(pp_ent_obj, entity_obj, self.entity_relationship)
                if not pp_token.jutx_child:
                    return
                for pp_jutx_child_id in pp_token.jutx_child:
                    pp_jutx_child_ent_obj = self.entity_list.get(pp_jutx_child_id)
                    build_relship(pp_jutx_child_ent_obj, entity_obj, self.entity_relationship)

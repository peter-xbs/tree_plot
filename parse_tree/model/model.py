# -*- coding:utf-8 -*-
from tornado.log import access_log

class Token(object):
    def __init__(self, word, token_id, tag, head_id, offset):
        self.word = str(word).lower()
        self.token_id = str(int(token_id))
        self.tag = str(tag).lower()
        self.head_id = str(head_id).lower()
        self.offset = offset
        self.left_child = []
        self.right_child = []
        self.parent = None
        self.entity_id = None
        self.jutx_child = []

    def __str__(self):
        return '#'.join([self.word, str(self.token_id), self.tag, str(self.head_id).strip(),
                         '_'.join([str(self.offset[0]), str(self.offset[1])])])


class Sentence(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.attribute_set = {'dat', 'tim', 'neg', 'rv', 'pob', 'col', 'cmp', 'x'}

    def reset_token_id_and_head_id(self):
        old_2_new_id_map = {token.token_id: new_id for new_id, token in enumerate(self.tokens)}
        for new_id, token in enumerate(self.tokens):
            token.token_id = new_id
            old_head_id = token.head_id
            token.head_id = old_2_new_id_map.get(old_head_id, '-1')  # todo 暂时调整为-1，后续再商讨

    def format_head_id(self):
        tokens_len = len(self.tokens)
        for i in range(tokens_len):
            tmp_token = self.tokens[i]
            if tmp_token.tag == 'x':  # 可能导致成环，又由于数据单头，成环部分会从树中丢失，暂不考虑
                tmp_token.head_id = str(i - 1)
            if tmp_token.head_id == '-2':
                set_flag = False
                forward = i - 1
                backward = i + 1
                while forward > -1 or backward < tokens_len:
                    if forward > -1:
                        forward_search_token = self.tokens[forward]
                        if forward_search_token.tag in self.attribute_set:
                            tmp_token.head_id = str(forward)
                            set_flag = True
                            break
                        else:
                            forward -= 1
                    if backward < tokens_len:
                        backward_search_token = self.tokens[backward]
                        if backward_search_token.tag in self.attribute_set:
                            tmp_token.head_id = str(backward)
                            set_flag = True
                            break
                        else:
                            backward += 1
                if not set_flag:
                    tmp_token.head_id = str(-1)

    def __len__(self):
        return len(self.tokens)

    def __getitem__(self, item):
        return self.tokens[item]

    def __str__(self):
        return '{}\n'.format('\n'.join([str(token) for token in self.tokens]))


class Tree(object):
    def __init__(self, sentence):
        self.sentence = sentence
        self.root = Token('ROOT', '-1', 'ROOT', '-1', (0, 0))
        self._build_tree()
        # self._build_bidirectional_tree(self.root, None)
        
    def __getitem__(self, item):
        return self.sentence[item]

    def __len__(self):
        return len(self.sentence)

    def _build_tree(self):
        for indx, token in enumerate(self.sentence):
            try:
                head_id = int(token.head_id)
            except Exception as ex:
                access_log.warning("提供了错误的数据格式，请检查第{}行数据...".format(indx))
                continue
            if head_id == -1:
                self.root.right_child.append(token)
            elif indx > head_id:
                token.parent = self.sentence[head_id]
                self.sentence[head_id].right_child.append(token)
            else:
                token.parent = self.sentence[head_id]
                self.sentence[head_id].left_child.append(token)

    def get_depth(self):
        """
            method of getting depth of BiTree
            求二叉树的深度或者高度的非递归实现，本质上可以通过层次遍历实现，方法如下：
                1. 如果树为空，返回0 。
                2. 从根结点开始，将根结点拉入列。
                3. 当列非空，记当前队列元素数（上一层节点数）。将上层节点依次出队，如果左右结点存在，依次入队。直至上层节点出队完成，深度加一。继续第三步，直至队列完全为空。
        """
        if self.root is None:
            return 0
        else:
            node_queue = list()
            node_queue.append(self.root)
            depth = 0
            while len(node_queue):
                q_len = len(node_queue)
                while q_len:
                    q_node = node_queue.pop(0)
                    q_len -= 1
                    if isinstance(q_node, Token):
                        if q_node.left_child:
                            node_queue.append(q_node.left_child)
                        if q_node.right_child:
                            node_queue.append(q_node.right_child)
                    elif isinstance(q_node, list):
                        for t_node in q_node:
                            if t_node.left_child:
                                node_queue.append(t_node.left_child)
                            if t_node.right_child:
                                node_queue.append(t_node.right_child)
                depth += 1
            return depth

    def _build_bidirectional_tree(self, roots, parent):
        """建立双向树"""
        if roots is None:
            return
        if isinstance(roots, list):
            for root in roots:
                if parent is not None:
                    root.parent = parent
                self._build_bidirectional_tree(root.left_child, root)
                self._build_bidirectional_tree(root.right_child, root)
        else:
            if parent is not None:
                roots.parent = parent
            self._build_bidirectional_tree(roots.left_child, roots)
            self._build_bidirectional_tree(roots.right_child, roots)

    def in_order_traverse(self, roots, result):
        """中序遍历树"""
        if roots is None:
            return []

        if isinstance(roots, list):
            for root in roots:
                self.in_order_traverse(root.left_child, result)
                result.append(root)
                self.in_order_traverse(root.right_child, result)
        else:
            self.in_order_traverse(roots.left_child, result)
            result.append(roots)
            self.in_order_traverse(roots.right_child, result)

    def get_struct_info(self):
        """获得当前树的层次结构信息，包括深度及每一层的节点数目，以dict形式存储"""
        stack = list()
        struct_dic = dict()
        depth =0
        if self.root is None:
            return struct_dic

        stack.append(self.root)
        while stack:
            stack_length = len(stack)
            struct_dic[depth] = stack_length
            while stack_length:
                stack_length -= 1
                current = stack.pop(0)
                if current.left_child:
                    stack.extend(current.left_child)
                if current.right_child:
                    stack.extend(current.right_child)
            depth += 1
        return struct_dic

    @staticmethod
    def get_content(node):
        return '|'.join([str(node.token_id), node.word, node.tag])


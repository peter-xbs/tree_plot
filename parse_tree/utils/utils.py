# -*- coding:utf-8 -*-
import os
import xlrd
from tornado.log import access_log
from parse_tree.model.model import Token, Sentence, Tree
import xlwt
from kernel_nlp.kernel_nlp_config import KernelNLPConfig
from kernel_nlp.util import KernelNlpUtil as knu

class TreeProducer(object):
    """
    根据输入数据生成依存树，现阶段主要使用read_excel方法直接读取标注excel文件测试流程，后期根据输入数据格式再作调整
    """
    @classmethod
    def read_excel(cls, file_path):
        # sentences列表主要放置校正索引后的实体识别结果
        sentences = []
        # tree_list列表放置sentences列表中实体构建出来的依存树
        tree_list = []
        # sentences_value_list内每个元素为1个列表，每个句子的实体识别结果分别存储其内
        sentences_value_list = []
        if os.path.exists(file_path):
            excel_data = xlrd.open_workbook(file_path)
            for sheet in excel_data.sheets():
                n_rows = sheet.nrows
                tokens = []
                # 定义初始偏移量
                start, end = 0, 0
                sentence_value_list = []
                for row in range(n_rows):
                    line_data = sheet.row_values(row)
                    word = str(line_data[0])
                    sentence_value_list.append(word)
                    token_id = line_data[1]
                    tag = line_data[2]
                    head_id = line_data[3]
                    end = start + len(word)
                    offset = (start, end)
                    start = end
                    if isinstance(token_id, float):
                        token_id = str(int(token_id))
                    if isinstance(head_id, float):
                        head_id = str(int(head_id))

                    if word:
                        if tag != 'unk':
                            tokens.append(Token(word, token_id, tag, head_id, offset))
                    else:
                        start, end = 0, 0  # 下一句话，从头初始化word偏移量
                        sentences_value_list.append(sentence_value_list)  # 每个句子的实体识别结果分别存储
                        sentence_value_list = []
                        sentence, sent_tree = cls.read_tokens(tokens)
                        sentences.append(sentence)
                        tree_list.append(sent_tree)
                        tokens = []
                if tokens:
                    sentence, sent_tree = cls.read_tokens(tokens)
                    sentences.append(sentence)
                    tree_list.append(sent_tree)
        else:
            print('{} is not exists!'.format(file_path))

        return sentences, tree_list, sentences_value_list

    @classmethod
    def read_text(cls, file_path):
        """根据输入文本文档数据生成依存树"""
        # sentences列表主要放置校正索引后的实体识别结果
        sentences = []
        # tree_list列表放置sentences列表中实体构建出来的依存树
        tree_list = []
        # sentences_value_list内每个元素为1个列表，每个句子的实体识别结果分别存储其内
        sentences_value_list = []
        with open(file_path, encoding='utf-8') as f:
            # 定义初始偏移量
            start, end = 0, 0
            # 定义tokens列表
            tokens = []
            # sentence_value_list，用于回收实体内容，用于拼装整段文本
            sentence_value_list = []
            for line_no, line in enumerate(f):
                line = line.strip()
                if not line:  # 遇到下一句
                    start, end = 0, 0  # 下一句话，从头初始化word偏移量
                    if sentence_value_list:
                        sentences_value_list.append(sentence_value_list)  # 每个句子的实体识别结果分别存储
                        sentence_value_list = []
                    if tokens:
                        sentence, sent_tree = cls.read_tokens(tokens)
                        sentences.append(sentence)
                        tree_list.append(sent_tree)
                        tokens = []
                    continue

                line_list = line.split('\t')
                if len(line_list) < 4:
                    access_log.warning("第{}行输入数据格式不正确，请检查...".format(line_no))
                    continue

                # 格式校正
                word, token_id, tag, head_id = line_list[0:4]
                word, tag = str(word).strip(), str(tag).strip()
                sentence_value_list.append(word)
                if isinstance(token_id, float):
                    token_id = int(token_id)
                if isinstance(head_id, float):
                    head_id = int(head_id)
                token_id, head_id = str(token_id).strip(), str(head_id).strip()

                # 计算每个实体的偏移量
                end = start + len(word)
                offset = (start, end)
                start = end

                # 去除未识别实体(unk)
                if tag == 'unk':
                    continue

                # 实例化为token对象并添加到tokens列表中
                tokens.append(Token(word, token_id, tag, head_id, offset))

            # 最后一句话的处理
            if sentence_value_list:
                sentences_value_list.append(sentence_value_list)
            if tokens:
                sentence, sent_tree = cls.read_tokens(tokens)
                sentences.append(sentence)
                tree_list.append(sent_tree)

        return sentences, tree_list, sentences_value_list

    @staticmethod
    def request_dependence(req_data):
        """
        请求依存树模型
        :param req_data:
        :return:
        """
        ip = KernelNLPConfig.dependence_ip
        port = KernelNLPConfig.dependence_port
        server_path = KernelNLPConfig.dependence_server_path

        data = knu.outer_server_request(req_data, ip, port, server_path)
        depend_rs = data.get('result', [])

        if not depend_rs:  # 依存返回为空
            return []

        return depend_rs


    @classmethod
    def generate_depend_tree_by_ner(cls, ner_list, req_type='list'):
        """
        根据ner生成依存树
        :param ner_list:
        :return:
        """
        if req_type == 'list':
            req_data = {'req_type': "et_list", "et_list": ner_list}
        elif req_type == 'sentence':
            req_data = {'req_type': "sentence", "sentence": ner_list}
        depend_rs_list = TreeProducer.request_dependence(req_data)

        # 定义初始偏移量
        start, end = 0, 0
        # 定义tokens列表
        tokens = []
        # sentence_value_list，用于回收实体内容，用于拼装整段文本
        sentence, sent_tree = None, None
        # 提取ner列表中所有实体
        sentence_value_list = [str(ner[0]).strip() for ner in ner_list]
        for line_list in depend_rs_list:
            word, token_id, tag, head_id = line_list[0:4]
            word, tag = str(word).strip(), str(tag).strip()
            # sentence_value_list.append(word)
            if isinstance(token_id, float):
                token_id = int(token_id)
            if isinstance(head_id, float):
                head_id = int(head_id)
            token_id, head_id = str(token_id).strip(), str(head_id).strip()

            # 计算每个实体的偏移量
            end = start + len(word)
            offset = (start, end)
            start = end

            # 去除未识别实体(unk)
            if tag == 'unk':
                continue

            # 实例化为token对象并添加到tokens列表中
            tokens.append(Token(word, token_id, tag, head_id, offset))

        if tokens:
            sentence, sent_tree = cls.read_tokens(tokens)

        return sentence, sent_tree, sentence_value_list

    @classmethod
    def read_tokens(cls, tokens):
        sentence = Sentence(tokens)
        sentence.reset_token_id_and_head_id()
        sentence.format_head_id()
        tree = Tree(sentence)
        return sentence, tree

    @classmethod
    def save_sentences(cls, file_path, data):
        excel_writer = xlwt.Workbook()
        sheet = excel_writer.add_sheet('sheet1')
        sentences_len = len(data)
        cur_row = 0
        for sentence in range(sentences_len):
            for token in range(len(data[sentence])):
                line = str(data[sentence][token]).strip()
                items = []
                if line:
                    items = line.split('#')
                if items:
                    for col in range(len(items)):
                        sheet.write(cur_row, col, items[col])
                cur_row += 1

            for col in range(4):
                sheet.write(cur_row, col, '')
            cur_row += 1

        excel_writer.save(file_path)


if __name__ == '__main__':
    pass

# _*_ coding:utf-8 _*_

import xlwt
import os
from collections import defaultdict

head_line = '表名@字段名@句子文本@原始实体值@标准化后的实体值@父类实体原始值@是否是粗粒度实体@实体类别@sublabel@疾病诊断分类(CLA)' \
            '@颜色(COL)@日期(DAT)@否定词(NEG)@可能性描述词(POB)@方位词(POS)@修饰词(ADJ)@时间(TIM)@通用单位(UNI)@吸烟量(SMK_AMT)' \
            '@饮酒量(drk_amt)@长度(LEN)@面积大小(SIZE)@年龄(AGE)@用药剂量(DSG)@频率(FEQ)@重量(WEIGHT)@体积(VLM)@血压值(BLOOD)' \
            '@温度值(TEMPERATURE)@比较属性(CMP)@疾病后缀词(DS)@实体关系'
# TODO NLP与依存结果对比，部分数据不需要
head_line = '句子文本@原始实体值@实体类别@疾病诊断分类(CLA)' \
            '@颜色(COL)@日期(DAT)@否定词(NEG)@可能性描述词(POB)@方位词(POS)@修饰词(ADJ)@时间(TIM)@通用单位(UNI)@吸烟量(SMK_AMT)' \
            '@饮酒量(drk_amt)@长度(LEN)@面积大小(SIZE)@年龄(AGE)@用药剂量(DSG)@频率(FEQ)@重量(WEIGHT)@体积(VLM)@血压值(BLOOD)' \
            '@温度值(TEMPERATURE)@比较属性(CMP)@疾病后缀词(DS)@实体关系'

class Output2Excl(object):
    """将依存树解析结果输出到excel进行可视化"""
    @classmethod
    def process(cls, file, total_ent_list, sent_list, entity_relationship):
        total_et = dict()
        for entity_list in total_ent_list:
            et_index = 0
            for entity in entity_list:
                et_id = entity['id']
                total_et[et_id] = entity
                entity['original'] = ''.join(['[', str(et_index), ']', entity['original']])
                et_index += 1

        et_rel = defaultdict(dict)
        all_et_relship = entity_relationship.get_all_relationship()
        et_relship = all_et_relship[0]
        for s_et_rel in et_relship:
            f_id = s_et_rel['first_id']
            s_id = s_et_rel['second_id']
            rel_type = s_et_rel['relation']

            et_rel[f_id][s_id] = rel_type
            et_rel[s_id][f_id] = rel_type

        sentence_entity_list_obj = zip(total_ent_list, sent_list)
        Output2Excl.save_result(file, sentence_entity_list_obj, total_et, et_rel)


    @classmethod
    def save_result(cls, file, sentence_entity_list_obj, total_et_data, rel_data):
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet('sheet 1')
        cls.write_head(sheet)

        line_no = 1
        for entity_list, sentence_value in sentence_entity_list_obj:
            try:
                if len(entity_list):
                    for et in entity_list:
                        tmp_et = EntityStructure()
                        tmp_et.set_value(et)
                        tmp_et.set_rel_value(total_et_data, rel_data)

                        cls.save_rs(sheet, '--', '--', sentence_value, tmp_et, line_no)
                        line_no += 1
                    line_no += 1
            except Exception as ex:
                print('处理字段时出现异常，就诊数据路径'.format())
                print(ex.with_traceback())

        wbk.save(os.path.join(file + '.xls'))
    @classmethod
    def write_head(cls, sheet):
        elements = head_line.split('@')
        for ele_index, ele in enumerate(elements):
            sheet.write(0, ele_index, ele)

    @classmethod
    def save_rs(cls, sheet, table_name, column_name, sentence, et, line_no):
        # sheet.write(line_no, 0, table_name)  # TODO NLP与依存结果对比，部分数据不需要
        # sheet.write(line_no, 1, column_name)  # TODO NLP与依存结果对比，部分数据不需要
        # sheet.write(line_no, 2, sentence)  # TODO NLP与依存结果对比，部分数据不需要

        sheet.write(line_no, 0, sentence)

        et_value = et.get_rs()
        et_values = et_value.split('@')
        for ele_index, ele in enumerate(et_values):
            sheet.write(line_no, 1 + ele_index, ele)


class EntityStructure(object):
    def __init__(self):
        self.id = ''
        self.original_value = ''
        # self.normalized_value = ''  # TODO NLP与依存结果对比，部分数据不需要
        # self.father_value = ''  # TODO NLP与依存结果对比，部分数据不需要
        # self.is_big = '是'  # TODO NLP与依存结果对比，部分数据不需要
        self.label = ''
        # self.sub_label = ''  # TODO NLP与依存结果对比，部分数据不需要
        self.cla = ''
        self.col = ''
        self.dat = ''
        self.neg = ''
        self.pob = ''
        self.pos = ''
        self.adj = ''
        self.tim = ''
        self.uni = ''
        self.smk_amt = ''
        self.drk_amt = ''
        self.len = ''
        self.size = ''
        self.age = ''
        self.dsg = ''
        self.feq = ''
        self.weight = ''
        self.vlm = ''
        self.blood = ''
        self.temperature = ''
        self.cmp = ''
        self.ds = ''
        self.relation = []

    def set_value(self, et):
        self.id = et['id']
        self.original_value = et['original']
        # self.normalized_value = et['normalized_value']  # TODO NLP与依存结果对比，部分数据不需要
        # self.father_value = et['father_value']  # TODO NLP与依存结果对比，部分数据不需要

        original_value = self.original_value.split(']')[-1]
        # if self.father_value != original_value:  # TODO NLP与依存结果对比，部分数据不需要
        #     self.is_big = '否'

        self.label = et['label']
        # self.sub_label = et['sub_label']  # TODO NLP与依存结果对比，部分数据不需要

        attributes = et['attribute']
        for k, v in attributes.items():
            if 'cla' == k:
                self.cla = v
            elif 'col' == k:
                self.col = v
            elif 'dat' == k:
                self.dat = v
            elif 'neg' == k:
                self.neg = v
            elif 'pob' == k:
                self.pob = v
            elif 'pos' == k:
                self.pos = v
            elif 'adj' == k:
                self.adj = v
            elif 'tim' == k:
                self.tim = v
            elif 'uni' == k:
                self.uni = v
            elif 'smk_amt' == k:
                self.smk_amt = v
            elif 'drk_amt' == k:
                self.drk_amt = v
            elif 'len' == k:
                self.len = v
            elif 'size' == k:
                self.size = v
            elif 'age' == k:
                self.age = v
            elif 'dsg' == k:
                self.dsg = v
            elif 'feq' == k:
                self.feq = v
            elif 'weight' == k:
                self.weight = v
            elif 'vlm' == k:
                self.vlm = v
            elif 'blood' == k:
                self.blood = v
            elif 'temperature' == k:
                self.temperature = v
            elif 'cmp' == k:
                self.cmp = v
            elif 'ds' == k:
                self.ds = v

    def set_rel_value(self, total_et, et_rel):
        tmp_relation = et_rel[self.id]
        if not tmp_relation:
            return

        for k, rel_type in tmp_relation.items():
            tmp_et = total_et[k]
            tmp_original_value = tmp_et['original']
            self.relation.append((tmp_original_value, rel_type))

    def get_rs(self):
        tmp_rs = list()
        tmp_rs.append(self.original_value)
        # tmp_rs.append(self.normalized_value)  # TODO NLP与依存结果对比，部分数据不需要
        # tmp_rs.append(self.father_value)  # TODO NLP与依存结果对比，部分数据不需要
        # tmp_rs.append(self.is_big)  # TODO NLP与依存结果对比，部分数据不需要
        tmp_rs.append(self.label)
        # tmp_rs.append(self.sub_label)  # TODO NLP与依存结果对比，部分数据不需要
        tmp_rs.append(';'.join(self.cla))
        tmp_rs.append(';'.join(self.col))
        tmp_rs.append(';'.join(self.dat))
        tmp_rs.append(';'.join(self.neg))
        tmp_rs.append(';'.join(self.pob))
        tmp_rs.append(';'.join(self.pos))
        tmp_rs.append(';'.join(self.adj))
        tmp_rs.append(';'.join([str(s_ele) for s_ele in self.tim]))
        tmp_rs.append(';'.join(self.uni))
        tmp_rs.append(';'.join(self.smk_amt))
        tmp_rs.append(';'.join(self.drk_amt))
        tmp_rs.append(';'.join(self.len))
        tmp_rs.append(';'.join(self.size))
        tmp_rs.append(';'.join(self.age))
        tmp_rs.append(';'.join(self.dsg))
        tmp_rs.append(';'.join(self.feq))
        tmp_rs.append(';'.join(self.weight))
        tmp_rs.append(';'.join(self.vlm))
        tmp_rs.append(';'.join(self.blood))
        tmp_rs.append(';'.join(self.temperature))
        tmp_rs.append(';'.join(self.cmp))
        tmp_rs.append(';'.join(self.ds))

        rel_rs = []
        for v, t in self.relation:
            # TODO NLP与依存结果对比，部分数据不需要
            # rel_rs.append(v + '_' + t)
            start = v.find('[')
            end = v.find(']')
            t_v = v[start+1:end]
            rel_rs.append(t_v)
        tmp_rs.append(';'.join(rel_rs))
        return '@'.join(tmp_rs)

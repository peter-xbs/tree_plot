# _*_ coding:utf-8 _*_

import threading
from transitions import Machine
from kernel_nlp.kernel_nlp_config import KernelNLPConfig


class FsmCfg:
    states = ["start", "emerge", "diagnose", "have", "stop", "end", "error"]
    transitions = [
        ['to_diagnose', ['start'], 'diagnose'],
        ['to_have', ['start'], 'have'],
        ['to_emerge', ['start'], 'emerge'],
        ['to_stop', ['emerge'], 'stop'],
        ['to_end', ['emerge', 'have', 'stop', 'diagnose'], 'end'],
        ['to_error', ['start', 'emerge', 'diagnose', 'have'], 'error']
    ]

    states_map_dic = {
        "emerge": {"出现"},
        "diagnose": {"诊断"},
        "have": {"有"},
        "stop": {"停用"},
        "end": {"给予", "予以", "服用", "应用", "服", "行", "予"}
    }

    act_label_dic = {
        "诊断": ["dis", "sym"],
        "给予": ["tot", "med"],
        "行": ["sur", "tot"],
        "服": ["med"],
        "服用": ["med"],
        "出现": ["dis", "sym"],
        "停用": ["tot", "med"],
        "予以": ["tot", "med"],
        "有": ["sym", "dis"],
        "应用": ["med", "tot"],
        "予": ["med", "tot"]
    }

    initial_act_types = {"诊断", "出现", "有"}


class FsmModel(object):
    """使用单例模式"""
    _instance_lock = threading.Lock()
    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(FsmModel, "_instance"):
            with FsmModel._instance_lock:
                if not hasattr(FsmModel, "_instance"):
                    FsmModel._instance = object.__new__(cls)
        return FsmModel._instance

    @staticmethod
    def seq_trans(seq, map_dic):
        trans_seq = []
        for s in seq:
            for k in map_dic:
                if s in map_dic.get(k):
                    trans_seq.append(k)
                    break
            else:
                trans_seq.append('error')
        return trans_seq

    @staticmethod
    def seq2state(state_seq, model):
        machine = Machine(model, FsmCfg.states, transitions=FsmCfg.transitions, initial='start')
        idx = 0
        length = len(state_seq)
        # 初始化转移
        state = state_seq[0]
        if state == 'emerge':
            model.to_emerge()
        elif state == 'have':
            model.to_have()
        elif state == 'diagnose':
            model.to_diagnose()
        else:
            model.to_error()

        while idx < length-1:
            if model.state == 'error':
                return model, idx
            if model.state == 'end':
                return model, idx+1

            cur_state = state_seq[idx]
            next_state = state_seq[idx+1]
            if cur_state == 'emerge':
                if next_state == 'stop':
                    model.to_stop()
                elif next_state == 'end':
                    model.to_end()
                else:
                    model.to_error()
            elif cur_state == 'diagnose':
                if next_state == 'end':
                    model.to_end()
                else:
                    model.to_error()
            elif cur_state == 'have':
                if next_state == 'end':
                    model.to_end()
                else:
                    model.to_error()
            elif cur_state == 'stop':
                if next_state == 'end':
                    model.to_end()
                else:
                    return model, idx+1

            idx += 1

        return model, idx+1


class FsmProcess(object):
    """状态机处理流程"""
    @classmethod
    def build_relationship(cls, tree, ent_list, ent_relship, model):
        rel_tokens = cls.get_rel_tokens(model, tree)
        for token_trigger, token_recv in rel_tokens:
            trigger_word, recv_word = token_trigger.word, token_recv.word
            trigger_label, recv_label = FsmCfg.act_label_dic.get(trigger_word), \
                                        FsmCfg.act_label_dic.get(recv_word)
            triggers, recvs = [], []
            for trigger_child in token_trigger.right_child:
                if trigger_child.tag in trigger_label:
                    triggers.append(ent_list.get(trigger_child.entity_id))
                    for ent_id in trigger_child.jutx_child:
                        triggers.append(ent_list.get(ent_id))
            for recv_child in token_recv.right_child:
                if recv_child.tag in recv_label:
                    recvs.append(ent_list.get(recv_child.entity_id))
                    for ent_id in recv_child.jutx_child:
                        recvs.append(ent_list.get(ent_id))
            if triggers and recvs:
                for trigger_ent_obj in triggers:
                    trigger_tag = trigger_ent_obj.get("label")
                    for recv_ent_obj in recvs:
                        recv_tag = recv_ent_obj.get("label")
                        relation_type = KernelNLPConfig.get_entity_relation_type(trigger_tag, recv_tag)
                        if relation_type:
                            ent_relship.add_entity_relationship(trigger_ent_obj, recv_ent_obj, relation_type)

    @classmethod
    def get_rel_tokens(cls, model, tree):
        rel_tokens = []
        act_tokens = cls.extract_act_tokens(tree)
        for act_pairs in act_tokens:
            act_words = [token.word for token in act_pairs]
            act_words_trans = model.seq_trans(act_words, FsmCfg.states_map_dic)
            model_res, index = model.seq2state(act_words_trans, model)
            status = model_res.state
            if status == "error":
                continue
            amend_token_pairs = act_pairs[0:index]
            token_trigger = amend_token_pairs[0]
            for token in amend_token_pairs[1:]:
                rel_tokens.append((token_trigger, token))
        return rel_tokens

    @classmethod
    def extract_act_tokens(cls, tree):
        """提取tree中连续的act对"""
        tokens = tree.root.right_child
        act_tokens = []
        index = 0
        length = len(tokens)
        if length < 2:
            return act_tokens
        while index < length:
            cur_token = tokens[index]
            if not cur_token.tag == "act" or not cur_token.word in FsmCfg.initial_act_types:
                index += 1
                continue
            next_idx = index + 1
            act_pairs = []
            act_pairs.append(cur_token)
            while next_idx < length:
                next_token = tokens[next_idx]
                if next_token.tag == "act" and next_token.word not in FsmCfg.initial_act_types:
                    act_pairs.append(next_token)
                    next_idx += 1
                else:
                    break
            if len(act_pairs) >= 2:
                act_tokens.append(act_pairs)

            index = next_idx

        return act_tokens


if __name__ == '__main__':
    fsm = FsmModel()
    seq = ["出现", "停用", "服用", "诊断", "停用"]
    states_seq = fsm.seq_trans(seq, FsmCfg.states_map_dic)
    fsm, index = fsm.seq2state(states_seq, fsm)
    print(fsm.state, index)
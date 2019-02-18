# _*_ coding:utf-8 _*_

import matplotlib.pyplot as plt
import matplotlib as mpl
from parse_tree.model.model import Tree


class TreeView(object):
    def __init__(self):
        self.fig = plt.figure(1, facecolor='white', figsize=(12, 5))
        self.fig.clf()
        self.ax = plt.subplot(111, frameon=False)
        self.ax.set_ylim(-1, 50)
        self.ax.set_xlim(-1, 30)
        mpl.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

    @staticmethod
    def plot_node(ax, node_text, center_point, parent_point, pos=None):
        """指定绘制格式"""
        # 定义文本框和箭头格式
        if pos == 'left':
            col = '#007500'  # 绿色
        elif pos == 'right':
            col = '#CC6600'  # 蓝色
        elif pos == 'root':
            col = 'red'  # root节点设置为红色
        else:
            col = 'white'  # 其余背景默认设置为白色
        node_type = dict(boxstyle="round4", fc=col)
        arrow_args = dict(arrowstyle="<-", facecolor=col)
        # node_text：节点内容；xy:(x,y)；
        ax.annotate(node_text, xy=parent_point, xycoords='axes fraction', xytext=center_point,
                    textcoords='axes fraction',
                    va="bottom", ha="center", bbox=node_type, arrowprops=arrow_args)

    def get_coord(self, cur_level, cur_num, struct_dict):
        cur_layer_ele_num = struct_dict.get(cur_level) + 2
        depth = len(struct_dict)

        y_gap = 1 / depth
        yc = 1 - 1 / (2 * depth) - cur_level  * y_gap

        x_gap = 1 / cur_layer_ele_num
        xc = cur_num * x_gap
        return xc, yc

    @staticmethod
    def view_in_graph(tree, sent_val):
        """
        使用matplotlib对树进行可视化
        """
        if tree.root is None:
            print("An Empty Tree, Nothing to plot")
        else:
            tv = TreeView()
            ax = tv.ax
            struct_dict = tree.get_struct_info()
            depth = len(struct_dict)
            # 将当前树对应的文本置于顶部
            # coord_text = (0.5, 1)
            # tv.plot_node(ax, sent_val, coord_text, coord_text)

            plt.title(sent_val, loc='center', verticalalignment='bottom', fontsize=10, fontweight='bold', bbox=dict(facecolor='g', edgecolor='blue', alpha=0.65 ))

            # 准备绘制根节点
            coord_root = (1 / 2, 1 - 1 / (2 * depth))
            tv.plot_node(ax, str(Tree.get_content(tree.root)), coord_root, coord_root, pos='root')
            node_queue = list()
            coord_queue = list()
            node_queue.append(tree.root)
            coord_queue.append(coord_root)
            cur_level = 0
            while len(node_queue):
                q_len = len(node_queue)
                cur_level += 1
                cur_num = 0
                while q_len:
                    q_node = node_queue.pop(0)
                    coord_prt = coord_queue.pop(0)
                    q_len -= 1
                    # 绘制左右节点
                    if q_node.left_child:
                        for node in q_node.left_child:
                            cur_num += 1
                            xc, yc = tv.get_coord(cur_level, cur_num, struct_dict)
                            content = Tree.get_content(node)
                            tv.plot_node(ax, content, (xc, yc), coord_prt, pos='left')
                            node_queue.append(node)
                            coord_queue.append((xc, yc))
                    if q_node.right_child:
                        for node in q_node.right_child:
                            cur_num += 1
                            xc, yc = tv.get_coord(cur_level, cur_num, struct_dict)
                            content = Tree.get_content(node)
                            tv.plot_node(ax, content, (xc, yc), coord_prt, pos='right')
                            node_queue.append(node)
                            coord_queue.append((xc, yc))

            plt.show()
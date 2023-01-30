#coding:utf-8
import logging
from PySide6.QtGui import QUndoCommand,QCursor
from vg_group import NodeGroup
from vg_edge import NodeEdge
# from vg_editor import VisualGraphTabView
from vg_node import GraphNode, TemplateNode
from tools.vg_tools import PrintHelper

class CutCommand(QUndoCommand):

    def __init__(self,editor):
        # 必须初始化父类
        super().__init__()

        self.editor = editor
        self.items = self.editor.get_selected_items()

        PrintHelper.debugPrint(f'Cut command --- {len(self.items)} items selected {self.editor.id}')

        # self.redo()

    def undo(self) -> None:
        for item in self.items:
            if isinstance(item,GraphNode):
                self.editor.add_node(item)
            elif isinstance(item,NodeEdge):
                self.editor.add_edge(item)

            elif isinstance(item,NodeGroup):
                self.editor.add_group(item)

    def redo(self):
        for item in self.items:
            if isinstance(item, GraphNode):
                # 获得相连接的edge并添加到items内部
                for edge in item.get_connected_edges():
                    if edge not in self.items:
                        self.items.append(edge)

                item.remove_self()

            elif isinstance(item,NodeGroup):
                self.editor.remove_group(item)

class PasteCommand(QUndoCommand):

    def __init__(self,editor,graph):

        super().__init__()

        self.editor = editor
        self.graph = graph


    def redo(self):
        mouse_pos = self.editor.map_mouse_to_scene()
        self.selected_items = self.editor.unselected_selected_items()
        print(str(self.selected_items))
        self.nodes,self.edges = self.editor.view.view_graph_json(self.graph,[mouse_pos.x(),mouse_pos.y()])

    def undo(self) -> None:
        # 重新选择之前的选择
        self.editor.select_items(self.selected_items)

        for edge in self.edges:
            edge.remove_self()

        for node in self.nodes:
            node.remove_self()

class GroupCommand(QUndoCommand):

    def __init__(self,editor):

        super().__init__()
        self.editor = editor


    def redo(self):
        selected_items = self.editor.get_selected_items()

        nodes = []
        edges: list[NodeEdge] = []
        # 获得最上、最下、最左、最右的坐标
        for item in selected_items:
            if isinstance(item, TemplateNode):
                nodes.append(item)

            elif isinstance(item, NodeEdge):
                edges.append(item)


        reserved_edges = []
        for edge in edges:

            if edge.get_des_node() in nodes and edge.get_source_node(
            ) in nodes:
                reserved_edges.append(edge)

        if len(nodes) == 0:
            return

        nodes.extend(reserved_edges)

        # logging.info(f'{len(nodes)} nodes selected')

        self.group = self.editor.view.add_node_group('This is a group title',nodes)

    def undo(self):
        self.editor.view.delte_node_group(self.group)


class UnGroupCommand(QUndoCommand):
    def __init__(self, editor):

        super().__init__()
        self.editor = editor
        self.groups = []

    def undo(self):

        if len(self.groups)>0:
            for group in self.groups:
                self.editor.view.add_node_group_obj(group)


    def redo(self):
        selected_items = self.editor.get_selected_items()

        # 获得选中的group
        for item in selected_items:
            if isinstance(item,NodeGroup):
                self.groups.append(item)
                self.editor.view.delte_node_group(item)


class ChangePositions(QUndoCommand):

    def __init__(self,editor,nodes,new_poses):

        super().__init__()
        self.editor = editor
        self.nodes = nodes
        self.new_poses = new_poses

        self.old_poses = []
        for node in self.nodes:
            self.old_poses.append(node.scenePos())

    def redo(self):

        for i,node in enumerate(self.nodes):
            node.setPos(self.new_poses[i])
            node.refresh_node()

    def undo(self):

        for i, node in enumerate(self.nodes):
            node.setPos(self.old_poses[i])
            node.refresh_node()

#coding:utf-8
'''
QGraphicsView的子类，是Scene的containter

'''

from collections import defaultdict
import json
import logging
from random import randint

import PySide6
from PySide6.QtCore import QEvent, Qt, QPoint, QPointF, Signal, QThread, QRectF
from PySide6.QtGui import QMouseEvent, QPainter, QPainterPath, QImage
from PySide6.QtWidgets import (QApplication, QGraphicsProxyWidget, QFileDialog,
                               QGraphicsView, QTreeWidgetItem)
from vg_dtypes import VGDtypes
from nodes.VariableNode import Getter_Setter_Helper

from nodes.ActionNode import BeginNode
from vg_edge import CuttingLine, DraggingEdge, NodeEdge
from vg_group import NodeGroup
from vg_env import VG_ENV
from vg_node import GraphNode, Node, TemplateNode
from vg_node_port import NodePort
from tools.vg_tree_widget import NodeListWidget, VariableTreeWidget
from tools.VariableManager import Variable, VariableManager
from tools.vg_tools import PrintHelper
from tools.GraphRunner import VGRunner
from execution.running_graph import RunningGraph
import os


# 用于在scene里添加和操作的基类
class VisualGraphView(QGraphicsView):

    # 定义一些信号
    nodeDropped = Signal(QPointF)
    variableDropped = Signal(QPointF, bool)

    def __init__(self, scene, parent=None):
        super().__init__(parent)

        self._nodes: list[TemplateNode] = []
        self._edges = []
        self._groups = []
        self._has_begin_node = False
        self._begin_node = None

        # 当前graph保存的路径
        self._saved_path = None

        self._session_id = 0

        self._scene = scene
        self.setScene(self._scene)
        self._scene.set_view(self)

        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing
                            | QPainter.SmoothPixmapTransform
                            | QPainter.LosslessImageRendering)

        # 隐藏滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # scale
        self._zoom_clamp = [0.2, 2]
        self._zoom_factor = 1.05
        self._view_scale = 1.0
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # 画布拖动
        self._drag_mode = False

        # 可拖动的边
        self._drag_edge = None
        self._drag_edge_mode = False

        # cutiing line
        self._cutting_mode = False
        self._cutting_line = CuttingLine()
        self._scene.addItem(self._cutting_line)

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setCacheMode(QGraphicsView.CacheBackground)

        # groups
        self.item_groups = []
        # 支持拖拽
        self.setAcceptDrops(True)

        # 变量
        self.variable_manager = VariableManager()

        # running thread
        self.runner_thread = None

    #################### view层的鼠标事件、键盘事件、滚轮事件 ####################
    def mousePressEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:

        if event.button() == Qt.MiddleButton:
            self.middleButtonPressed(event)
        elif event.button() == Qt.LeftButton:
            self.leftButtonPressed(event)

        elif event.button() == Qt.RightButton:

            self.rightButtonPressed(event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:

        if event.button() == Qt.MiddleButton:
            self.middleButtonRealeased(event)

        elif event.button() == Qt.LeftButton:
            self.leftButtonReleased(event)

        elif event.button() == Qt.RightButton:

            self.rightButtonReleased(event)

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:

        if event.button() == Qt.MiddleButton:
            self.reset_scale()

        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):

        if not self._drag_mode:

            if event.angleDelta().y() > 0:
                zoom_factor = self._zoom_factor
            else:
                zoom_factor = 1 / self._zoom_factor

            self._view_scale *= zoom_factor

            if self._view_scale < self._zoom_clamp[
                    0] or self._view_scale > self._zoom_clamp[1]:
                zoom_factor = 1.0
                self._view_scale = self._last_scale

            self._last_scale = self._view_scale

            # 每一次相对于上一次的进行缩放
            self.scale(zoom_factor, zoom_factor)

    # 鼠标移动时间
    def mouseMoveEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:

        if self._drag_edge_mode:
            self._drag_edge.update_position(self.mapToScene(event.pos()))
            # self._scene.update()

        elif self._cutting_mode:
            self._cutting_line.update_points(self.mapToScene(event.pos()))
            # self._scene.update()

        else:
            super().mouseMoveEvent(event)

    # 键盘点击
    def keyPressEvent(self, event: PySide6.QtGui.QKeyEvent) -> None:

        return super().keyPressEvent(event)

    # 鼠标中间点击
    def middleButtonPressed(self, event):

        if self.itemAt(event.pos()) is not None:
            return
        else:
            # 创建虚拟的左键松开事件
            release_event = QMouseEvent(QEvent.MouseButtonRelease, event.pos(),
                                        Qt.LeftButton, Qt.NoButton,
                                        event.modifiers())
            super().mouseReleaseEvent(release_event)

            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._drag_mode = True
            # 创建虚拟的左键点击事件
            click_event = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                                      Qt.LeftButton, Qt.NoButton,
                                      event.modifiers())
            super().mousePressEvent(click_event)

    def middleButtonRealeased(self, event):
        release_event = QMouseEvent(QEvent.MouseButtonRelease, event.pos(),
                                    Qt.LeftButton, Qt.NoButton,
                                    event.modifiers())
        super().mouseReleaseEvent(release_event)

        self.setDragMode(QGraphicsView.RubberBandDrag)
        self._drag_mode = False

    def leftButtonPressed(self, event: QMouseEvent):
        # 菜单隐藏
        self._menu_widget.hide()

        mouse_pos = event.pos()
        item = self.itemAt(mouse_pos)

        if isinstance(item, NodePort):
            # 设置为drag edge mode
            self._drag_edge_mode = True
            self.create_dragging_edge(item)

        else:
            super().mousePressEvent(event)

    def leftButtonReleased(self, event: QMouseEvent):

        if self._drag_edge_mode:
            self._drag_edge_mode = False

            item = self.itemAt(event.pos())

            if isinstance(item, NodePort):
                # self.add_graph_node()
                self._drag_edge.set_second_port(item)
                edge = self._drag_edge.create_node_edge()
                if edge is not None:
                    self._edges.append(edge)

            # 删除self._drag_edge
            self._scene.removeItem(self._drag_edge)
            self._drag_edge = None

        super().mouseReleaseEvent(event)

    def rightButtonPressed(self, event):

        item = self.itemAt(event.pos())

        if item is None:
            if (event.modifiers() == Qt.ControlModifier):
                self._cutting_mode = True
                QApplication.setOverrideCursor(Qt.CrossCursor)
            # else:
            #     self.show_nodelistw_at_pos(self.mapToScene(event.pos()))

        self.setDragMode(QGraphicsView.NoDrag)

        super().mousePressEvent(event)

    def rightButtonReleased(self, event):

        # 获得和cutting line相交的边，并删除
        self._cutting_line.remove_intersect_edges(self._edges)
        # 清除cutting line
        self._cutting_mode = False
        self._cutting_line.clear_points()
        QApplication.setOverrideCursor(Qt.ArrowCursor)

        self.setDragMode(QGraphicsView.RubberBandDrag)

    ################ 边的操作事件##########################
    def create_dragging_edge(self, port: NodePort):

        port_pos = port.get_port_pos()

        if port._port_type == NodePort.PORT_TYPE_EXEC_OUT or port._port_type == NodePort.PORT_TYPE_OUTPUT:
            drag_from_source = True
        else:
            drag_from_source = False

        if self._drag_edge is None:
            self._drag_edge = DraggingEdge(port_pos,
                                           port_pos,
                                           edge_color=port._port_color,
                                           drag_from_source=drag_from_source,
                                           scene=self._scene)
            self._drag_edge.set_first_port(port)
            self._scene.addItem(self._drag_edge)

    ### 重置scale
    def reset_scale(self):
        self.resetTransform()
        self._view_scale = 1.0

    ##################   边和节点的添加与删除操作 #################
    # 使用cls构建node对象，并添加
    def add_graph_node_with_cls(self, cls, pos, centered=False):

        node: Node = cls()
        graph_node = node.init_graphNode()

        if centered:
            pos[0] = pos[0] - graph_node.get_node_width() / 2

        self.add_graph_node(graph_node, pos)
        return graph_node

    def add_graph_node_with_cls_at_view_point(self,
                                              cls,
                                              pos: QPointF,
                                              centered=True):
        scene_pos = self.mapToScene(int(pos.x()), int(pos.y()))
        try:
            self.add_graph_node_with_cls(
                cls, [scene_pos.x(), scene_pos.y()], centered=centered)
        except ValueError as e:
            PrintHelper.printError(e)

    # 添加节点
    def add_graph_node(self, node, pos=[0, 0]):

        if isinstance(node.running_node, BeginNode):
            if self._has_begin_node:
                PrintHelper.debugPrint(
                    'View -- Add Graph Debug: BeginNode already exists.')
                return
            else:
                self._has_begin_node = True
                self._begin_node = node.running_node

        self._scene.addItem(node)
        if not pos is None:
            node.setPos(pos[0], pos[1])
        node.set_scene(self._scene)
        self._nodes.append(node)

    def add_node_edge(self, source_port, des_port):
        edge = NodeEdge(source_port, des_port, self._scene)
        self._edges.append(edge)
        self._scene.update()
        return edge

    def readd_edge(self, edge: NodeEdge):
        edge.add_to_scene()
        self._edges.append(edge)
        self._scene.update()

    def remove_edge(self, edge):
        if edge in self._edges:
            self._edges.remove(edge)

    def remove_node(self, node):

        if isinstance(node.running_node, BeginNode):
            self._has_begin_node = False
            self._begin_node = None

        self._nodes.remove(node)

    # 添加一个新的接电组
    def add_node_group(self, title, items):
        group = NodeGroup(title, items=items, scene=self._scene)
        self._groups.append(group)
        return group

    def add_node_group_obj(self, group):
        self._groups.append(group)
        group.init_item_group_rel()
        self._scene.addItem(group)
        return group

    def delte_node_group(self, group):
        group.remove_self()
        self._groups.remove(group)
        self.update()

    ###########保存与加载graph###############
    def set_saved_path(self, path):
        self._saved_path = path

    def get_saved_path(self):
        return self._saved_path

    # 判断是否能够直接保存
    def save_graph_directly(self):

        path = self.get_saved_path()

        if path is None:
            return False
        else:
            self.save_graph_to_file(path)
            return True

    # 将选中的items进行存储
    def stringfy_items(self, items):
        data = {}
        data['nodes'] = []
        data['edges'] = []

        data['base_point'] = None
        for item in items:

            if isinstance(item, TemplateNode):
                data['nodes'].append(item.to_string())

                base_point = data['base_point']
                pos = item.scenePos()

                if base_point is None:
                    data['base_point'] = [pos.x(), pos.y()]

                else:
                    if pos.x() < base_point[0]:
                        data['base_point'] = [pos.x(), pos.y()]

            if isinstance(item, NodeEdge):
                data['edges'].append(item.to_string())

        return data

    # 获得多个item的范围
    def get_item_rect(self, nodes: list[TemplateNode]) -> QRectF:
        left_top = None
        right_bottom = None
        for node in nodes:

            if not isinstance(node, TemplateNode):
                continue

            pos = node.scenePos()
            pos1 = [pos.x(), pos.y()]
            pos2 = [
                pos.x() + node.get_node_width(),
                pos.y() + node.get_node_height()
            ]

            if left_top is None:
                left_top = pos1
            elif right_bottom is None:
                right_bottom = pos2
            else:

                if pos1[0] < left_top[0]:
                    left_top[0] = pos1[0]

                if pos1[1] < left_top[1]:
                    left_top[1] = pos1[1]

                if pos2[0] > right_bottom[0]:
                    right_bottom[0] = pos2[0]

                if pos2[1] > right_bottom[1]:
                    right_bottom[1] = pos2[1]

        if left_top is None or right_bottom is None:
            return None

        return QRectF(left_top[0] - 100, left_top[1] - 100,
                      right_bottom[0] - left_top[0] + 200,
                      right_bottom[1] - left_top[1] + 200)

    def render_items(self, nodes):
        # 获得items的左上角和右上角
        rect = self.get_item_rect(nodes)

        if rect is not None:
            rect_size = rect.size().toSize()
            image = QImage(rect_size, QImage.Format_RGB32)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.LosslessImageRendering, True)
            self._scene.render(painter, source=rect)
            painter.end()

            filepath, filetype = QFileDialog.getSaveFileName(
                self, '选择保存文件', os.getcwd(), 'input file (*.png)')

            if not filepath == '':
                image.save(filepath, 'PNG', -1)
                PrintHelper.debugPrint(f'渲染的图片已保存至:{filepath}')
            else:
                PrintHelper.printWarning('图像渲染已取消。')

    def render_selected(self):
        selected_items = self.get_selected_items()
        self.unselect_items(selected_items)
        self.render_items(selected_items)
        self.select_items(selected_items)

    def render_graph(self):
        self.render_items(self._nodes)

    ### 将graph的dict添加到view内
    # base point是整个需要copy的图的左上角的坐标
    def view_graph_json(self, graph, mouse_position):
        nodes = graph['nodes']
        base_point = graph['base_point']

        distance = [
            mouse_position[0] - base_point[0],
            mouse_position[1] - base_point[1]
        ]

        nodeid_obj = {}

        node_objs = []
        edge_objs = []

        for node in nodes:
            # 获得classname对应的class类
            cls = self.get_node_cls(node)

            # 添加node
            node_pos = node['pos']
            node_obj = self.add_graph_node_with_cls(
                cls, [node_pos[0] + distance[0], node_pos[1] + distance[1]])
            node_obj.setSelected(True)
            # 不设置ID,重新生成id就可以了，防止和当前view里的id重复
            nodeid_obj[node['id']] = node_obj

            node_objs.append(node_obj)

            # 设置widget的默认值
            port_dv = node['port_defaultv']
            for i, v in port_dv.items():
                port = node_obj.get_input_port(int(i))
                port.set_widget_value(v)

        edges = graph['edges']

        for edge in edges:

            source_node = nodeid_obj.get(edge['source_node_id'], None)
            des_node = nodeid_obj.get(edge['des_node_id'], None)

            if source_node is None or des_node is None:
                continue

            source_port = source_node.get_output_port(
                edge['source_port_index'])
            des_port = des_node.get_input_port(edge['des_port_index'])

            edge = self.add_node_edge(source_port, des_port)
            edge.setSelected(True)

            edge_objs.append(edge)

        return node_objs, edge_objs

    # 将当前view的graph保存到指定的文件内
    def save_graph_to_file(self, filepath):

        data = {}
        data['graph_name'] = ''
        data['time'] = ''
        data['nodes'] = []
        data['edges'] = []
        data['groups'] = []
        data['variables'] = self.variable_manager.toJson()
        # Node
        for node in self._nodes:
            data['nodes'].append(node.to_string())

        # edge
        for edge in self._edges:
            data['edges'].append(edge.to_string())

        for group in self._groups:
            data['groups'].append(group.to_string())

        graph = json.dumps(data)

        # 和执行文件有关系
        f = open(filepath, 'w')
        f.write(graph)
        self.set_saved_path(filepath)
        f.close()
        PrintHelper.debugPrint(f'View----Graph Saved to {filepath}.')

    # 清空图
    def clear_graph(self):

        self._session_id = 0

        for node in self._nodes.copy():
            node.remove_self()

        for edge in self._edges.copy():
            edge.remove_self()

        for group in self._groups.copy():
            self.delte_node_group(group)

        self._nodes = []
        self._edges = []
        self._groups = []

        self.variable_manager.clearVariable()

        self._scene.update()

        self.update()

    def get_node_cls(self, node):

        cls_name = f"{node['module']}.{node['class']}"
        cls = VG_ENV.get_cls_by_name(cls_name)
        if cls is None:
            cls = self.variable_name_cls[cls_name]

        return cls

    #  将路径内的graph加载到view内
    def load_graph(self, filepath):

        if filepath == self.get_saved_path():
            return

        self.clear_graph()

        graph = json.loads(open(filepath).read())
        PrintHelper.debugPrint(f'View----Load Graph from {filepath}.')

        # 变量加载
        self.variable_manager.loadFromJson(graph['variables'])
        self.getVariableClsData()

        # 读取graph的node，并创建node
        nodes = graph['nodes']

        nodeid_obj = {}

        for node in nodes:
            # 获得classname对应的class类
            cls = self.get_node_cls(node)

            # 添加node
            node_obj = self.add_graph_node_with_cls(cls, node['pos'])
            node_obj.set_node_id(node['id'])

            nodeid_obj[node['id']] = node_obj

            # 设置widget的默认值
            port_dv = node['port_defaultv']
            for i, v in port_dv.items():
                port = node_obj.get_input_port(int(i))
                port.set_widget_value(v)

        edges = graph['edges']

        edgeid_obj = {}
        for edge in edges:

            source_node = nodeid_obj[edge['source_node_id']]
            des_node = nodeid_obj[edge['des_node_id']]

            source_port = source_node.get_output_port(
                edge['source_port_index'])
            des_port = des_node.get_input_port(edge['des_port_index'])

            edge_obj = self.add_node_edge(source_port, des_port)
            edge_obj.set_edge_id(edge['edge_id'])

            edgeid_obj[edge['edge_id']] = edge_obj

        groups = graph.get('groups', [])
        for group in groups:
            nodes = []
            group_title = group['title']
            nodes.extend([nodeid_obj[node_id] for node_id in group['nodes']])
            nodes.extend([edgeid_obj[edge_id] for edge_id in group['edges']])
            self.add_node_group(group_title, nodes)

        self.set_saved_path(filepath)

    ############################ 右键菜单的列表 #######################
    def setMenuWidget(self, menuW):
        self._menu_widget = menuW

    def node_selected(self, item, column):
        if isinstance(item, QTreeWidgetItem):
            cls = item.data(0, Qt.UserRole)
            if cls is not None:

                geometry = self._menu_widget.geometry()
                pos = QPointF(geometry.x(), geometry.y())
                view_pos = self.mapFromParent(pos)
                scene_pos = self.mapToScene(int(view_pos.x()),
                                            int(view_pos.y()))
                self.add_graph_node_with_cls(
                    cls, [scene_pos.x(), scene_pos.y()])
                self._menu_widget.hide()

    # 接受drop
    def dragMoveEvent(self, event) -> None:
        # print('drag move')
        if isinstance(event.source(), NodeListWidget):
            event.acceptProposedAction()
        elif isinstance(event.source(), VariableTreeWidget):
            event.acceptProposedAction()

        else:
            return super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:

        if isinstance(event.source(), NodeListWidget):
            self.nodeDropped.emit(event.pos())

        if isinstance(event.source(), VariableTreeWidget):
            self.variableDropped.emit(event.pos(),
                                      event.modifiers() == Qt.AltModifier)

        return super().dropEvent(event)

    # #####################    对选中项的操作      ##################
    def delete_selected_items(self):
        # 获得当前选中的items
        selected_items = self.get_selected_items()

        for item in selected_items:

            if isinstance(item, NodeEdge):
                item.remove_self()
                item.update()

        for item in selected_items:
            if isinstance(item, GraphNode):
                item.remove_self()
                item.update()

    def unselected_selected_items(self):

        selected_items = self.get_selected_items()

        if len(selected_items) > 0:
            for item in selected_items:
                item.setSelected(False)

        return selected_items

    def select_all_items(self):
        self.select_items(self._nodes)
        self.select_items(self._edges)

    def unselect_items(self, items):
        for item in items:
            item.setSelected(False)

    def select_items(self, items):
        for item in items:
            item.setSelected(True)

    def get_selected_items(self):
        return self._scene.selectedItems()

    def get_selected_nodes(self):
        nodes = []
        for node in self.get_selected_items():

            if isinstance(node, TemplateNode):
                nodes.append(node)

        return nodes

    def group_items(self, items):
        group = self._scene.createItemGroup(items)
        self.item_groups.append(group)

    def del_group(self, group):
        self.item_groups.remove(group)
        self._scene.destroryItemGroup()

    ##################对齐操作
    def heaviest_node(self, nodes):
        '''所连接的边越多，节点的weight越高'''
        heavy_node = None
        weight = 0
        for node in nodes:

            if not isinstance(node, TemplateNode):
                continue

            node_weight = node.get_edge_count()

            if heavy_node is None or node_weight > weight:
                heavy_node = node
                weight = node_weight

        return heavy_node

    def get_top_bottom_nodes(self, nodes: list[Node]):

        for i in range(1, len(nodes)):
            for j in range(0, len(nodes) - i):
                if nodes[j].scenePos().y() > nodes[j + 1].scenePos().y():
                    nodes[j], nodes[j + 1] = nodes[j + 1], nodes[j]

        top_node = nodes[0]

        bottom_node: Node = None
        total_height = 0
        count = 0
        for node in nodes:

            total_height += node.get_node_height()
            count += 1

            if bottom_node is None or bottom_node.scenePos().y(
            ) + bottom_node.get_node_height() < node.scenePos().y(
            ) + node.get_node_height():
                bottom_node = node

        top_y = top_node.scenePos().y()
        bottom_y = bottom_node.scenePos().y() + bottom_node.get_node_height()

        height = bottom_y - top_y

        offset = (height - total_height) / (count - 1)

        if offset < 0:

            bottom_y = top_y + total_height + (count - 1) * 5
            offset = 5

        return nodes, top_y, bottom_y, offset

    def get_left_right_nodes(self, nodes: list[Node]):

        for i in range(1, len(nodes)):
            for j in range(0, len(nodes) - i):
                if nodes[j].scenePos().x() > nodes[j + 1].scenePos().x():
                    nodes[j], nodes[j + 1] = nodes[j + 1], nodes[j]

        left_node: Node = nodes[0]
        right_node: Node = None

        total_width = 0
        count = 0

        for node in nodes:

            total_width += node.get_node_width()
            count += 1

            node_x = node.scenePos().x() + node.get_node_width()
            if right_node is None or node_x > right_node.scenePos().x(
            ) + right_node.get_node_width():
                right_node = node

        left_x = left_node.scenePos().x()
        right_x = right_node.scenePos().x() + right_node.get_node_width()

        width = right_x - left_x

        offset = (width - total_width) / (count - 1)

        if offset < 0:
            right_x = total_width + left_x + (count - 1) * 5
            offset = 5

        return nodes, left_x, right_x, offset

    def align_horizontal_center(self, nodes):

        if len(nodes) < 2:
            return None, None

        # 首先找出最上面的Item
        base_item = self.heaviest_node(nodes)
        center_x = base_item.scenePos().x() + base_item.get_node_width() / 2
        # 计算出每一个node移动出的距离，并设置
        new_poses = []
        for node in nodes:
            if not isinstance(node, TemplateNode):
                continue
            node_left = center_x - node.get_node_width() / 2
            new_poses.append(QPointF(node_left, node.scenePos().y()))

        return nodes, new_poses

    def align_vertical_center(self, nodes):
        if len(nodes) < 2:
            return None, None

        # 首先找出最左边
        base_item = self.heaviest_node(nodes)
        center_y = base_item.scenePos().y() + base_item.get_node_height() / 2
        # 计算出每一个node移动出的距离，并设置
        new_poses = []
        for node in nodes:
            if not isinstance(node, TemplateNode):
                continue
            node_top = center_y - node.get_node_height() / 2

            new_poses.append(QPointF(node.scenePos().x(), node_top))

        return nodes, new_poses

    def horizontal_distributed(self, nodes):
        if len(nodes) < 2:
            return None, None

        # 获得左右两边的节点的位置
        nodes, left_x, _, offset = self.get_left_right_nodes(nodes)
        current_x = left_x
        poses = []
        for node in nodes:
            pos = node.scenePos()
            poses.append(QPointF(current_x, pos.y()))
            current_x += (node.get_node_width() + offset)

        return nodes, poses

    def vertical_distributed(self, nodes):

        if len(nodes) < 2:
            return None, None

        nodes, top_y, _, offset = self.get_top_bottom_nodes(nodes)
        current_y = top_y
        poses = []
        for node in nodes:
            pos = node.scenePos()
            poses.append(QPointF(pos.x(), current_y))
            current_y += (node.get_node_height() + offset)

        return nodes, poses

    def align_left(self, nodes):

        if len(nodes) < 2:
            return None, None

        base_item: Node = self.heaviest_node(nodes)
        left_x = base_item.scenePos().x()
        poses = []
        for node in nodes:
            poses.append(QPointF(left_x, node.scenePos().y()))

        return nodes, poses

    def align_right(self, nodes):

        if len(nodes) < 2:
            return None, None

        base_item: Node = self.heaviest_node(nodes)
        right_x = base_item.scenePos().x() + base_item.get_node_width()
        poses = []
        for node in nodes:
            poses.append(
                QPointF(right_x - node.get_node_width(),
                        node.scenePos().y()))

        return nodes, poses

    def align_top(self, nodes):

        if len(nodes) < 2:
            return None, None

        base_item: Node = self.heaviest_node(nodes)
        top_y = base_item.scenePos().y()
        poses = []
        for node in nodes:
            poses.append(QPointF(node.scenePos().x(), top_y))

        return nodes, poses

    def align_bottom(self, nodes):

        if len(nodes) < 2:
            return None, None

        base_item: Node = self.heaviest_node(nodes)
        bottom_y = base_item.scenePos().y() + base_item.get_node_height()
        poses = []
        for node in nodes:
            poses.append(
                QPointF(node.scenePos().x(),
                        bottom_y - node.get_node_height()))

        return nodes, poses

    def align_edges(self, nodes: list[Node]):

        length = len(nodes)

        if length < 2:
            return None, None

        base_item: Node = self.heaviest_node(nodes)
        completes = [base_item]
        poses = [base_item.scenePos()]
        nodes.remove(base_item)

        run_count = 0
        while len(nodes) > 0:
            move_node = nodes[randint(0, len(nodes) - 1)]

            if run_count > 100:
                break

            run_count += 1

            connected = False
            for edge in move_node.get_connected_edges():

                source_node: Node = edge.get_source_node()
                des_node: Node = edge.get_des_node()
                base_port_pos_y = None
                des_port_pos_y = None
                if source_node.get_node_id() == move_node.get_node_id():

                    if des_node not in completes:
                        continue
                    base_port_pos_y = edge.get_source_port().scenePos().y()
                    des_port_pos_y = edge.get_des_port().scenePos().y()

                    base_node = des_node

                elif des_node.get_node_id() == move_node.get_node_id():

                    if source_node not in completes:
                        continue
                    base_port_pos_y = edge.get_des_port().scenePos().y()
                    des_port_pos_y = edge.get_source_port().scenePos().y()

                offset = des_port_pos_y - base_port_pos_y
                completes.append(move_node)
                pos = move_node.scenePos()
                poses.append(QPointF(pos.x(), pos.y() + offset))

                nodes.remove(move_node)
                connected = True

                if connected:
                    break

            # 孤立的节点
            if not connected and len(nodes) == 1:
                break

        return completes, poses

    ############# graph的运行，简单实现 ################
    def convert_to_running_graph(self):
        running_nodes = []
        for node in self._nodes:
            running_node = node.get_running_node()
            running_nodes.append(running_node)

        # 把pin和node都连接起来
        for edge in self._edges:
            edge.create_or_get_running_edge()

        var_jsons = []
        for name, var in self.variable_manager.getAllVariables().items():
            var_jsons.append(var.toJson())

        self.running_graph = RunningGraph(running_nodes, var_jsons)

    # RUN Graph
    def run_graph(self, isInBackGround=False):

        if self.runner_thread is not None and self.runner_thread.isRunning():
            PrintHelper.printWarning('这个graph已有有线程在运行。')
            return

        # 首先 在nodes里面找到BeginNode
        # 如果没有则提示没有begin graph， 需要添加begin graph
        if not self._has_begin_node:
            PrintHelper.printError('Graph needs a begin node.')
            return

        # 首先需要将node进行转化running graph
        # 包括初始化running 节点,绑定action等等
        # 重置变量
        self.convert_to_running_graph()

        #TODO background运行的方式需要修改
        #TODO 正常情况使用现在的run in background
        #TODO run in background 采用的启动一个独立进程

        try:
            if not isInBackGround:
                PrintHelper.printInfo(f'Run Graph in Main Thread.')

                self.running_graph.run_graph()
            else:
                PrintHelper.printInfo(
                    f'Run Graph In Background, new Session:{self._session_id}')

                self.run_in_new_thread()

        except ValueError as e:
            PrintHelper.printError(e)

    def run_graph_in_back(self):
        # forward的形式进行
        self.run_graph(True)

    def begin_to_run(self):
        self._begin_node.run_node_in_back()

    def run_in_new_thread(self):
        self.runner_thread = QThread()
        # 因此需要将node获取value的过程与UI进行脱离
        self.running_graph.moveToThread(self.runner_thread)
        self.runner_thread.started.connect(self.running_graph.run_graph)
        self.running_graph.finished.connect(self.running_done)
        # 运行preview node
        self.running_graph.finished.connect(self.run_preview_nodes)
        self.runner_thread.start()

    def running_done(self):
        self.runner_thread.quit()
        self.running_graph.deleteLater()
        self.runner_thread.deleteLater()
        self.runner_thread = None
        PrintHelper.debugPrint('Thread Done')

    def run_preview_nodes(self):
        for node in self._nodes:
            if node.is_preview_node:
                # 是preview node就preview
                node.preview_port()

    def new_session(self):
        self._session_id += 1
        # 刷新所有节点的状态
        for node in self._nodes:
            node.new_session(self._session_id)

    # #####################graph里面的变量增删改查############################
    def getVariable(self, name):
        return self.variable_manager.getVariable(name)

    def getVariableValue(self, name):
        return self.variable_manager.getVariableValue(name)

    def setVariableValue(self, name, value):
        self.variable_manager.setVariableValue(name, value)

    def renameVariable(self, preName, currentName):
        self.variable_manager.renameVariable(preName, currentName)

    def changeVariableType(self, name, type):
        self.variable_manager.changeVariableType(name, type)

    def changeVariableGroup(self, name, group):
        self.variable_manager.changeVariableGroup(name, group)

    def getVariables(self):
        return self.variable_manager.variables

    def addVariable(self, name, type, value, group):
        self.variable_manager.addVariable(Variable(name, type, value, group))

    def removeVariable(self, name):
        self.variable_manager.removeVariable(name)

    def getVariableData(self):
        data = defaultdict(list)
        for name, variable in self.getVariables().items():
            data[variable.getGroup()].append({
                'name': variable.getName(),
                'type': variable.getType(),
                'group': variable.getGroup()
            })
        return data

    def getVariableClsData(self):
        '''数据存储变成 module_name.class_name作为class'''

        data = defaultdict(dict)
        self.variable_name_cls = {}
        for name, variable in self.getVariables().items():

            get_cls = Getter_Setter_Helper.variable_getter_node(
                name, variable.getType())
            set_cls = Getter_Setter_Helper.variable_setter_node(
                name, variable.getType())

            data[variable.getGroup()][f'Get {name}'] = get_cls
            data[variable.getGroup()][f'Set {name}'] = set_cls

            self.variable_name_cls[
                f'{get_cls.__module__}.Get_{name}'] = get_cls
            self.variable_name_cls[
                f'{set_cls.__module__}.Set_{name}'] = set_cls

        return data

    def debug_add_variables(self):
        self.variable_manager.addVariable(
            Variable('Width', VGDtypes.Float, 2.0, 'Area'))
        self.variable_manager.addVariable(
            Variable('Height', VGDtypes.Float, 10, 'Area'))

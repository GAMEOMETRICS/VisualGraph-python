#coding:utf-8

from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsDropShadowEffect, QGraphicsProxyWidget
from PySide6.QtCore import QRectF,Qt,Signal
from PySide6.QtGui import QPainter,QPen,QColor,QBrush,QFont,QPainterPath
from vg_config import GroupConfig
from vg_node import GraphNode, TemplateNode
from vg_edge import NodeEdge
import numpy as np
from tools.vg_tools import EditableLabel,ItemSizeGrip


class NodeGroup(QGraphicsItem):

    def __init__(self,group_title = 'This is a group title',items=None,scene=None,group_height=400,group_width=800):

        super().__init__(None)

        self._scene = scene
        self._items = items

        self.group_title = group_title
        self.group_padding = 50

        self.group_title_height = 40
        self.group_bak_color = QColor(GroupConfig.group_content_bak_color)
        self.group_bak_color.setAlpha(155)

        self.init_item_group_rel()
        # 初始化group的高度与宽度
        self.init_group_width_height()

        self.init_group_title()

        self._pen_selected = QPen(QColor('#ddffee00'))
        self._pen_selected.setWidthF(2)

        self.setFlags(QGraphicsItem.ItemIsMovable|QGraphicsItem.ItemIsSelectable|QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(-2)


        # 添加resize的组件
        self._sizegrip = ItemSizeGrip(parent=self)
        self.update_sizegrip_pos()
        self._sizegrip.resize_signal.connect(self.resize_group)

        self._scene.addItem(self)

    def update_sizegrip_pos(self):

        posx, posy = self.group_width - 15, self.group_height - 15
        self._sizegrip.setPos(posx,posy)
        self._sizegrip.set_top_left_pos([self.group_min_width,self.group_title_height+10])


    def init_item_group_rel(self):
        for item in self._items:
            if isinstance(item, GraphNode):
                # 将item添加到这个组
                item.add_to_group(self)

    def init_group_width_height(self):

        # 获得最上、最下、最左、最右的坐标
        top, bottom, left, right = np.inf, -np.inf, np.inf, -np.inf
        for item in self._items:
            if isinstance(item, GraphNode):
                # 将item添加到这个组
                node_pos = item.scenePos()
                x = node_pos.x()
                left = x if x < left else left
                right = x + item._node_width if x + item._node_width > right else right
                y = node_pos.y()
                top = y if y < top else top
                bottom = y + item._node_height if y + item._node_height > bottom else bottom

        pos = [left, top]
        width = right - left
        height = bottom - top
        self.group_min_height = height + self.group_padding*2 + self.group_title_height
        self.group_min_width = width + self.group_padding*2

        # 定义一个全局的宽度和高度
        self.group_width  = self.group_min_width
        self.group_height = self.group_min_height

        self.set_pos(pos)


    # 初始化组标题
    def init_group_title(self):

        self.group_title_padding = 5
        self.title_pen = QPen(QColor(GroupConfig.group_title_pen_color))
        self.title_brush_color = QColor(GroupConfig.group_title_bak_color)
        self.title_brush_color.setAlpha(155)
        self.title_brush = QBrush(self.title_brush_color)
        self.title_font = QFont(GroupConfig.group_title_font,GroupConfig.group_title_font_size)

        self.group_pen = QPen(self.title_brush_color)
        self.group_pen.setWidthF(2)

        # self._title_item = QGraphicsTextItem(self)
        # self._title_item.setPlainText(self.group_title)
        # self._title_item.setFont(self.title_font)
        # self._title_item.setDefaultTextColor(QColor(GroupConfig.group_title_pen_color))
        # self._title_item.setPos(self.group_title_padding, self.group_title_padding)

        self._title_item = EditableLabel(self.group_title)
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(self._title_item)
        proxy.setPos(self.group_title_padding, self.group_title_padding)
        self._title_item.textchanged_signal.connect(self.title_changed)

    def title_changed(self,length):
        self.group_min_width = length
        self.group_width = self.group_width if self.group_width > self.group_min_width else self.group_min_width

        self.update_sizegrip_pos()

        self.prepareGeometryChange()
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(0,0,self.group_width,self.group_height)

    def set_pos(self,pos):
        self.setPos(pos[0]-self.group_padding,pos[1]-self.group_title_height-self.group_padding)

    def paint(self, painter: QPainter, option,widget):


        # 画背景颜色
        node_outline = QPainterPath()
        node_outline.addRoundedRect(0, 0, self.group_width, self.group_height, 1, 1)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.group_bak_color)
        painter.drawPath(node_outline.simplified())

        # 画title的背景颜色
        title_outline = QPainterPath()
        title_outline.setFillRule(Qt.WindingFill)
        title_outline.addRoundedRect(0, 0, self.group_width,
                                     self.group_title_height, 1,
                                     1)

        title_outline.addRect(0, self.group_title_height - 1, 1, 1)
        title_outline.addRect(self.group_width - 1, self.group_title_height - 1,
                             1, 1)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.title_brush)
        painter.drawPath(title_outline.simplified())

        if not self.isSelected():
            painter.setPen(self.group_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(node_outline)
        else:
            painter.setPen(self._pen_selected)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(node_outline)
            self.detect_nodes_in_rect()

            if self._items is not None:
                for item in self._items:
                    item.setSelected(True)

    def remove_self(self):
        self._scene.removeItem(self)
        self.ungroup()

    def remove_node(self,node):
        if node in self._items:
            self._items.remove(node)

    def add_node(self,node):
        if node not in self._items:
            self._items.append(node)

    def ungroup(self):
        for item in self._items:
            item._group = None

    def to_string(self):

        group = {}
        group['title'] = self._title_item.get_text()
        group['nodes'] = []
        group['edges'] = []

        for item in self._items:
            if isinstance(item,TemplateNode):
                group['nodes'].append(item.get_node_id())

            elif isinstance(item,NodeEdge):
                group['edges'].append(item.get_edge_id())

        return group


    def mouseDoubleClickEvent(self, event):

        self._title_item.labelClicked(event)


    def resize_group(self,change,pos):

        pos = self.mapToScene(pos)
        new_width = pos.x()+15-self.scenePos().x()
        new_height = pos.y()+15-self.scenePos().y()

        self.group_width = new_width
        self.group_height = new_height

        self.detect_nodes_in_rect()

        self.prepareGeometryChange()
        self.update()


    def detect_nodes_in_rect(self):

        group_rect = self.mapToScene(self.boundingRect())
        group_rect = QRectF(group_rect[0],group_rect[2])

        for node in self._scene._view._nodes:

            node_rect = node.mapToScene(node.boundingRect())
            node_rect = QRectF(node_rect[0],node_rect[2])

            if group_rect.contains(node_rect):
                if node not in self._items:
                    # self._items.append(node)
                    node.add_to_group(self)

            else:
                if node in self._items:
                    node.remove_from_current_group()






    # def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):

    #     print(change)

    #     if change == QGraphicsItem.ItemTransformChange:
    #         self.update_sizegrip_pos()

    #     return super().itemChange(change, value)

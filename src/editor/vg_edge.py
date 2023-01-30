#coding:utf-8
'''
节点的连接边
'''
from PySide6.QtWidgets import QGraphicsItem,QGraphicsPathItem,QGraphicsDropShadowEffect
from PySide6.QtGui import QPen,QColor,QPainterPath,QPainter,QPolygonF
from PySide6.QtCore import Qt,QRectF,QPointF
from vg_node_port import NodePort
import uuid
from execution.RunningEdge import RunningEdge


class NodeEdge(QGraphicsPathItem):

    def __init__(self,source_port,des_port,scene=None,edge_color = '#ffffff',parent=None):

        super().__init__(parent)

        self._source_port = source_port
        self._des_port = des_port
        self._scene = scene

        # 初始画笔
        self._edge_color = self._source_port._port_color
        self._pen_default = QPen(QColor(self._edge_color))
        self._pen_default.setWidthF(2)

        self.setZValue(-1)

        self.init_edge_id()

        # 选中投影
        self._shadow = QGraphicsDropShadowEffect()
        self._shadow.setOffset(0,0)
        self._shadow.setBlurRadius(20)

        self._shadow_color = Qt.yellow

        self.setFlags(QGraphicsItem.ItemIsSelectable)

        self.update_edge_path()

        # 添加到相关的node以及scene里面
        self.add_to_scene()

        #
        self.running_edge = None


    def init_edge_id(self):
        self._edge_id = 'e_'+str(uuid.uuid1())

    def set_edge_id(self,edge_id):
        self._edge_id = edge_id

    def get_edge_id(self):
        return self._edge_id

    def add_to_scene(self):
        self._scene.addItem(self)
        # 相关节点的port更新内容
        self._source_port.add_edge(self,self._des_port)
        self._des_port.add_edge(self,self._source_port)
        self._source_port.update()
        self._des_port.update()


    def paint(self, painter:QPainter, option, widget):

        self.update_edge_path()

        painter.setPen(self._pen_default)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

        if self.isSelected():
            self._shadow.setColor(self._shadow_color)
            self.setGraphicsEffect(self._shadow)
        else:
            self._shadow.setColor('#00000000')
            self.setGraphicsEffect(self._shadow)

    def remove_self(self):
        # 准备改变
        # self.prepareGeometryChange()

        # 删除自己
        self._scene._view.remove_edge(self)
        self._source_port.remove_edge(self)
        self._des_port.remove_edge(self)
        self._scene.removeItem(self)
        self._source_port.update()
        self._des_port.update()

        self.update()

    # 更新路径
    def update_edge_path(self):

        source_pos = self._source_port.get_port_pos()
        des_pos = self._des_port.get_port_pos()

        path = QPainterPath(source_pos)

        xwidth = source_pos.x()-des_pos.x()

        xwidth = xwidth+0.01 if xwidth ==0 else xwidth

        yheight = abs(source_pos.y()-des_pos.y())

        tangent = float(yheight)/xwidth*0.5

        tangent *= xwidth

        if xwidth>0:
            if xwidth>150:
                xwidth = 150
            tangent += xwidth
        else:
            if tangent > 150:
                tangent = 150

        path.cubicTo(QPointF(source_pos.x()+tangent,source_pos.y()),
                    QPointF(des_pos.x()-tangent,des_pos.y()),
                    des_pos)

        self.setPath(path)

    def to_string(self):

        edge = {}
        edge['edge_id'] = self._edge_id
        edge['source_node_id'] = self._source_port.get_parent_node()._node_id
        edge['source_port_index'] = self._source_port.get_port_index()

        edge['des_node_id'] =  self._des_port.get_parent_node()._node_id
        edge['des_port_index'] = self._des_port.get_port_index()

        return edge


    def get_source_node(self):
        return self._source_port.get_parent_node()

    def get_des_node(self):
        return self._des_port.get_parent_node()

    def get_source_port(self):
        return self._source_port

    def get_des_port(self):
        return self._des_port


    def create_or_get_running_edge(self):

        source_pin = self._source_port.get_running_pin()
        des_pin = self._des_port.get_running_pin()
        self.running_edge = RunningEdge(source_pin,des_pin)

        return self.running_edge


class DraggingEdge(QGraphicsPathItem):

    def __init__(self,source_pos,des_pos,drag_from_source=True,edge_color = '#ffffff',scene=None,parent=None):

        super().__init__(parent)

        self._source_pos = source_pos
        self._des_pos = des_pos
        self._drag_from_source = drag_from_source
        self._edge_color = edge_color
        self._scene = scene

        # 初始画笔
        self._edge_color = edge_color
        self._pen_default = QPen(QColor(self._edge_color))
        self._pen_default.setWidthF(2)

        self.setZValue(-1)

    def paint(self, painter: QPainter, option,widget) -> None:
        self.update_edge_path()
        painter.setPen(self._pen_default)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())


    def update_edge_path(self):

        source_pos = self._source_pos
        des_pos = self._des_pos

        if source_pos is None or des_pos is None:
            return

        path = QPainterPath(source_pos)

        xwidth = source_pos.x() - des_pos.x()

        xwidth = xwidth+0.01 if xwidth ==0 else xwidth

        yheight = abs(source_pos.y() - des_pos.y())

        tangent = float(yheight) / xwidth * 0.5

        # tangent = tangent if tangent < 1 else 1

        tangent *= xwidth

        if xwidth>0:
            if xwidth>150:
                xwidth = 150
            tangent += xwidth
        else:
            if tangent > 150:
                tangent = 150

        path.cubicTo(QPointF(source_pos.x() + tangent, source_pos.y()),
                     QPointF(des_pos.x() - tangent, des_pos.y()), des_pos)

        self.setPath(path)

    def set_first_port(self,port):

        if self._drag_from_source:
            self._source_port = port
        else:
            self._des_port = port

    def set_second_port(self,port):
        if not self._drag_from_source:
            self._source_port = port
        else:
            self._des_port = port

    def update_position(self,position):
        if self._drag_from_source:
            self._des_pos = position
        else:
            self._source_pos = position

        self.prepareGeometryChange()
        self.update_edge_path()
        self.update()


    def create_node_edge(self):
        # 首先需要判断是否能够连接
        if self.can_connect():
            edge = NodeEdge(self._source_port,self._des_port,self._scene,self._edge_color)
            return edge

        return None

    def can_connect(self):
        # 是否是成对的port
        if self.is_pair() and self.not_in_same_node() and self.has_same_class() and self.des_not_none():
            return True
        return False

    def des_not_none(self):
        if self._des_port.get_port_pos() is None:
            return False
        return True

    def is_pair(self):

        if self._source_port._port_type == NodePort.PORT_TYPE_EXEC_OUT and self._des_port._port_type == NodePort.PORT_TYPE_EXEC_IN:
            return True

        if self._source_port._port_type == NodePort.PORT_TYPE_OUTPUT and self._des_port._port_type == NodePort.PORT_TYPE_PARAM:
            return True

        return False

    def not_in_same_node(self):

        if self._source_port._parent_node == self._des_port._parent_node:
            return False

        return True

    def has_same_class(self):

        source_class = self._source_port._port_class
        if not isinstance(source_class,str):
            source_class = source_class.__name__

        des_class = self._des_port._port_class
        if not isinstance(des_class, str):
            des_class = des_class.__name__

        if des_class == 'Any':
            return True

        if source_class == des_class:
            return True

        return False



class CuttingLine(QGraphicsPathItem):

    def __init__(self,parent=None):

        super().__init__(parent)

        self._line_points = []

        self._pen = QPen(Qt.red)
        self._pen.setWidthF(1.5)
        self._pen.setDashPattern([3,3])


    def paint(self, painter: QPainter, option, widget) -> None:
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._pen)
        painter.drawPath(self.path())

    def update_points(self,point):
        self._line_points.append(point)

        poly = QPolygonF(self._line_points)
        path = QPainterPath()
        path.addPolygon(poly)
        self.setPath(path)

        self.prepareGeometryChange()
        self.update()

    def clear_points(self):
        self._line_points = []
        self.setPath(QPainterPath())

        self.prepareGeometryChange()
        self.update()

    def remove_intersect_edges(self,edges):

        for edge in edges.copy():
            path = QPainterPath()
            path.addPolygon(QPolygonF(self._line_points))

            if edge.collidesWithPath(path):
                edge.remove_self()
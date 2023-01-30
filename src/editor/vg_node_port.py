#coding:utf-8
'''
Node Port的实现
'''
from abc import abstractmethod
from PySide6.QtWidgets import QGraphicsItem,QGraphicsProxyWidget,QLineEdit,QCheckBox
from PySide6.QtGui import QColor,QPen,QBrush,QPainterPath,QPainter,QPolygonF,QFont,QFontMetrics,QIntValidator,QDoubleValidator
from PySide6.QtCore import Qt,QRectF,QPointF
from execution.RunningPort import RunningPin

from vg_config import EditorConfig,NodeConfig
from vg_dtypes import VGDtypes
import logging

class NodePort(QGraphicsItem):

    PORT_TYPE_EXEC_IN = 1001
    PORT_TYPE_EXEC_OUT = 1002
    PORT_TYPE_PARAM = 1003
    PORT_TYPE_OUTPUT = 1004

    def __init__(self,
                 port_label='',
                 port_class='str',
                 port_color='#ffffff',
                 port_type=PORT_TYPE_EXEC_IN,
                 parent=None,
                 connected_ports=None,
                 edges=None,
                 default_widget=None,
                 hide_icon = False
                 ):
        super().__init__(parent)

        self._port_label = port_label
        self._port_class = port_class
        self._port_color = port_color
        self._port_type = port_type
        self._edges = [] if edges is None else edges
        self._connected_ports:list[NodePort] = [] if edges is None else edges

        self.running_pin = None

        # 定义Pen和Brush
        self._pen_default = QPen(QColor(self._port_color))
        self._pen_default.setWidthF(1.5)
        self._brush_default = QBrush(QColor(self._port_color))
        self._font_size = EditorConfig.editor_node_pin_label_size
        self._port_font = QFont(EditorConfig.editor_node_pin_label_font, self._font_size)
        self._font_metrics = QFontMetrics(self._port_font)

        self._port_icon_size = NodeConfig.port_icon_size
        self._port_height = self._port_icon_size
        self._port_label_size = self._font_metrics.horizontalAdvance(self._port_label)
        self._port_width = self._port_icon_size + self._port_label_size
        self._hide_icon = hide_icon
        self._default_widget = None

        # 设置port的值
        self._port_value = None
        self._has_value_set = False


    def boundingRect(self) -> QRectF:
        return QRectF(0,0,self._port_width,self._port_icon_size)

    # 将本节点添加到parent node上
    def add_to_parent_node(self,parent_node,scene):
        self.setParentItem(parent_node)
        self._parent_node = parent_node
        self._scene = scene

    def get_parent_node(self):
        return self._parent_node

    def get_port_pos(self)->QPointF:

        if self._hide_icon:
            return None
        else:
            self._port_pos = self.scenePos()
            return QPointF(self._port_pos.x() + 0.25 * self._port_icon_size,
                        self._port_pos.y() + 0.5 * self._port_icon_size)


    ################# 添加或删除连接的边以及连接的port #######################

    def add_edge(self,edge,connected_port):
        self.conditioned_remove_edge()
        self._parent_node.add_connected_node(connected_port._parent_node, edge)
        self._edges.append(edge)
        self._connected_ports.append(connected_port)

    def conditioned_remove_edge(self):
        # 如果port_type 是 PORT_TYPE_EXEC_IN 以及PORT_TYPE_PARAM的话，将已有的边和连接的ports删除
        if self._port_type == NodePort.PORT_TYPE_EXEC_IN or self._port_type == NodePort.PORT_TYPE_PARAM or self._port_type == NodePort.PORT_TYPE_EXEC_OUT:

            if len(self._edges)>0:
                for edge in self._edges:
                    edge.remove_self()

    def remove_edge(self,edge):

        if edge not in self._edges:
            return

        self._edges.remove(edge)

        if edge._source_port == self:
            self._connected_ports.remove(edge._des_port)
            self._parent_node.remove_connected_node(edge._des_port._parent_node,edge)
        else:
            self._connected_ports.remove(edge._source_port)
            self._parent_node.remove_connected_node(
                edge._source_port._parent_node,
                edge)

    def is_connected(self):
        return len(self._edges) > 0

    # 返回连接的port
    def get_connected_ports(self):
        return self._connected_ports


    ##################获得 或者 设置port的值######################################

    #  新一次会话
    def new_session(self,session_id):
        self._session_id = session_id
        self._has_value_set = False
        self._port_value = None

        self.running_pin = None

    # 获得默认值
    def get_default_value(self):

        if self._default_widget is None or not self._default_widget.isVisible():
            self._port_value = None
            self._has_value_set = False
            return None
        else:
            self.set_port_value(self._default_widget.getValueFromWidget())
            return self._port_value

    def set_widget_value(self,value):
        self._default_widget.setWidgetValue(value)

    def set_port_value(self,value):
        self._port_value = value
        self._has_value_set = True

    def get_port_value(self):
        return self._port_value

    def get_value_from_connected_port(self):

        if self.is_connected():
            connected_port = self._connected_ports[0]
            # 直接获得port的值
            return connected_port.get_port_value()

        else:
            print('Node:',self._parent_node.node_title,'- Port:',self._port_label,'没有设置值且没有连接的边.')
            return None


    def set_port_index(self,index):
        self._port_index = index

    def get_port_index(self):
        return self._port_index


    def create_running_pin(self):
        pin_value = self.get_default_value()

        if self._port_type == NodePort.PORT_TYPE_EXEC_IN or self._port_type == NodePort.PORT_TYPE_EXEC_OUT:
            pin_type = 'exec'
        else:
            pin_type = 'data'
        self.running_pin = RunningPin(self._port_label,self._port_class,pin_type,pin_value)

        return self.running_pin
    
    def fetch_running_value(self):
        self.set_port_value(self.running_pin.get_pin_value())

    def get_running_pin(self):
        return self.running_pin


class EXECPort(NodePort):

    def __init__(self,
                 port_label='',
                 port_class='str',
                 port_color='#ffffff',
                 port_type=NodePort.PORT_TYPE_EXEC_IN,
                 parent=None):
        super().__init__(port_label, port_class, port_color, port_type, parent)



class EXECInPort(EXECPort):

    def __init__(self,port_label=''):
        super().__init__(port_label=port_label, port_type=NodePort.PORT_TYPE_EXEC_IN)

    def paint(self, painter: QPainter, option, widget) -> None:

        port_outline = QPainterPath()
        poly = QPolygonF()
        poly.append(QPointF(0,0.2*self._port_icon_size))
        poly.append(QPointF(0.25*self._port_icon_size,0.2*self._port_icon_size))
        poly.append(QPointF(self._port_icon_size*0.5,self._port_icon_size*0.5))
        poly.append(QPointF(0.25*self._port_icon_size,0.8*self._port_icon_size))
        poly.append(QPointF(0,0.8*self._port_icon_size))
        port_outline.addPolygon(poly)

        if not self.is_connected():
            painter.setPen(self._pen_default)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(port_outline.simplified())
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._brush_default)
            painter.drawPath(port_outline.simplified())

        painter.setPen(self._pen_default)
        painter.setFont(self._port_font)
        painter.drawText(QRectF(0.8*self._port_icon_size,0,self._port_label_size,self._port_icon_size),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,self._port_label)




class EXECOutPort(EXECPort):

    def __init__(self,port_label=''):
        super().__init__(port_label=port_label, port_type=NodePort.PORT_TYPE_EXEC_OUT)

    def paint(self, painter: QPainter, option, widget) -> None:
        # print('==',self.mapToScene(self.pos()),self._parent_node._id)
        painter.setPen(self._pen_default)
        painter.setFont(self._port_font)
        painter.drawText(QRectF(0,0,self._port_label_size,self._port_icon_size),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter,self._port_label)

        port_outline = QPainterPath()
        poly = QPolygonF()
        poly.append(QPointF(self._port_label_size+0.5*self._port_icon_size,0.2*self._port_icon_size))
        poly.append(QPointF(self._port_label_size+0.5*self._port_icon_size+0.25*self._port_icon_size,0.2*self._port_icon_size))
        poly.append(QPointF(self._port_label_size+0.5*self._port_icon_size+self._port_icon_size*0.5,self._port_icon_size*0.5))
        poly.append(QPointF(self._port_label_size+0.5*self._port_icon_size+0.25*self._port_icon_size,0.8*self._port_icon_size))
        poly.append(QPointF(self._port_label_size+0.5*self._port_icon_size,0.8*self._port_icon_size))
        port_outline.addPolygon(poly)

        if not self.is_connected():
            painter.setPen(self._pen_default)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(port_outline.simplified())
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._brush_default)
            painter.drawPath(port_outline.simplified())

    def get_port_pos(self) -> QPointF:
        port_pos = self.scenePos()
        return QPointF(port_pos.x()+self._port_label_size + 0.75 * self._port_icon_size,
                       port_pos.y() + 0.5 * self._port_icon_size)


class ParamPort(NodePort):

    def __init__(self,
                 port_label='',
                 port_class='str',
                 port_color='#ffffff',
                 parent=None,default_widget=None,hide_icon=False,default_value = None):
        super().__init__(port_label, port_class, port_color, NodePort.PORT_TYPE_PARAM, parent,default_widget=default_widget,hide_icon=hide_icon)
        self.default_value = default_value

        if default_widget is not None:
            self._default_widget = default_widget()
            self._port_width += self._default_widget.width()
            self._port_height = self._default_widget.widget_height if self._port_height < self._default_widget.widget_height else self._port_height

        self.init_widget()


    def paint(self, painter: QPainter, option, widget) -> None:
        if self._default_widget is not None:
            self._port_height = self._default_widget.widget_height

        # icon o> 来表示
        if not self.is_connected():
            painter.setPen(self._pen_default)
            painter.setBrush(Qt.NoBrush)

            if self._default_widget:
                self._default_widget.setVisible(True)
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._brush_default)

            if self._default_widget:
                self._default_widget.setVisible(False)

        if not self._hide_icon:

            painter.drawEllipse(QPointF(0.25*self._port_icon_size,0.5*self._port_icon_size),0.25*self._port_icon_size,0.25*self._port_icon_size)
            #  >
            poly = QPolygonF()
            poly.append(QPointF(0.6*self._port_icon_size,0.35*self._port_icon_size))
            poly.append(
                QPointF(0.75 * self._port_icon_size, 0.5 * self._port_icon_size))
            poly.append(
                QPointF(0.6 * self._port_icon_size, 0.65 * self._port_icon_size))

            painter.setBrush(self._brush_default)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(poly)


        # port label
        painter.setPen(self._pen_default)
        painter.setFont(self._port_font)
        painter.drawText(QRectF(self._port_icon_size,0,self._port_label_size,self._port_icon_size),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,self._port_label)


    def init_widget(self):
        if self._default_widget is None:
            return
        # 画出default widget
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(self._default_widget)
        self._default_widget.setWidgetValue(VGDtypes.get_default_value(self._port_class))

        if not self._hide_icon:
            proxy.setPos(self._port_icon_size+self._port_label_size+10,0)
        else:
            proxy.setPos(10,0)


class OutputPort(NodePort):

    def __init__(self,
                 port_label='',
                 port_class='str',
                 port_color='#ffffff',
                 parent=None):
        super().__init__(port_label, port_class, port_color,
                         NodePort.PORT_TYPE_OUTPUT, parent)

    def paint(self, painter: QPainter, option, widget) -> None:

        # port label
        painter.setPen(self._pen_default)
        painter.setFont(self._port_font)
        painter.drawText(
            QRectF(0,0,
                   self._port_label_size, self._port_icon_size),
            Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter, self._port_label)

        # icon o> 来表示
        if not self.is_connected():
            painter.setPen(self._pen_default)
            painter.setBrush(Qt.NoBrush)
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._brush_default)
        painter.drawEllipse(
            QPointF(self._port_label_size+0.5 * self._port_icon_size, 0.5 * self._port_icon_size),
            0.25 * self._port_icon_size, 0.25 * self._port_icon_size)
        #  >
        poly = QPolygonF()
        poly.append(
            QPointF(self._port_label_size + 0.85 * self._port_icon_size,
                    0.35 * self._port_icon_size))
        poly.append(
            QPointF(self._port_label_size + 1 * self._port_icon_size,
                    0.5 * self._port_icon_size))
        poly.append(
            QPointF(self._port_label_size + 0.85 * self._port_icon_size,
                    0.65 * self._port_icon_size))

        painter.setBrush(self._brush_default)
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(poly)

    def get_port_pos(self) -> QPointF:
        port_pos = self.scenePos()
        return QPointF(port_pos.x()+self._port_label_size + 0.5 * self._port_icon_size,
                       port_pos.y() + 0.5 * self._port_icon_size)



class Pin:

    def __init__(self,
                 pin_name='',
                 pin_class='',
                 use_default_widget=True,
                 pin_type='data',
                 pin_widget=None,
                 has_input=True,
                 default_value=None):

        self._pin_name = pin_name
        self._pin_type = pin_type

        if self._pin_type == 'data' or self._pin_type == 'var':
            self._pin_class = pin_class
            self._pin_color = VGDtypes.get_dtype_color(self._pin_class)

            self._pin_widget = pin_widget
            if pin_widget is None:
                # 获得默认的pin widget
                self._pin_widget = VGDtypes.default_widget.get(self._pin_class)

        self.has_input = has_input
        self.port = None
        self.default_value = default_value

    @abstractmethod
    def init_port(self,index):
        pass

    def get_port(self)->NodePort:
        return self.port


class NodeInput(Pin):

    def init_port(self,index):
        if self._pin_type=='data' or self._pin_type=='var':
            hide_icon = not self.has_input
            self.port = ParamPort(port_label=self._pin_name,port_class=self._pin_class,port_color=self._pin_color,default_widget=self._pin_widget,hide_icon=hide_icon,default_value = self.default_value)
            self.port.set_port_index(index)

        elif self._pin_type == 'exec':
            self.port = EXECInPort(port_label=self._pin_name)
            self.port.set_port_index(index)

        else:
            self.port = None
            print('No such kinds of pin type')

        return self.port

class NodeOutput(Pin):

    def init_port(self,index):
        if self._pin_type=='data' or self._pin_type=='var':
            self.port = OutputPort(port_label=self._pin_name,port_class=self._pin_class,port_color=self._pin_color)
            self.port.set_port_index(index)

        elif self._pin_type=='exec':
            self.port = EXECOutPort(port_label=self._pin_name)
            self.port.set_port_index(index)

        else:
            self.port = None
            print('No such kinds of pin type')

        return self.port

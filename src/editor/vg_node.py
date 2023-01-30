# coding:utf-8
'''
QGraphicsItem的子类

'''

from abc import abstractmethod
import logging
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsDropShadowEffect, QGraphicsProxyWidget, QPushButton
from PySide6.QtCore import QRectF, Qt, QPointF, Signal, QObject
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont, QIcon
from widgets.NodeWidget import NodeWidget
from tools.vg_tools import PrintHelper
from vg_dtypes import VGDtypes, resource_path
from vg_node_port import EXECInPort, EXECOutPort, NodePort, Pin, NodeInput, NodeOutput
from vg_config import EditorConfig, NodeConfig
import uuid
from execution.RunningPort import RunningPin
from typing import Callable, Any


class GraphNode(QGraphicsItem):

    STATE_NORMAL = '111'
    STATE_RUNNING = '1111'
    STATE_FINISHED = '11111'
    STATE_ERROR = '111111'

    def __init__(self,
                 title='',
                 param_ports=None,
                 output_ports=None,
                 is_pure=True,
                 scene=None,
                 parent=None,
                 node_position=[0, 0],
                 edges=None,
                 connected_nodes=None,
                 is_preview_node=False,
                 preview_port_index=0):

        super().__init__(parent)

        self._scene = scene

        self._node_position = node_position
        self._edges = edges if edges is not None else []
        self._connected_nodes = connected_nodes if connected_nodes is not None else []

        # 节点的title
        self._title = title

        # 定义node的大小
        self._node_width_min = 20
        self._node_height_min = 40
        self._node_width = 100
        self._node_height = 50
        self._node_radius = 3
        self._port_space = 60

        self.is_preview_node = is_preview_node
        self.preview_port_index = preview_port_index
        self._node_widget = None

        self.init_node_color()

        self.init_title()

        self.setFlags(QGraphicsItem.ItemIsSelectable
                      | QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemSendsGeometryChanges)

        # exec Ports
        self._port_padding = 10
        self._port_index = 0

        if not is_pure:
            self._node_height_min += 20

        # param ports
        self._param_ports = param_ports
        self._output_ports = output_ports

        self.init_node_width_height()
        self.init_ports()

        # 选中投影
        self._shadow = QGraphicsDropShadowEffect()
        self._shadow.setOffset(0, 0)
        self._shadow.setBlurRadius(20)
        self._shadow_color = QColor('#aaeeee00')

        # 运行的投影
        self._run_shadow_color = QColor('#aacfcfee')
        self._finished_shadow_color = QColor('#c4c')
        self._error_shaow_color = QColor('#aadd1515')

        # 所属的group
        self._group = None

        # 当前状态
        self.state = GraphNode.STATE_NORMAL

        # 设置NodeWidget
        if self.is_preview_node:
            # 设置preview node
            self.init_node_widget()

    # 初始化node widget
    def init_node_widget(self):

        # 获得preview_port_index对应的输入port
        param_port: NodePort = self._param_ports[self.preview_port_index]
        port_class = param_port._port_class
        # 获得对应的NodeWidget
        node_wdg_cls = VGDtypes.getPreviewWdgByClass(port_class)

        # 如果不是空
        if node_wdg_cls is not None and issubclass(node_wdg_cls, NodeWidget):
            self._nw_proxy = QGraphicsProxyWidget(self)
            self._node_widget = node_wdg_cls()
            self._node_widget.set_preview_port(param_port)
            self._nw_proxy.setWidget(self._node_widget)
        
            self._node_widget.setVisible(False)

        self.init_title_preview_btn()

    #  初始化title栏的运行按钮,并联立按钮
    def init_title_preview_btn(self):
        self._btn_proxy = QGraphicsProxyWidget(self)
        self._preview_btn = QPushButton(
            QIcon(resource_path('./src/editor/icons/refresh.png')), '')
        self._preview_btn.setFixedSize(self._title_height - 10,
                                       self._title_height - 10)
        self._preview_btn.setAttribute(Qt.WA_TranslucentBackground, True)
        self._preview_btn.setStyleSheet(
            'QPushButton{background-color:transparent;border:none;} QPushButton:hover{border:1px solid #c4c4c4;} QPushButton:pressed{border:2px solid #fff;}'
        )
        self._preview_btn.clicked.connect(self.preview_port)

        self._btn_proxy.setWidget(self._preview_btn)
        self.update_positions()
    

    def preview_port(self):
        self._node_widget.setVisible(True)
        self._node_widget.preview()
        self.update_positions()
        self.update()

    # update所有node widget以及port的位置
    def update_positions(self):
        self.init_node_width_height()
        self._btn_proxy.setPos(
            self._node_width - self._port_padding -
            self._btn_proxy.boundingRect().width(), self._title_padding)

    def init_node_color(self):

        self._pen_selected = QPen(QColor('#ddffee00'))
        #  node的背景
        self._brush_background = QBrush(QColor('#dd151515'))

        # color = self.get_title_color()
        self._title_bak_color = self.get_title_color()
        title_color = QColor(self._title_bak_color)
        self._pen_default = QPen(title_color)
        title_color.setAlpha(175)
        self._brush_title_back = QBrush(title_color)

    def get_node_width(self):
        return self._node_width

    def get_node_height(self):
        return self._node_height

    def get_title_color(self) -> str:
        return NodeConfig.node_title_back_color.get(self.package_name,
                                                    '#4e90fe')

    def init_ports(self):
        # 参数
        self.init_param_ports()
        # 输出
        self.init_output_ports()

    def set_scene(self, scene):
        self._scene = scene

    def get_view(self):
        return self._scene._view

    def init_title(self):

        # title的高度
        self._title_height = 35
        self._title_font_size = EditorConfig.editor_node_title_font_size
        self._title_font = QFont(EditorConfig.editor_node_title_font,
                                 self._title_font_size)
        self._title_color = Qt.white
        self._title_padding = 5

        self._title_item = QGraphicsTextItem(self)
        self._title_item.setPlainText(self._title)
        self._title_item.setFont(self._title_font)
        self._title_item.setDefaultTextColor(self._title_color)
        self._title_item.setPos(self._title_padding, self._title_padding)

        title_width = self._title_font_size * len(
            self._title) + self._node_width_min

        if self._node_width < title_width:
            self._node_width = title_width

    # def init_exec_ports(self):
    #     execin = EXECInPort()
    #     execout = EXECOutPort()
    #     self.add_port(execin)
    #     self.add_port(execout)

    def get_edge_count(self):
        return len(self._edges)

    def init_param_ports(self):

        for i, port in enumerate(self._param_ports):
            self.add_port(port, index=i)

    def init_output_ports(self):

        for i, port in enumerate(self._output_ports):
            self.add_port(port, index=i)

    def init_node_width_height(self):

        self._max_param_port_width = 0
        for _, port in enumerate(self._param_ports):

            if self._max_param_port_width < port._port_width:
                self._max_param_port_width = port._port_width

        self._max_output_port_width = 0
        for i, port in enumerate(self._output_ports):
            if self._max_output_port_width < port._port_width:
                self._max_output_port_width = port._port_width

        if self._max_param_port_width + self._max_output_port_width + self._port_space > self._node_width:
            self._node_width = self._max_param_port_width + self._max_output_port_width + self._port_space

        # Node Widget的宽度进行设置
        self.node_widget_width = 0
        self.node_widget_height = 0
        if self.is_preview_node and self._node_widget:
            self.node_widget_width = self._node_widget.width()
            self.node_widget_height = self._node_widget.height()

            if self.node_widget_width+self._port_padding*2 > self._max_param_port_width + self._max_output_port_width + self._port_space:
                self._node_width = self.node_widget_width + self._port_padding * 2 

        param_height = sum(
            [p._port_height + self._port_padding
             for p in self._param_ports]) + 5 + self._node_height_min

        output_height = len(
            self._output_ports) * (NodeConfig.port_icon_size +
                                   self._port_padding) + self._node_height_min

        self._node_height = param_height if param_height > output_height else output_height

        if self.is_preview_node and self._node_widget:
            # 设置node widget的位置
            self._nw_proxy.setPos(self._port_padding, self._node_height)
            self._node_height += self._port_padding + self.node_widget_height

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._node_width, self._node_height)

    def paint(self, painter: QPainter, option, widget):

        self.init_node_width_height()

        if self.state == GraphNode.STATE_NORMAL:
            self._shadow.setColor('#00000000')
            self.setGraphicsEffect(self._shadow)
        elif self.state == GraphNode.STATE_RUNNING:
            self._shadow.setColor(self._run_shadow_color)
            self.setGraphicsEffect(self._shadow)

        elif self.state == GraphNode.STATE_FINISHED:
            self._shadow.setColor(self._finished_shadow_color)
            self.setGraphicsEffect(self._shadow)

        elif self.state == GraphNode.STATE_ERROR:
            self._shadow.setColor(self._error_shaow_color)
            self.setGraphicsEffect(self._shadow)

        if self.isSelected():
            self._shadow.setColor(self._shadow_color)
            self.setGraphicsEffect(self._shadow)

        # 画背景颜色
        node_outline = QPainterPath()
        node_outline.addRoundedRect(0, 0, self._node_width, self._node_height,
                                    self._node_radius, self._node_radius)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(node_outline.simplified())

        # 画title的背景颜色
        title_outline = QPainterPath()
        title_outline.setFillRule(Qt.WindingFill)
        title_outline.addRoundedRect(0, 0, self._node_width,
                                     self._title_height, self._node_radius,
                                     self._node_radius)

        title_outline.addRect(0, self._title_height - self._node_radius,
                              self._node_radius, self._node_radius)
        title_outline.addRect(self._node_width - self._node_radius,
                              self._title_height - self._node_radius,
                              self._node_radius, self._node_radius)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_title_back)
        painter.drawPath(title_outline.simplified())

        if not self.isSelected():
            painter.setPen(self._pen_default)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(node_outline)
        else:
            painter.setPen(self._pen_selected)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(node_outline)

    def add_connected_node(self, node, edge):
        self._connected_nodes.append(node)
        self._edges.append(edge)

    def get_connected_nodes(self):
        return self._connected_nodes

    def remove_connected_node(self, node, edge):
        self._connected_nodes.remove(node)
        self._edges.remove(edge)

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemPositionChange:
            # 更新连接的边
            if len(self._edges) > 0:
                for edge in self._edges:
                    edge.update()
            # self.refresh_node()

        return super().itemChange(change, value)

    def add_port(self, port: NodePort, index=0):

        if port._port_type == NodePort.PORT_TYPE_EXEC_IN:
            self.add_exec_in_port(port, index=index)

        elif port._port_type == NodePort.PORT_TYPE_EXEC_OUT:
            self.add_exec_out_port(port, index=index)

        elif port._port_type == NodePort.PORT_TYPE_PARAM:
            self.add_param_port(port, index=index)

        elif port._port_type == NodePort.PORT_TYPE_OUTPUT:
            self.add_output_port(port, index=index)

    def add_exec_in_port(self, port: NodePort, index=0):
        port.add_to_parent_node(self, self._scene)
        port.setPos(
            self._port_padding, self._title_height + index *
            (self._port_padding + port._port_icon_size) + self._port_padding)

    def add_exec_out_port(self, port: NodePort, index=0):
        port.add_to_parent_node(self, self._scene)
        port.setPos(
            self._node_width - port._port_width - self._port_padding,
            self._title_height + index *
            (self._port_padding + port._port_icon_size) + self._port_padding)

    def add_param_port(self, port: NodePort, index=0):
        port.add_to_parent_node(self, self._scene)
        port.setPos(
            self._port_padding, self._title_height + index *
            (self._port_padding + port._port_icon_size) + self._port_padding)

    def add_output_port(self, port: NodePort, index=0):
        port.add_to_parent_node(self, self._scene)
        port.setPos(
            self._node_width - port._port_width - self._port_padding,
            self._title_height + index *
            (self._port_padding + port._port_icon_size) + self._port_padding)

    # 刷新node
    def refresh_node(self):
        self.update()
        for edge in self._edges:
            edge.update_edge_path()
            edge.update()

    # 删除自己
    def remove_self(self):
        # edge删除
        self.prepareGeometryChange()
        # print(len(self._edges))
        for edge in self._edges.copy():
            edge.remove_self()

        # 自己删除
        self._scene.removeItem(self)
        self._scene._view.remove_node(self)

        # group的更新
        if self._group is not None:
            self.remove_from_current_group()

        self.update()

    def get_connected_edges(self):
        return self._edges

    # group的设置
    def add_to_group(self, group):
        # 如果已有group，从已有的group里面删除
        if self._group is not None:
            self.remove_from_current_group()

        self._group = group
        self._group.add_node(self)

    def remove_from_current_group(self):
        self._group.remove_node(self)
        self._group = None

    def set_state_as_normal(self):
        self.state = GraphNode.STATE_NORMAL

    def set_state_as_running(self):
        self.state = GraphNode.STATE_RUNNING

    def set_state_as_finished(self):
        self.state = GraphNode.STATE_FINISHED

    def set_state_as_error(self):
        self.state = GraphNode.STATE_ERROR


class Node(QObject):
    '''
        Node创建Running Node， 创建时，如果widget是可见的，就将value设置为widget的值。
    '''
    # 开始运行信号
    running_start = Signal()
    # 运行错误
    running_error = Signal()
    # 运行完成
    running_finished = Signal()
    # 输入节点值设置
    inport_value_set = Signal(int, object)
    # 输出节点值设置
    outport_value_set = Signal(int, object)
    # 运行进度 progress/total
    running_progress = Signal(int, int)
    # 变量值改变
    variable_value_changed = Signal(str, object)
    # thread结束
    thread_finished = Signal(QObject)

    snew_session = Signal(int)

    # 一些设置,用于初始化graph NODE
    stored = True
    package_name = ''
    node_title = ''
    node_description = ''

    # out session
    refresh_along_session = True

    # 设置preview node
    is_preview_node = False
    preview_port_index = 0

    # 这里的pin是静态变量Pin用于定义每一个Node的port
    input_pins: list[Pin] = None
    output_pins: list[Pin] = None

    def __init__(self):

        super().__init__()
        # 自我检查参数
        self.is_validate()

        self.input_running_pins: list[RunningPin] = []
        self.output_running_pins: list[RunningPin] = []
        self.connected_nodes = []
        self.edges = []

    def is_validate(self):

        if self.node_title == '':
            PrintHelper.printError(
                f'Node {self.node_title} init: node title could not be empty')
            return False

        if self.node_title is None:
            PrintHelper.printError(
                f'Node {self.node_title} init: node title could not be None')
            return False

        if self.input_pins is None:
            self.input_pins = []

        if len(self.output_pins) is None:
            self.output_pins = []

        return True

    def init_graphNode(self):

        # TODO node widget的处理
        # Template Node里面需要添加两个参数
        # hasPreview 决定Node是否有preview功能
        # port index; port name; 决定preview那个input port

        # 这里直接创建Node
        node_cls = type(
            self.__class__.__name__, (TemplateNode, ), {
                'stored': self.stored,
                'package_name': self.package_name,
                'node_title': self.node_title,
                'node_description': self.node_description,
                'input_pins': self.input_pins,
                'output_pins': self.output_pins,
                'is_preview_node': self.is_preview_node,
                'preview_port_index': self.preview_port_index
            })

        graph_node = node_cls()
        graph_node.set_running_node(self)

        return graph_node

    # 结束线程
    def finish_thread(self):
        self.thread_finished.emit(self)

    def init_in_and_out_pins(self, in_pins, out_pins):

        # 这里的pin是running pin，用于各个存储各个实例
        self.input_running_pins: list[RunningPin] = in_pins
        self.output_running_pins: list[RunningPin] = out_pins

        for pin in self.input_running_pins:
            pin.set_parent_node(self)

        for pin in self.output_running_pins:
            pin.set_parent_node(self)

    def add_connected_node(self, running_node):
        self.connected_nodes.append(running_node)

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_input_pin(self, index):
        return self.input_running_pins[index]

    def get_output_pin(self, index):
        return self.output_running_pins[index]

    @abstractmethod
    def run_node(self):
        pass

    # running in back
    def run_node_in_back(self):
        self.running_start.emit()
        self.run_node()
        self.running_finished.emit()

    # TODO 需要确认 graph执行前 已经将running的值设置好了，主要是input pins的
    def input(self, i):
        # 这里需要将widget value设置好
        pin = self.get_input_pin(i)

        if pin.pin_type != 'data':
            self.running_error.emit()
            raise ValueError(
                f'Node {self.node_title} {i+1}th input pin is not a data pin.')

        # 首先获得widget的默认值
        pin_value = pin.get_pin_value()
        # 如果这个值没有设置，那么就需要从之前的node获取
        if pin_value is None:
            connected_pins: list[RunningPin] = pin.get_connected_pins()
            # 如果没有连接node，抛出错误
            if len(connected_pins) == 0:
                self.running_error.emit()
                raise ValueError(
                    f'{self.node_title} {i+1}-th input pin should have an connected node.'
                )
            # 只能有一个前项node
            elif len(connected_pins) == 1:
                connected_pin = connected_pins[0]
                # 从connected pin获得值，如果该pin没有设置值，那么就需要运行这个node，进行值的设置
                if not connected_pin.is_valued():
                    pre_node: Node = connected_pin.get_parent_node()
                    pre_node.run_node_in_back()
                # 从连接的pin获得值
                pin_value = connected_pin.get_pin_value()
            # 多个前项node，说明设置错误了
            else:
                self.running_error.emit()
                raise ValueError(
                    f'{self.node_title} {i+1}-th input pin should have value.')
        return pin_value

    def output(self, i, value):
        pin = self.get_output_pin(i)
        if pin.pin_type != 'data':
            self.running_error.emit()
            raise ValueError(
                f'Node {self.node_title} {i+1}th output pin is not a data pin.'
            )
        return pin.set_pin_value(value)

    def exec_input(self, i):

        pin = self.get_input_pin(i)
        if pin.pin_type != 'exec':
            raise ValueError(
                f'{self.node_title} {i+1}-th input pin is not a execution pin.'
            )

        return pin.get_pin_value()

    def exec_output(self, i):

        pin = self.get_output_pin(i)

        if pin.pin_type != 'exec':
            raise ValueError(
                f'{self.node_title} {i+1}-th output pin is not a execution pin.'
            )
        else:
            pins: list[RunningPin] = pin.get_connected_pins()

            if pins is not None and len(pins) == 1:
                # 获得连接的node然后运行
                pin = pins[0]
                # 执行端口设置为真
                pin.set_pin_value(True)
                connected_node: Node = pin.get_parent_node()
                connected_node.run_node_in_back()

    # TODO确保执行之前每一个node都设置了variableManager,只进行读取操作
    def set_variableManager(self, variableManager):
        self.variableManager = variableManager

    def getVariableValue(self, name):
        return self.variableManager.getVariableValue(name)

    def setVariableValue(self, name, value):
        # self.variable_value_changed.emit(name, value)
        self.variableManager.setVariableValue(name, value)

    def spawn_new_session(self):
        self.snew_session.emit(self._session_id + 1)

    def new_session(self, session_id):

        self._session_id = session_id

        if not self.refresh_along_session:
            return

        for pin in self.input_running_pins:
            pin.new_session(self._session_id)

        for pin in self.output_running_pins:
            pin.new_session(self._session_id)


class VGNode(Node):

    is_pure = False
    params = {}
    returns = {}
    func = lambda: None

    def __init__(self):

        self.input_pins = [] if self.is_pure else [NodeInput(pin_type='exec')]

        if self.params is None:
            self.params = self.__class__.func.__annotations__
            arg_count = self.__class__.func.__code__.co_argcount
            if self.params.get('return', None) is not None:
                self.params.pop('return')

            if len(self.params) != arg_count:
                raise ValueError(
                    f'Node {self.__class__.__name__} 没有使用修饰器正确声明节点输入及类型，并且没有使用注释方法参数类型。'
                )

        for param, dtype in self.params.items():
            if param == 'return':
                continue
            self.input_pins.append(
                NodeInput(pin_name=param, pin_class=dtype, pin_type='data'))

        self.output_pins = [] if self.is_pure else [
            NodeOutput(pin_type='exec')
        ]
        for out, dtype in self.returns.items():
            self.output_pins.append(
                NodeOutput(pin_name=out, pin_class=dtype, pin_type='data'))

        super().__init__()

    def run_node(self):
        # 获得输入的值
        args = []

        for i, (k, t) in enumerate(self.params.items()):
            # 如果不是纯函数，那么就是从1开始
            if not self.is_pure:
                i += 1

            v = self.input(i)

            if isinstance(v, t) or type(
                    v).__name__ == t.__name__ or t.__name__ == 'Any':
                args.append(v)

        results = self.__class__.func(*args)

        if isinstance(results, tuple):
            for i, r in enumerate(results):
                if not self.is_pure:
                    i += 1

                self.output(i, r)
        else:
            i = 0
            if not self.is_pure:
                i += 1

            self.output(i, results)

        if not self.is_pure:
            self.exec_output(0)


class TemplateNode(GraphNode):

    stored = True
    package_name = ''
    node_title = ''
    node_description = ''

    input_pins: list[Pin] = None
    output_pins: list[Pin] = None

    is_preview_node = False
    preview_port_index = 0

    def __init__(self):

        self.in_ports: list[NodePort] = [
            pin.init_port(i) for i, pin in enumerate(self.input_pins)
        ]
        self.out_ports: list[NodePort] = [
            pin.init_port(i) for i, pin in enumerate(self.output_pins)
        ]
        super().__init__(self.node_title,
                         param_ports=self.in_ports,
                         output_ports=self.out_ports,
                         is_pure=True,
                         is_preview_node=self.is_preview_node,
                         preview_port_index=self.preview_port_index)

        # 状态
        self._input_data_ready = False
        self._output_data_ready = False
        # 随机生成的
        self._node_id = 'n_' + str(uuid.uuid1())

        self.running_node = None

    def set_node_id(self, id):
        self._node_id = id

    def get_node_id(self):
        return self._node_id

    # 创建新的ssession
    def new_session(self, session_id):
        self._session_id = session_id

        for port in self.in_ports:
            port.new_session(self._session_id)

        for port in self.out_ports:
            port.new_session(self._session_id)

    def get_input_port(self, i):
        return self.in_ports[i]

    def get_output_port(self, i):
        return self.out_ports[i]

    def to_string(self):

        node = {}

        node['id'] = self._node_id
        running_node_cls = self.running_node.__class__
        node['class'] = running_node_cls.__name__
        node['module'] = running_node_cls.__module__
        node['pos'] = [self.scenePos().x(), self.scenePos().y()]
        node['port_defaultv'] = {}
        for i, port in enumerate(self.in_ports):

            dv = port.get_default_value()

            if dv is not None:
                node['port_defaultv'][i] = dv

        return node

    # 运行前初始化 running node并设置variableMangager
    def get_running_node(self):
        input_running_pins = []
        for port in self.in_ports:
            input_running_pins.append(port.create_running_pin())

        out_running_pins = []
        for port in self.out_ports:
            out_running_pins.append(port.create_running_pin())

        self.running_node.init_in_and_out_pins(input_running_pins,
                                               out_running_pins)

        # self.running_node.set_variableManager(self.get_view().variable_manager)

        return self.running_node

    def fetch_value_from_running_node(self):
        for port in self.in_ports:
            port.fetch_running_value()

        for port in self.out_ports:
            port.fetch_running_value()

    def set_running_node(self, running_node):
        self.running_node: Node = running_node
        # # 将running node的状态进行绑定

        # self.running_node.running_start.connect(self.onStart)
        self.running_node.thread_finished.connect(self.onFinished)
        # self.running_node.running_error.connect(self.onError)
        # self.running_node.variable_value_changed.connect(
        # self.onVariableValueChanged)

    def onStart(self):
        if PrintHelper.DEBUG_MODE:
            self.set_state_as_running()
            self.update()
            PrintHelper.debugPrint(f'{self.node_title} STARTS.')

    def onFinished(self):
        if PrintHelper.DEBUG_MODE:

            # self.set_state_as_finished()
            # self.update()
            PrintHelper.debugPrint(f'{self.node_title} finish.')

        # 结束之后将pin进行传值
        self.fetch_value_from_running_node()

    def onError(self):
        self.set_state_as_error()
        self.update()
        # PrintHelper.debugPrint(f'{self.node_title} Error.')

    def onVariableValueChanged(self, name, value):
        # PrintHelper.debugPrint(f'{self.node_title} change variable {name} value {value}.')
        self.get_view().setVariableValue(name, value)

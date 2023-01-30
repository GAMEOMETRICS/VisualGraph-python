#coding:utf-8
'''
编辑器主体

'''
import sys
from functools import partial
import os
from PySide6.QtWidgets import QPushButton, QWidget,QBoxLayout,QMainWindow,QVBoxLayout,QFileDialog,QTabWidget,QApplication,QDockWidget,QHBoxLayout,QLabel,QSplitter,QToolBox,QTreeWidgetItem
from nodes.VariableNode import Getter_Setter_Helper
from vg_dtypes import VGDtypes
from vg_edge import NodeEdge
from vg_edit_command import CutCommand, GroupCommand, PasteCommand,UnGroupCommand,ChangePositions
from vg_env import VG_ENV
from PySide6.QtGui import QMouseEvent, QGuiApplication, QAction,QKeySequence,QCursor,QUndoStack,QUndoCommand,QPainter,QImage
from PySide6.QtCore import Qt,QPointF,QSize,QThread
import logging

from queue import Queue

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO)

from vg_view import VisualGraphView
from vg_scene import VisualGraphScene
from vg_node import GraphNode
from tools.vg_tree_widget import NodeListWidget
from tools.vg_tools import VariableAttrSet,EmittingStream,PrintHelper,StdReceiver
import json
# PrintHelper.DEBUG_MODE = False

import numpy as np

from tools.SidebarWidgets import SidebarWidget,DetailWidget
from tools.vg_tree_widget import VariableTreeWidget,FuncTreeWidget

from vg_widgets import LoggerWidget

class VisualGraphWindow(QMainWindow):

    def __init__(self,parent=None):

        super().__init__(parent)
        # 初始化node环境
        VG_ENV.initialize_node_env()

        self.setWindowTitle('Visual Graph')
        self.resize(2000,1080)
        self.center()

        self.splitter = QSplitter(Qt.Horizontal,self)

        # 编辑器设置，位置在中间，占比例至少80%
        self.setup_editor()

        # 初始化菜单栏
        self.initialize_menubar()

        # 初始化左右侧边栏
        self.initialize_sidebar()

        # 设置布局的初始大小
        self.setup_layout()

        # 剪贴板
        self.clipboard = QApplication.clipboard()

        # 输入流和输出流
        # self.setup_logger()


    def setup_logger(self):
        # TODO 这是一个终端的BUG 需要一个更好用的shell来覆盖
        self.std_thread = QThread()
        std_queue = Queue()
        sys.stdout = EmittingStream(std_queue)
        self.std_receiver = StdReceiver(std_queue)

        #把标准输出流用一个thead进行撰写
        self.std_receiver.std.connect(self.onStdOutWritten)
        self.std_receiver.moveToThread(self.std_thread)
        self.std_thread.started.connect(self.std_receiver.printStr)
        self.std_thread.start()
    
    # def closeEvent(self, event) -> None:
    #     self.std_receiver.deleteLater()
    #     self.std_thread.quit()
    #     return super().closeEvent(event)


    def setup_editor(self):
        # Visual Graph的编辑器 TabWidget编辑器
        self.editor: VisualGraphTab = None
        self.tab_count = 0
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setTabsClosable(True)
        # self.setCentralWidget(self.tabWidget)
        self.add_a_tab()
        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.tabWidget.tabCloseRequested.connect(self.tab_close)
        self.opened_graphs = {}

    def initialize_sidebar(self):

        # 左边是一个QFrame
        self.left_sidebar = QWidget(self)
        self.left_layout = QVBoxLayout(self.left_sidebar)
        self.left_layout.setContentsMargins(0,0,0,0)

        sw = SidebarWidget(title='',isStretch= False)

        # 添加一个树
        self.func_tree = FuncTreeWidget(sw)
        sw.addComp(f'函数', self.func_tree, False,10)

        self.vari_tree = VariableTreeWidget(sw)
        sw.addComp(f'变量', self.vari_tree, False,20)
        self.initVariableTree()

        self.left_layout.addWidget(sw)

        # 左边侧边栏 一个边栏TitleBar
        self.right_sidebar = QWidget(self)
        self.right_layout = QVBoxLayout(self.right_sidebar)
        self.right_layout.setContentsMargins(0,0,0,0)

        sw = SidebarWidget(title='', isStretch=False)

        # 添加一个树
        self.model_data = VG_ENV.get_nodelib_json_data()
        self.model_tree = NodeListWidget(self.model_data,self,dragEnabled=True)
        sw.addComp(f'模块库', self.model_tree, False,10)

        self.detail_widget = DetailWidget(None, self)
        sw.addComp(f'详情', self.detail_widget, False,20)
        self.detail_widget.valueChanged.connect(self.refreshVariableTree)

        self.right_layout.addWidget(sw)


    ########################变量树##############################################
    # 刷新变量树，根据当前tab
    def refreshVariableTree(self):
        data = self.editor.view.getVariableData()
        self.vari_tree.loadTreeFromDict(data)

    def initVariableTree(self):
        self.vari_tree.itemAdded.connect(self.onVariableAdded)
        self.vari_tree.itemRenamed.connect(self.onVariableRenamed)
        self.vari_tree.itemRegrouped.connect(self.onVariableRegrouped)
        self.vari_tree.itemDeleted.connect(self.onVariableDeleted)
        self.vari_tree.itemSelected.connect(self.onVariableSelected)
        self.refreshVariableTree()

    def onVariableAdded(self,item:QTreeWidgetItem):
        data = item.data(0,Qt.UserRole)
        dtype = data['type']
        if isinstance(dtype,str):
            dtype = VGDtypes.dtypes_clses[dtype]
        self.editor.view.addVariable(data['name'],dtype,VGDtypes.get_default_value(dtype),data['group'])

    def onVariableRenamed(self,preName,item:QTreeWidgetItem):
        data = item.data(0,Qt.UserRole)
        self.editor.view.renameVariable(preName,data['name'])

    def onVariableRegrouped(self,item):
        data = item.data(0,Qt.UserRole)
        self.editor.view.changeVariableGroup(data['name'],data['group'])

    def onVariableDeleted(self,item):
        name = item.data(0,Qt.UserRole)['name']
        self.editor.view.removeVariable(name)

    def onVariableSelected(self,item):
        name = item.data(0,Qt.UserRole)['name']
        selected_var = self.editor.view.getVariable(name)
        self.detail_widget.refresh(VariableAttrSet(selected_var))

    ###########################################################
    def setup_logger_console(self):
        self.logger_widget = LoggerWidget(self)
        # TODO 先隐藏Logger Widget,之后再做
        self.logger_widget.hide()


    def setup_layout(self):
        # 设置中间splitter
        self.setup_centeral_splitter()

        self.splitter.addWidget(self.left_sidebar)
        self.splitter.addWidget(self.center_splitter)
        self.splitter.addWidget(self.right_sidebar)
        self.splitter.setSizes([250,1500,250])
        self.setCentralWidget(self.splitter)

    def setup_centeral_splitter(self):
        self.setup_logger_console()

        self.center_splitter = QSplitter(Qt.Vertical,self)
        self.center_splitter.addWidget(self.tabWidget)
        self.center_splitter.addWidget(self.logger_widget)
        self.center_splitter.setSizes([800,200])

    def tab_changed(self,index):
        # 当前不的都关闭之后index返回-1
        if index>=0:
            self.editor = self.tabWidget.currentWidget()

        self.refreshVariableTree()

    def tab_close(self,index):
        self.tabWidget.removeTab(index)
        self.record_graph_closed(index)

        self.tab_count -= 1

        if self.tabWidget.count()==0:
            self.add_a_tab()


    def add_a_tab(self,filepath=None):
        self.tab_count +=1

        tab_view = VisualGraphTab(self)
        if filepath is None or isinstance(filepath,int):
            tab_tile = f'Unititled-{self.tab_count} Graph'
        else:
            tab_tile = os.path.basename(filepath)

        self.tabWidget.addTab(tab_view,tab_tile)
        self.tabWidget.setCurrentIndex(self.tabWidget.count()-1)
        self.editor = self.tabWidget.currentWidget()

        tab_view.view.nodeDropped.connect(self.onNodeDropped)
        tab_view.view.variableDropped.connect(self.onVariableDropped)

    # model中的函数拖入
    def onNodeDropped(self,pos):
        # 拖拽的是哪个item，从item里面获得class name
        cls = self.model_tree.getDraggedItem().data(0,Qt.UserRole)
        if cls is not None:
            self.editor.view.add_graph_node_with_cls_at_view_point(cls,pos)
            self.editor.hide_menu()

    # 变量拖入
    def onVariableDropped(self,pos,hasControlPressed):
        data = self.vari_tree.getDraggedItem().data(0,Qt.UserRole)
        if hasControlPressed:
            cls = Getter_Setter_Helper.variable_setter_node(
                data['name'], data['type'])
        else:
            cls = Getter_Setter_Helper.variable_getter_node(data['name'], data['type'])
        self.editor.view.add_graph_node_with_cls_at_view_point(cls, pos)
        self.editor.hide_menu()


    def initialize_menubar(self):
        # 菜单栏
        self.create_actions()
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.newGraphAction)
        fileMenu.addAction(self.newEditorAction)
        fileMenu.addSeparator()

        fileMenu.addAction(self.openAction)
        self.recent_menu = fileMenu.addMenu('Open recent graphs:')
        self.recent_menu.aboutToShow.connect(self.show_recent_files)
        # 添加Recent file TODO 等save功能完成以后进行
        fileMenu.addSeparator()
        fileMenu.addAction(self.workspaceAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addAction(self.saveAllAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.quitAction)

        editMenu = menuBar.addMenu('&Edit')
        editMenu.addAction(self.undoAction)
        editMenu.addAction(self.redoAction)
        editMenu.addSeparator()
        editMenu.addAction(self.cutAction)
        editMenu.addAction(self.copyAction)
        editMenu.addAction(self.pasteAction)
        editMenu.addSeparator()
        editMenu.addAction(self.delAction)
        editMenu.addSeparator()
        editMenu.addAction(self.commentAction)
        editMenu.addAction(self.groupAction)
        editMenu.addAction(self.unGroupAction)
        editMenu.addSeparator()
        editMenu.addAction(self.selectAllAction)
        editMenu.addAction(self.deselectAllAction)

        alignMenu = menuBar.addMenu('&Alignment')
        alignMenu.addAction(self.alignVCenterAction)
        alignMenu.addAction(self.alignHCenterAction)
        alignMenu.addSeparator()
        alignMenu.addAction(self.verticalDistributedAction)
        alignMenu.addAction(self.horizontalDistributedAction)
        alignMenu.addSeparator()
        alignMenu.addAction(self.alignLeftAction)
        alignMenu.addAction(self.alignRightAction)
        alignMenu.addAction(self.alignTopAction)
        alignMenu.addAction(self.alignBottomAction)
        alignMenu.addSeparator()
        alignMenu.addAction(self.straightenEdgeAction)

        viewMenu = menuBar.addMenu('&View')
        viewMenu.addAction(self.showLoggerAction)
        viewMenu.addAction(self.showLeftSidebarAction)
        viewMenu.addAction(self.showRightSidebarAction)

        renderMenu = menuBar.addMenu('&Render')
        renderMenu.addAction(self.renderSelectedAction)
        renderMenu.addAction(self.renderAllNodesAction)


        runMenu = menuBar.addMenu('&Run')
        runMenu.addAction(self.runAction)
        runMenu.addAction(self.runInBackAction)

        helpMenu = menuBar.addMenu('&Help')

        # 最近文件列表,只记录文件绝对路径
        self.recent_files = []


    def center(self):
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()

        self.center_move = [(screen.width() - size.width()) / 2-200,
                            (screen.height() - size.height()) / 2]
        self.move(self.center_move[0], self.center_move[1])

    def create_actions(self):

        # 文件菜单栏
        self.newGraphAction = QAction('New Graph',self)
        self.newGraphAction.setShortcut(QKeySequence.New)
        self.newGraphAction.triggered.connect(self.add_a_tab)

        self.newEditorAction = QAction('New Window', self)
        self.newEditorAction.setShortcut(QKeySequence('Ctrl+Shift+N'))

        self.openAction = QAction('Open',self)
        self.openAction.setShortcut(QKeySequence('Ctrl+O'))
        self.openAction.triggered.connect(self.dialog_open_graph)

        self.workspaceAction = QAction('Set Workspace Path', self)


        self.saveAction = QAction('Save',self)
        self.saveAction.setShortcut(QKeySequence('Ctrl+S'))
        self.saveAction.triggered.connect(self.save_graph)

        self.saveAsAction = QAction('Save As', self)
        self.saveAsAction.setShortcut(QKeySequence('Ctrl+Shift+S'))
        self.saveAsAction.triggered.connect(self.save_graph_as)

        self.saveAllAction = QAction('Save All', self)
        self.saveAllAction.setShortcut(QKeySequence('Ctrl+Alt+S'))
        self.saveAllAction.triggered.connect(self.save_all_graph)

        self.quitAction = QAction('Quit', self)
        self.quitAction.setShortcut(QKeySequence('Alt+F4'))
        self.quitAction.triggered.connect(self.quit)


        self.clearMenuAction = QAction('Clear recent graph list')
        self.clearMenuAction.triggered.connect(self.clear_recent_files)


        self.copyAction = QAction('Copy',self)
        self.copyAction.setShortcut(QKeySequence('Ctrl+C'))
        self.copyAction.triggered.connect(self.copy_items)

        self.cutAction = QAction('Cut', self)
        self.cutAction.setShortcut(QKeySequence('Ctrl+X'))
        self.cutAction.triggered.connect(self.cut_items)

        self.pasteAction = QAction('Paste',self)
        self.pasteAction.setShortcut(QKeySequence('Ctrl+V'))
        self.pasteAction.triggered.connect(self.paste_items)


        self.undoAction = QAction('Undo',self)
        self.undoAction.setShortcut(QKeySequence('Ctrl+Z'))
        self.undoAction.triggered.connect(self.undo_edit)


        self.redoAction = QAction('Redo',self)
        self.redoAction.setShortcut(QKeySequence('Ctrl+Y'))
        self.redoAction.triggered.connect(self.redo_edit)

        self.delAction = QAction('Delete selected items',self)
        self.delAction.setShortcuts([QKeySequence('X'),QKeySequence('Delete')])
        self.delAction.triggered.connect(self.remove_selected)


        self.commentAction = QAction('Comment Nodes',self)
        self.commentAction.setShortcut(QKeySequence('Ctrl+Alt+C'))

        self.groupAction = QAction('Group Nodes',self)
        self.groupAction.setShortcut(QKeySequence('Ctrl+G'))
        self.groupAction.triggered.connect(self.group_items)

        # 将group节点删除
        self.unGroupAction = QAction('UnGroup',self)
        self.unGroupAction.setShortcut(QKeySequence('Alt+G'))
        self.unGroupAction.triggered.connect(self.ungroup_items)

        # 全选和全不选
        self.selectAllAction = QAction('Select All',self)
        self.selectAllAction.setShortcut(QKeySequence('Ctrl+A'))
        self.selectAllAction.triggered.connect(self.selectAllItems)


        # 全选和全不选
        self.deselectAllAction = QAction('Deselect All', self)
        self.deselectAllAction.setShortcut(QKeySequence('Ctrl+D'))
        self.deselectAllAction.triggered.connect(self.deselectAllItems)

        # 调节editor各个view的显示
        # 先调整一个 console的显示
        self.showLoggerAction = QAction('Show Logger',self)
        self.showLoggerAction.setShortcut(QKeySequence('Alt+Shift+B'))
        self.showLoggerAction.setCheckable(True)
        self.showLoggerAction.setChecked(False)
        self.showLoggerAction.triggered.connect(self.show_logger)

        self.showLeftSidebarAction = QAction('Show Left Sidebar', self)
        self.showLeftSidebarAction.setShortcut(QKeySequence('Alt+Shift+L'))
        self.showLeftSidebarAction.setCheckable(True)
        self.showLeftSidebarAction.setChecked(True)
        self.showLeftSidebarAction.triggered.connect(self.show_left)

        self.showRightSidebarAction = QAction('Show Left Sidebar', self)
        self.showRightSidebarAction.setShortcut(QKeySequence('Alt+Shift+R'))
        self.showRightSidebarAction.setCheckable(True)
        self.showRightSidebarAction.setChecked(True)
        self.showRightSidebarAction.triggered.connect(self.show_right)


        # renderAction
        self.renderSelectedAction = QAction('Render Selected Nodes',self)
        self.renderSelectedAction.setShortcut(QKeySequence('Ctrl+Alt+R'))
        self.renderSelectedAction.triggered.connect(self.renderSelected)

        # renderAction
        self.renderAllNodesAction = QAction('Render Graph', self)
        self.renderAllNodesAction.setShortcut(QKeySequence('Ctrl+Shift+R'))
        self.renderAllNodesAction.triggered.connect(self.renderGraph)

        # Align Action
        self.alignVCenterAction = QAction('Align Vertical Center',self)
        self.alignVCenterAction.setShortcut(QKeySequence('V'))
        self.alignVCenterAction.triggered.connect(self.alignVCenter)

        self.verticalDistributedAction = QAction('Vertical Equally Distribution', self)
        self.verticalDistributedAction.setShortcut(QKeySequence('Shift+V'))
        self.verticalDistributedAction.triggered.connect(self.alignVDistributed)

        self.alignHCenterAction = QAction('Align Horizontal Center',self)
        self.alignHCenterAction.setShortcut(QKeySequence('H'))
        self.alignHCenterAction.triggered.connect(self.alignHCenter)

        self.horizontalDistributedAction = QAction('Horizontal Equally Distribution',
                                                  self)
        self.horizontalDistributedAction.setShortcut(QKeySequence('Shift+H'))
        self.horizontalDistributedAction.triggered.connect(self.alignHDistributed)

        self.alignLeftAction = QAction('Align Horizontal Left', self)
        self.alignLeftAction.setShortcut(QKeySequence('Shift+L'))
        self.alignLeftAction.triggered.connect(self.alignLeft)

        self.alignRightAction = QAction('Align Horizontal Right', self)
        self.alignRightAction.setShortcut(QKeySequence('Shift+R'))
        self.alignRightAction.triggered.connect(self.alignRight)

        self.alignTopAction = QAction('Align Vertical Top', self)
        self.alignTopAction.setShortcut(QKeySequence('Shift+T'))
        self.alignTopAction.triggered.connect(self.alignTop)

        self.alignBottomAction = QAction('Align Vertical Bottom', self)
        self.alignBottomAction.setShortcut(QKeySequence('Shift+B'))
        self.alignBottomAction.triggered.connect(self.alignBottom)

        self.straightenEdgeAction = QAction('Straighten Edge',self)
        self.straightenEdgeAction.setShortcut(QKeySequence('Q'))
        self.straightenEdgeAction.triggered.connect(self.straightenEdge)

        self.runAction = QAction('Run Graph',self)
        self.runAction.setShortcut(QKeySequence('Ctrl+R'))
        self.runInBackAction = QAction('Run Graph In Background', self)
        self.runInBackAction.setShortcut(QKeySequence('Ctrl+B'))

        self.runAction.triggered.connect(self.run_graph)
        self.runInBackAction.triggered.connect(self.run_graph_in_back)

    ################ 节点对齐

    def alignVCenter(self):
        '''垂直中心对齐'''
        nodes,poses = self.editor.view.align_vertical_center(self.editor.view.get_selected_nodes())
        if nodes is None:
            return
        change_pos_command = ChangePositions(self,nodes,poses)
        self.editor.add_action_to_stack('Align Vertical Center',change_pos_command)


    def alignHCenter(self):
        '''水平中心对齐'''
        nodes,poses = self.editor.view.align_horizontal_center(
            self.editor.view.get_selected_nodes())

        if nodes is None:
            return

        change_pos_command = ChangePositions(self, nodes, poses)
        self.editor.add_action_to_stack('Align Horizontal Center',change_pos_command)


    def alignVDistributed(self):
        nodes,poses = self.editor.view.vertical_distributed(self.editor.view.get_selected_nodes())
        if nodes is None:
            return
        change_pos_command = ChangePositions(self, nodes, poses)
        self.editor.add_action_to_stack('Vertical Equally Distribution',change_pos_command)

    def alignHDistributed(self):
        nodes,poses = self.editor.view.horizontal_distributed(self.editor.view.get_selected_nodes())
        if nodes is None:
            return
        change_pos_command = ChangePositions(self, nodes, poses)
        self.editor.add_action_to_stack('Horizontal Equally Distribution',change_pos_command)

    def alignLeft(self):
        nodes,poses = self.editor.view.align_left(self.editor.view.get_selected_nodes())
        if nodes is None:
            return
        change_pos_command = ChangePositions(self, nodes, poses)
        self.editor.add_action_to_stack('Align Left',
                                        change_pos_command)

    def alignRight(self):
        nodes,poses = self.editor.view.align_right(self.editor.view.get_selected_nodes())
        if nodes is None:
            return
        change_pos_command = ChangePositions(self, nodes, poses)
        self.editor.add_action_to_stack('Align Left',
                                        change_pos_command)

    def alignTop(self):
        nodes, poses = self.editor.view.align_top(
            self.editor.view.get_selected_nodes())
        if nodes is None:
            return
        change_pos_command = ChangePositions(self, nodes, poses)
        self.editor.add_action_to_stack('Align Left', change_pos_command)

    def alignBottom(self):
        nodes, poses = self.editor.view.align_bottom(
            self.editor.view.get_selected_nodes())
        if nodes is None:
            return
        change_pos_command = ChangePositions(self, nodes, poses)
        self.editor.add_action_to_stack('Align Left', change_pos_command)


    def straightenEdge(self):

        nodes,poses = self.editor.view.align_edges(self.editor.view.get_selected_nodes())

        if nodes is None:
            return
        change_pos_command = ChangePositions(self, nodes, poses)
        self.editor.add_action_to_stack('Align Left', change_pos_command)


    ######################全选和全不选
    def selectAllItems(self):
        self.editor.view.select_all_items()

    def deselectAllItems(self):
        self.editor.view.unselected_selected_items()

    # ################# Render 操作
    def renderSelected(self):

        self.editor.view.render_selected()

    def renderGraph(self):
        self.editor.view.render_graph()

    ##############View 的操作####################
    def show_logger(self):

        if self.logger_widget.isVisibleTo(self):
            self.logger_widget.hide()
        else:
            self.logger_widget.show()

    def show_left(self):

        if self.left_sidebar.isVisibleTo(self):
            self.left_sidebar.hide()
        else:
            self.left_sidebar.show()

    def show_right(self):

        if self.right_sidebar.isVisibleTo(self):
            self.right_sidebar.hide()
        else:
            self.right_sidebar.show()


    ###############编辑菜单#####################

    # 将选中的node进行复制
    def copy_items(self):
        # 获得当前的view，在view中获取已选择的items
        selected_items = self.editor.stringfy_selected_items()

        if selected_items is None:
            PrintHelper.debugPrint('editor ---- nothing selected!')

        else:
            self.clipboard.clear()
            self.clipboard.setText(json.dumps(selected_items))

    def cut_items(self):
        selected_items = self.editor.stringfy_selected_items()
        if selected_items is None:
            PrintHelper.debugPrint('editor ---- nothing selected!')

        else:
            self.clipboard.clear()
            self.clipboard.setText(json.dumps(selected_items))
            self.editor.cut_items()


    def paste_items(self):

        try:
            items = json.loads(self.clipboard.text())
            if items.get('nodes',None) is not None:
                #将items添加到view里面
                self.editor.paste_selected_items(items)

            else:
                PrintHelper.debugPrint('editor ------- no nodes in clipborad')

        except ValueError as e:
            PrintHelper.debugPrint('editor ------- noting in clipborad',e)

    def undo_edit(self):
        self.editor.undo_edit()

    def redo_edit(self):
        self.editor.redo_edit()

    def remove_selected(self):
        self.editor.del_items()

    def group_items(self):
        self.editor.group_items()

    def ungroup_items(self):
        self.editor.ungroup_items()

    def run_graph(self):
        self.editor.run_graph()

    def run_graph_in_back(self):
        self.editor.run_graph_in_back()

    ############## 文件操作 #################

    def add_to_recent_file(self,filepath):
        # self.recent_files.append(filepath)
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)

        self.recent_files.insert(0,filepath)

        PrintHelper.debugPrint(f'editor ----- add file to recent:{self.recent_files}')


    def show_recent_files(self):

        self.recent_menu.clear()

        actions = []
        for filepath in self.recent_files:
            action = QAction(filepath,self)
            action.triggered.connect(partial(self.load_recent_graph,filepath))
            actions.append(action)

        if len(actions)>0:
            self.recent_menu.addActions(actions)
        else:
            no_recent = QAction('No recent file.',self)
            no_recent.setDisabled(True)
            self.recent_menu.addAction(no_recent)

        self.recent_menu.addSeparator()
        self.recent_menu.addAction(self.clearMenuAction)

    def clear_recent_files(self):
        self.recent_files = []
        self.show_recent_files()


    def save_all_graph(self):
        # if self.tabs:
        for i in range(self.tabWidget.count()):
            view = self.tabWidget.widget(i)
            self.save_graph_in_view(view,i)

    def save_graph(self):

        if not self.editor.save_graph_in_current_view():
            filepath, filetype = QFileDialog.getSaveFileName(
                self, '保存为', os.getcwd(), 'Visual Graph File (*.vgf)')

            if filepath == '':
                PrintHelper.debugPrint('文件选择已取消')
                return

            self.tabWidget.setTabText(self.tabWidget.currentIndex(),os.path.basename(filepath))

            self.add_to_recent_file(filepath)
            self.record_graph_opened(filepath,self.tabWidget.currentIndex())
            self.editor.save_graph_in_current_view_as(filepath)

    def save_graph_in_view(self,tabview,index):
        if not tabview.save_graph_in_current_view():
            filepath, filetype = QFileDialog.getSaveFileName(
                self, '保存为', os.getcwd(), 'Visual Graph File (*.vgf)')

            if filepath == '':
                PrintHelper.debugPrint('文件选择已取消')
                return

            self.tabWidget.setTabText(index,os.path.basename(filepath))

            self.add_to_recent_file(filepath)
            self.record_graph_opened(filepath,index)
            tabview.save_graph_in_current_view_as(filepath)


    # 将当前的graph另存为文件
    def save_graph_as(self):

        # 弹出对话框，选择文件夹以及保存文件的名字
        filepath,filetype = QFileDialog.getSaveFileName(self,'另存为',os.getcwd(),'Visual Graph File (*.vgf)')

        if filepath == '':
            PrintHelper.debugPrint('文件选择已取消')
            return

        self.tabWidget.setTabText(self.tabWidget.currentIndex(),os.path.basename(filepath))

        # 将当前选择的路径，传入要保存的file内
        self.add_to_recent_file(filepath)
        self.record_graph_opened(filepath,self.tabWidget.currentIndex())
        self.editor.save_graph_in_current_view_as(filepath)

    def dialog_open_graph(self):
        # 弹出对话框选择文件
        filepath,filetype = QFileDialog.getOpenFileName(self,'选择文件',os.getcwd(),'Visual Graph File (*.vgf)')

        if filepath == '':
            PrintHelper.debugPrint('文件选择已取消')
            return

        self.open_graph(filepath)


    def open_graph(self,filepath):

        self.add_to_recent_file(filepath)

        index = self.is_graph_opened(filepath)
        if index !=-1:
            self.tabWidget.setCurrentIndex(index)
            return

        # 当前的tab是不是没有存储，如果没有存储，则在当前的tab上进行load
        if self.editor.is_untitled_view():
            #创建一个新的tab，并将graphload到新的tab中
            self.add_a_tab(filepath)
        else:
            self.tabWidget.setTabText(self.tabWidget.currentIndex(),os.path.basename(filepath))

        self.record_graph_opened(filepath,self.tabWidget.currentIndex())
        self.editor.load_graph_to_current_view(filepath)
        self.refreshVariableTree()


    def record_graph_opened(self,filepath,index):
        self.opened_graphs[filepath] = index

    def record_graph_closed(self,index):

        for filepath,tab_index  in self.opened_graphs.items():
            if tab_index > index:
                self.opened_graphs[filepath] = tab_index-1

            elif tab_index ==index:
                self.opened_graphs[filepath] = -1


    def is_graph_opened(self,filepath):
        return self.opened_graphs.get(filepath,-1)

    def load_recent_graph(self,filepath):
        self.open_graph(filepath)

    # 退出
    def quit(self):
        QApplication.quit()


    # ###################标准输入输出流 ###############
    def onStdOutWritten(self,lines):

        if len(lines)==0:
            return

        self.logger_widget.show()
        self.showLoggerAction.setChecked(True)

        for text in lines:
            # if text == '':
            #     continue
            try:
                data = json.loads(text)

                if isinstance(data,dict):
                    color = data['color']
                    text = data['text']
                else:
                    text = str(text)
                    color = '#FFF'
            except:
                text = str(text)
                color = '#fff'

            self.logger_widget.log(text,color)

    def onStdErrWritten(self,text):
        # if text.strip() == '':
        #     return

        # data = json.loads(text)
        # if isinstance(data, dict):
        #     color = data['color']
        #     text = data['text']
        # else:
        #     text = str(text)
        #     color = '#f44'

        # self.logger_widget.show()
        # self.showLoggerAction.setChecked(True)
        # self.logger_widget.log(text, color)

        logging.info(text)

class VisualGraphTab(QWidget):

    def __init__(self,parent=None):

        super().__init__(parent)
        self.setup_editor()
        self.setup_menu()
        self.undo_stack = QUndoStack(self)
        self.id = np.random.randint(1,10000)

    # 设置窗口，只需要初始化view
    def setup_editor(self):
        # 窗口位置以及大小
        self.layout = QBoxLayout(QBoxLayout.LeftToRight,self)
        self.layout.setContentsMargins(0,0,0,0)

        # 初始化scence
        self.scene = VisualGraphScene(self)
        self.view = VisualGraphView(self.scene,self)
        self.layout.addWidget(self.view)

    # 聚焦于节点的中心
    def center_graph(self):
        if len(self.view._nodes)>0:
            pos_x = []
            pos_y = []
            for node in self.view._nodes:

                pos = node.scenePos()
                pos_x.append(pos.x())
                pos_y.append(pos.y())

            self.view.centerOn(QPointF(np.mean(pos_x),np.mean(pos_y)))

    # 将全局鼠标位置映射为场景为止
    def map_mouse_to_scene(self):
        return self.view.mapToScene(
            self.view.mapFromGlobal(QCursor.pos()))

    #################### 编辑操作 ####################
    # 将某个action添加到栈内
    def add_action_to_stack(self,command_text,command:QUndoCommand):
        self.undo_stack.beginMacro(command_text)
        # push的时候会自动的执行一次redo,不需要自己去执行
        self.undo_stack.push(command)
        self.undo_stack.endMacro()

    #  撤销
    def undo_edit(self):
        PrintHelper.debugPrint(f'editor {self.id}  undo {self.undo_stack.isActive()}')
        self.undo_stack.undo()
    #  恢复
    def redo_edit(self):
        PrintHelper.debugPrint(f'editor {self.id}  redo')
        self.undo_stack.redo()

    # 将选中的节点转化成json字符串
    def stringfy_selected_items(self):

        if len(self.get_selected_items())>0:
            return self.view.stringfy_items(self.get_selected_items())
        else:
            return None

    #  粘贴命令
    def paste_selected_items(self,graph):
        pasteCommand = PasteCommand(self,graph)
        self.add_action_to_stack('Paste Items',pasteCommand)

    # 剪切命令
    def cut_items(self):
        command = CutCommand(self)
        self.add_action_to_stack('cut items',command)

    # 使用剪切命令完成删除
    def del_items(self):
        command = CutCommand(self)
        self.add_action_to_stack('del items',command)

    # 删除selected nodes
    def delete_selected_nodes(self):
        for item in self.get_selected_items():
            if isinstance(item, GraphNode):
                item.remove_self()

    # 获得当前选中的项目
    def get_selected_items(self):
        return self.view.get_selected_items()

    #  deselect 当前选中的项目
    def unselected_selected_items(self):
        return self.view.unselected_selected_items()

    #  选中指定项目
    def select_items(self,items):
        for item in items:
            item.setSelected(True)

    #  将指定项目group
    def group_items(self):
        # 获得选中的nodes
        command = GroupCommand(self)
        self.add_action_to_stack('group items',command)

    #  将指定项目group
    def ungroup_items(self):
        # 获得选中的nodes
        command = UnGroupCommand(self)
        self.add_action_to_stack('ungroup items',command)

    def add_group(self,group):
        self.view.add_node_group_obj(group)

    def remove_group(self,group):
        self.view.delte_node_group(group)

    # ################### 文件操作 ################

    # 判断当前tab是不是未命名
    def is_untitled_view(self):
        return False if self.view.get_saved_path() is None else True

    # 将当前tab进行保存
    def save_graph_in_current_view(self):
        return self.view.save_graph_directly()

    # 将当前tab进行另存为
    def save_graph_in_current_view_as(self,path):
        self.view.save_graph_to_file(path)

    # 将对应路径的graph加载到当前的tab内
    def load_graph_to_current_view(self,path):
        self.view.load_graph(path)
        self.center_graph()

    # 添加节点
    def add_node(self,node:GraphNode):
        self.view.add_graph_node(node,pos=None)

    # 添加边
    def add_edge(self,edge:NodeEdge):
        self.view.readd_edge(edge)


    ##############运行操作
    def run_graph(self):
        self.view.run_graph()

    def run_graph_in_back(self):
        self.view.run_graph_in_back()

    #  右键点击，添加右键菜单 TODO 将该功能改到window的context menu功能内
    def mousePressEvent(self, event: QMouseEvent) -> None:

        if event.button() == Qt.RightButton and event.modifiers() !=Qt.ControlModifier:
            self.show_menu(event.pos())

        super().mousePressEvent(event)


    # def contextMenuEvent(self, event) -> None:
    #     self.show_menu(event.pos())



    # ########## 设置菜单栏
    def setup_menu(self):
        self.refresh_menu_data()
        self._menu_widget = NodeListWidget(self._menu_data,self)
        self._menu_widget.setGeometry(0,0,200,300)
        self.view.setMenuWidget(self._menu_widget)
        self.hide_menu()

        self._menu_widget.itemDoubleClicked.connect(self.view.node_selected)


    def hide_menu(self):
        self._menu_widget.setVisible(False)

    def show_menu(self,pos):
        self.refresh_menu_data()
        self._menu_widget.refresh_tree(self._menu_data)
        self._menu_widget.setGeometry(pos.x(),pos.y(),200,300)
        self._menu_widget.show()


    def refresh_menu_data(self):
        lib_data = VG_ENV.get_nodelib_json_data()
        var_data = self.view.getVariableClsData()
        self._menu_data = {}
        self._menu_data.update(lib_data)
        self._menu_data.update(var_data)

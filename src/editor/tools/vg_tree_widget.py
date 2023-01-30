#coding:utf-8

from collections import defaultdict
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QTreeWidget, QTreeWidgetItem
from functools import partial
from PySide6.QtCore import Qt,Signal
from PySide6.QtGui import QCursor, QAction, QIcon
import json
from tools.QssLoader import QSSLoadTool
from vg_dtypes import VGDtypes


class NodeListWidget(QTreeWidget):
    '''
        data = {
            'package name1':{
                'node title':NodeCls,

            }
        }   

        
        data = {
            
            'Basic Operation':{
                'Add':AddNode
            },
            'Control Structure':{
                'Branch':BranchNode
            }

        } 
    
    '''
    def __init__(self, data, parent=None, dragEnabled=False):
        super().__init__(parent)

        self.data = data

        # self.resize(200,300)
        self.setColumnCount(1)
        self.setHeaderHidden(True)

        self.construct_tree()
        QSSLoadTool.setStyleSheetFile(self, './src/editor/qss/tree.qss')

        self.setObjectName('MenuTree')

        self.pos = None

        # 默认情况下QWidget是一个组件，不是window， window的话就是屏幕位置
        # self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        if dragEnabled:
            self.setDragEnabled(True)
            self.viewport().setAcceptDrops(False)
            self.setDragDropMode(QTreeWidget.DragDrop)
            self.setDropIndicatorShown(True)

            rootItem = self.invisibleRootItem()
            rootItem.setFlags(rootItem.flags() ^ Qt.ItemIsDropEnabled)

    def startDrag(self, supportedActions) -> None:

        self.dragged_item = self.itemAt(self.mapFromGlobal(QCursor.pos()))
        return super().startDrag(supportedActions)

    def getDraggedItem(self):
        return self.dragged_item

    def refresh_tree(self, data):
        self.data = data
        self.construct_tree()

    def construct_tree(self, filter=None):
        self.clear()

        items = []
        for pkg_name in self.data.keys():
            item = QTreeWidgetItem([pkg_name])
            flags = item.flags()
            flags ^= Qt.ItemIsSelectable
            flags ^= Qt.ItemIsDropEnabled
            item.setFlags(flags)
            for node_title in self.data[pkg_name].keys():
                node_item = QTreeWidgetItem([node_title])
                node_item.setData(0, Qt.UserRole,
                                  self.data[pkg_name][node_title])
                node_item.setFlags(node_item.flags() ^ Qt.ItemIsDropEnabled)
                item.addChild(node_item)

            items.append(item)

        self.insertTopLevelItems(0, items)


class ItemTreeWidget(QTreeWidget):


    itemAdded = Signal(QTreeWidgetItem)
    itemRenamed = Signal(str,QTreeWidgetItem)
    itemDeleted = Signal(QTreeWidgetItem)
    itemRegrouped = Signal(QTreeWidgetItem)

    itemSelected = Signal(QTreeWidgetItem)


    def __init__(self, parent=None):
        super().__init__(parent)

        # item类型
        self.item_types = ['General', 'Group', 'Item']
        self.item_names = defaultdict(set)

        self.setColumnCount(1)
        self.setHeaderHidden(True)
        QSSLoadTool.setStyleSheetFile(self, './src/editor/qss/tree.qss')

        # self.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.defaultGroup = None
        self.construct()

        # 打开拖动
        self.setDragEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.showDropIndicator()
        self.setDragDropMode(QTreeWidget.InternalMove)

        # 根节点不接受拖动
        rootItem = self.invisibleRootItem()
        rootItem.setFlags(rootItem.flags() ^ Qt.ItemIsDropEnabled)

        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # 连接action,传递的是一个Qpoint的参数
        self.customContextMenuRequested.connect(self.showCustomMenu)

        self.itemPressed.connect(self.onItemPressed)

        # 检测重命名
        self.itemChanged.connect(self.onItemChanged)

    def construct(self):

        self.clear()
        self.defaultGroup = None
        self.item_names = defaultdict(set)
        '''

            'group name':[
                'variable name1',
                'variable name2'
            ]

            'Default':['width','height'],
            'Graph':[''],
            'Visualization':['']


            'group name':{
               'childs':[],
               'IsDefault':True
            }
        
        '''

        data = {
            'Group1': [
                {
                    'name': 'width',
                    'type': 'int'
                },
                {
                    'name': 'height',
                    'type': 'int'
                }  #变量对象
            ],
            'Group2': [
                {
                    'name': 'angle',
                    'type': 'int'
                },
                {
                    'name': 'length',
                    'type': 'int'
                }  #变量对象
            ]
        }

        # 添加一个默认节点是不可以删除的
        if self.defaultGroup is None:
            self.defaultGroup = self.initAGroup('Default')
            self.defaultGroup.setFlags(self.defaultGroup.flags()
                                    ^ Qt.ItemIsEditable)
            self.defaultGroup.setExpanded(True)
            self.insertTopLevelItem(0,self.defaultGroup)


    def initAGroup(self, group_name):

        if group_name == 'Default' and self.defaultGroup is not None:
            return self.defaultGroup

        self.item_names[self.item_types[1]].add(group_name)
        item = QTreeWidgetItem([group_name])
        item.setFlags(Qt.ItemIsEditable | Qt.ItemIsSelectable
                      | Qt.ItemIsDropEnabled | item.flags())
        # 一级节点只接受新的子节点，不能拖动
        item.setFlags(item.flags() ^ Qt.ItemIsDragEnabled)
        item.setData(0, Qt.UserRole, {'IsGroup': True, 'name': group_name})
        return item

    def initAItem(self, data):
        self.item_names[self.item_types[2]].add(data['name'])
        subitem = QTreeWidgetItem([data['name']])
        if data['type']=='func':
            subitem.setIcon(0, QIcon('./src/editor/icons/func.png'))
        else:
            subitem.setIcon(0,VGDtypes.get_cls_icon(data['type']))
        subitem.setFlags(Qt.ItemIsEditable | Qt.ItemIsSelectable
                         | Qt.ItemIsDragEnabled | subitem.flags())
        # 子节点不接受拖动形成新的子节点
        subitem.setFlags(subitem.flags() ^ Qt.ItemIsDropEnabled)
        subitem.setData(0, Qt.UserRole, data)

        return subitem

    def showCustomMenu(self, qPoint):
        item = self.itemAt(qPoint)
        # 创建菜单
        # TODO 绑定每一个动作
        # TODO 每一次变动需要对数据进行保存
        # TODO 数据加载
        menu = QMenu(self, self)
        self.setupMenuActions(menu, item)
        menu.exec(self.mapToGlobal(qPoint))

    def check_item_type(self, item):

        if item is None:
            item_type = self.item_types[0]
        else:
            data = item.data(0, Qt.UserRole)

            if data.get('IsGroup', False):
                item_type = self.item_types[1]
            else:
                item_type = self.item_types[2]

        return item_type

    def setupMenuActions(self, menu: QMenu, item: QTreeWidgetItem,action_labels = ['New Group','New Item','Rename','Delete'] ):

        # 无论在哪里点击都会在树的结尾进行添加
        newGroupAction = QAction(action_labels[0], menu)
        newGroupAction.triggered.connect(self.newGroup)

        # 如果点击的是Group则加入该Group的Item
        menu_type = self.check_item_type(item)
        if menu_type == 'Group':
            group = item
            index = group.childCount()

        # 如果是Item的话，则在点击的item后面进行添加
        elif menu_type == 'Item':
            group = item.parent()
            index = group.indexOfChild(item) + 1

        else:
            group = self.defaultGroup
            index = group.childCount()

        newItemAction = QAction(action_labels[1], menu)
        # TODO data是需要根据实际需求改的
        newItemAction.triggered.connect(
            partial(self.newItem,
                    group,
                    index,
                    data={
                        'name': f'{self.generate_name(self.item_types[2])}',
                        'type': VGDtypes.Float,
                        'group': group.text(0)
                    }))

        renameAction = QAction(action_labels[2], menu)
        renameAction.triggered.connect(partial(self.renameItem, item))

        deleteAction = QAction(action_labels[3], menu)
        deleteAction.triggered.connect(partial(self.delteItem, item))


        menu.addAction(newGroupAction)
        menu.addAction(newItemAction)
        menu.addAction(renameAction)
        menu.addAction(deleteAction)

    def onItemPressed(self, item, column):
        self.selected_item = item
        self.selected_item_data = item.data(0, Qt.UserRole)

        if self.check_item_type(item) == 'Item':
            self.itemSelected.emit(item)

    # 创建group
    def newGroup(self):
        # 初始化一个groupitem
        groupItem = self.initAGroup(self.generate_name(self.item_types[1]))
        # 添加至tree
        self.addTopLevelItem(groupItem)
        # 设置为可编辑
        self.editItem(groupItem)

    # 创建group下的Item
    # TODO 需要一个data参数，是需要在添加的时候进行定义，例如类型，名字等等
    def newItem(self, group: QTreeWidgetItem, index, data):
        # data需要传入
        item = self.initAItem(data)
        group.insertChild(index, item)
        # 打开group
        group.setExpanded(True)
        # 编辑新添加的item
        self.editItem(item)

        self.saveTreeAsDict()

        self.itemAdded.emit(item)

    def generate_name(self, type, default_item_labels = ['Group','Item']):

        if type == self.item_types[1]:
            prefix = default_item_labels[0]
        elif type == self.item_types[2]:
            prefix = default_item_labels[1]
        else:
            prefix = default_item_labels[0]

        index = 1
        name = f'{prefix}-{index}'
        while self.isNameExist(name, type):
            name = f'{prefix}-{index}'
            index += 1

        return name

    # 删除节点及其子节点
    def delteItem(self, item):

        if item == self.defaultGroup:
            print('Default group cannot be deleted.')
            return

        item_type = self.check_item_type(item)
        if item_type == 'Item':
            item.parent().removeChild(item)
        elif item_type == 'Group':
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
        else:
            pass

        self.saveTreeAsDict()

        self.itemDeleted.emit(item)

    # 重命名
    def renameItem(self, item):
        if item != self.defaultGroup and item != None:
            self.editItem(item)

    def onItemChanged(self, item: QTreeWidgetItem, column):
        # 在重命名的时候进行一些操作
        # 判断当前名字是否和已有的item重复，如果重复则进行改正
        current_name = item.text(column)
        pre_name = item.data(column, Qt.UserRole)['name']

        item_type = self.check_item_type(item)

        if current_name == pre_name:
            return

        # 如果名字已存在，那么设为原来的名字
        if self.isNameExist(current_name, item_type):
            item.setText(column, pre_name)
            print('same name exists.')
        else:
            data = item.data(column, Qt.UserRole)
            data['name'] = current_name
            item.setData(column, Qt.UserRole, data)

            # 加入到全局变量
            self.item_names[item_type].add(current_name)
            self.item_names[item_type].remove(pre_name)

            # 如果是Group 就是Item需要改变Group
            if item_type == 'Group':
                for index in range(0,item.childCount()):
                    childItem = item.child(index)
                    data = childItem.data(0,Qt.UserRole)
                    data['group'] = item.text(0)
                    childItem.setData(0,Qt.UserRole,data)
                    self.itemRegrouped.emit(childItem)
            else:
                self.itemRenamed.emit(pre_name,item)

        self.saveTreeAsDict()

    # 判断该名称是否存在
    def isNameExist(self, name, item_type):
        return name in self.item_names[item_type]

    def dropEvent(self, event) -> None:

        super().dropEvent(event)
        self.saveTreeAsDict()
        self.dragged_item.parent().setExpanded(True)
        data = self.dragged_item.data(0, Qt.UserRole)
        data['group'] = self.dragged_item.parent().text(0)
        self.dragged_item.setData(0, Qt.UserRole, data)
        self.itemRegrouped.emit(self.dragged_item)
        self.dragged_item = None

    def startDrag(self, supportedActions) -> None:

        self.dragged_item = self.itemAt(self.mapFromGlobal(QCursor.pos()))
        return super().startDrag(supportedActions)

    def getDraggedItem(self):
        return self.dragged_item

    # ############ 加载与保存树
    def loadTreeFromDict(self, data):
        self.construct()
        items = []
        # 以及树的名字是group name
        for group_name in data.keys():
            item = self.initAGroup(group_name)
            # item.setData(0,Qt.UserRole,data[group_name])
            for var in data[group_name]:
                item.addChild(self.initAItem(var))

            items.append(item)

        self.insertTopLevelItems(0, items)
        if self.defaultGroup.childCount()>0:
            self.defaultGroup.setExpanded(True)

    def loadTreeFromJsonFile(self, filePath):
        data = json.loads(open(filePath).read())
        self.loadTreeFromDict(data)

    # 遍历当前树，生成一个新的json文件
    def saveTreeAsDict(self):
        data = {}
        # 首先获得TopLevel的Item
        top_level_item_count = self.topLevelItemCount()
        for i in range(top_level_item_count):
            group = self.topLevelItem(i)

            childs = []
            child_count = group.childCount()
            for j in range(child_count):
                subitem = group.child(j)
                item_data = subitem.data(0, Qt.UserRole)
                childs.append(item_data)

            data[group.text(0)] = childs

        return data

    def saveTreeToJsonFile(self, filePath):
        data = self.saveTreeAsDict()
        open(filePath, 'w').write(json.dumps(data))


class VariableTreeWidget(ItemTreeWidget):

    def setupMenuActions(self, menu: QMenu, item: QTreeWidgetItem, action_labels=['New Group', 'New Variable', 'Rename', 'Delete']):
        return super().setupMenuActions(menu, item, action_labels)

    def generate_name(self, type, default_item_labels=['Group', 'Variable']):
        return super().generate_name(type, default_item_labels)


class FuncTreeWidget(ItemTreeWidget):

    def setupMenuActions(
            self,
            menu: QMenu,
            item: QTreeWidgetItem,
            action_labels=['New Group', 'New Function', 'Rename', 'Delete']):
        return super().setupMenuActions(menu, item, action_labels)

    def generate_name(self, type, default_item_labels=['Group', 'Function']):
        return super().generate_name(type, default_item_labels)
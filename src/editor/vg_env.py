#coding:utf-8
from collections import defaultdict,OrderedDict
import functools
from platform import node
from vg_dtypes import VGDtypes
from tools.vg_tools import PrintHelper

import nodes
import structs
import inspect
import sys
from vg_node import Node,VGNode
from vg_node_port import NodeInput,NodeOutput


import os

class VG_ENV:

    # 这个是clasname对应cls
    clsname_cls = {}
    # node的类列表
    node_cls_list = []
    # table strcut 列表
    table_struct_list = []

    @staticmethod
    def register_node_cls_to_lib(nodeclas):

        if isinstance(nodeclas, list):
            VG_ENV.node_cls_list.extend(nodeclas)
        else:
            VG_ENV.node_cls_list.append(nodeclas)

        VG_ENV.node_cls_list = list(set(VG_ENV.node_cls_list))

    @staticmethod
    def register_struct_cls_to_lib(struct):
        '''注册一个struct'''
        VG_ENV.table_struct_list.append(struct)
        VG_ENV.table_struct_list = list(set(VG_ENV.table_struct_list))

    @staticmethod
    def initialize_node_env():

        VG_ENV.load_submodules(structs)
        sub_modules =VG_ENV.load_submodules(nodes)
        # inspect可以对已经导入的module进行查看
        for module_name in sorted(sub_modules):
            # 根据modules分别获得module文件内的class
            for cls_name,cls in inspect.getmembers(sys.modules[module_name],inspect.isclass):
                if cls_name != 'Node' and issubclass(cls,Node) and cls.stored:
                    VG_ENV.add_cls_to_lib(
                        f'{sys.modules[module_name].__name__}.{cls_name}', cls)

    @staticmethod
    def load_submodules(top_module):
        ''' 将对应的文件加下面的module全部引入 '''
        sub_modules = []
        # inspect只能查看Live Modules，就是必须是已经import的modules
        # 获得nodes的路径,获得该路径下的文件名，并导入
        module_folder = os.path.dirname(top_module.__file__)
        module_name = top_module.__name__
        for module in os.listdir(module_folder):
            if not module.endswith('.py') or module == '__init__.py':
                continue
            __import__(f'{module_name}.{module[:-3]}', locals(), globals())
            sub_modules.append(f'{module_name}.{module[:-3]}')

        return sub_modules

    @staticmethod
    def get_cls_by_name(cls_name):
        return VG_ENV.clsname_cls.get(cls_name,None)

    @staticmethod
    def add_cls_to_lib(cls_name,cls):
        VG_ENV.clsname_cls[cls_name] = cls
        VG_ENV.register_node_cls_to_lib(cls)


    @staticmethod
    def get_register_node_clses():
        return VG_ENV.node_cls_list

    def get_register_struct_clses():
        return VG_ENV.table_struct_list


    @staticmethod
    def get_nodelib_json_data():
        # print('cls num:' , len(VG_ENV.get_register_node_clses()))
        data = defaultdict(dict)
        for cls in VG_ENV.get_register_node_clses():

            pkg_name = cls.package_name
            node_title = cls.node_title
            data[pkg_name][node_title] = cls

        sorted_data = {}

        for pkg in data.keys():
            sorted_data[pkg] = OrderedDict(sorted(data[pkg].items()))

        return OrderedDict(sorted(sorted_data.items()))


# 定义一个decorator
def register_node(name=None,input=None,output={},package='Default',is_pure=False):
    def wrapper(func,*args):

        package_name = package

        func_name = func.__name__
        func_name = func_name.replace('.','_').replace(' ','_')
        node_title = name if name is not None else func_name
        node_description = func.__doc__ if func.__doc__ is not None else ''

        # print(node_title)
        # 注册方法
        try:
            node_cls = type(f'{node_title}', (VGNode, ), {
                    'package_name': package_name,
                    'node_title': node_title,
                    'node_description': node_description,
                    'is_pure':is_pure,
                    'params':input,
                    'returns':output,
                    'func':func
                })

            # 这里创建的module会是 vg_env.class_name，但是并没有vg_env中并没有class_name这个属性，因此需要动态添加进去
            # print(node_cls.__name__)
            # print(node_cls.__module__)
            # 将创建的module
            setattr(sys.modules[node_cls.__module__], node_cls.__name__,node_cls)
            cls_name = node_cls.__module__+'.'+node_cls.__name__
            VG_ENV.add_cls_to_lib(cls_name,node_cls)

        except ValueError as e:
            PrintHelper.printError(e)

    return wrapper


class TableStruct:
    columns:list = None

# struct的修饰器
def register_struct(cls):

    if issubclass(cls,TableStruct):
        VG_ENV.register_struct_cls_to_lib(cls)


# 使用struct的修饰器
def use_struct(cls):
    '''这个方法需要注册所有的struct，生成node'''
    for  struct_cls in VG_ENV.table_struct_list:
        try:
            # 创建需要struct的子类，并制定struct_cls
            node_cls = type(f'{struct_cls.__name__}_{cls.__name__}',(cls,),{
                'node_title':f'Split Table ({struct_cls.__name__})',
                'table_class':struct_cls
            })
            # 动态将该子类添加到Module上
            setattr(sys.modules[node_cls.__module__], node_cls.__name__,
                node_cls)
            cls_name = node_cls.__module__ + '.' + node_cls.__name__
            VG_ENV.add_cls_to_lib(cls_name, node_cls)

        except ValueError as e:
            PrintHelper.printError(e)


def use_dtypes(cls):
    '''class注册所有类型'''
    for dtype in VGDtypes.dtypes:

        try:
            # 创建需要struct的子类，并制定struct_cls
            node_cls = type(
                f'{cls.__name__}_{dtype.__name__}', (cls, ), {
                    'node_title':f'{cls.node_title} ({dtype.__name__})',
                    'dtype': dtype
                })
            # 动态将该子类添加到Module上
            setattr(sys.modules[node_cls.__module__], node_cls.__name__,
                    node_cls)
            cls_name = node_cls.__module__ + '.' + node_cls.__name__
            VG_ENV.add_cls_to_lib(cls_name, node_cls)

        except ValueError as e:
            PrintHelper.printError(e)

#coding:utf-8

from struct import pack
import sys
from tools.vg_tools import PrintHelper

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes

from vg_config import NodeConfig
from vg_env import register_node,TableStruct, use_struct

import pandas as pd



class TableReader(Node):

    package_name = 'Table'
    node_title = 'Read CSV From File'
    node_description = '读取CSV file成为Dataframe'

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_type='data',pin_class=VGDtypes.String,pin_name='File Path'),
        NodeInput(pin_type='data',pin_class=VGDtypes.String,pin_name='Seperator',default_value=','),
        NodeInput(pin_type='data',pin_class=VGDtypes.Bool,pin_name='dropNa')
    ]

    output_pins = [
        NodeOutput(pin_type='exec'),
        NodeOutput(pin_type='data',pin_class=VGDtypes.Table,pin_name='table')
    ]

    def run_node(self):
        filepath:str = self.input(1)

        if not filepath.endswith('csv'):
            raise ValueError('输入文件不是CSV文件！')

        seperator = self.input(2)
        # 将csv文件读取为dataframe
        table = pd.read_csv(filepath,sep=seperator,encoding='utf-8')
        if self.input(3):
            table = table.dropna()
        # 设置到输出
        self.output(1,table)
        # 执行
        self.exec_output(0)

class TableHeader(Node):

    package_name = 'Table'
    node_title = 'Headers'
    node_description = '读取table的Headers'

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_type='data',pin_class=VGDtypes.Table,pin_name='Table')
    ]

    output_pins = [
        NodeOutput(pin_type='exec'),
        NodeOutput(pin_type='data',pin_class=VGDtypes.Array,pin_name='Headers')
    ]

    def run_node(self):
        table = self.input(1)
        self.output(1,table.columns)
        self.exec_output(0)

class TableSeries(Node):

    package_name = 'Table'
    node_title = 'Get Series (Name)'
    node_description = '获得一个column'

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_type='data',pin_class=VGDtypes.Table,pin_name='Table'),
        NodeInput(pin_type='data', pin_class=VGDtypes.String, pin_name='Column Name')
    ]

    output_pins = [
        NodeOutput(pin_type='exec'),
        NodeOutput(pin_type='data',pin_class=VGDtypes.Column, pin_name='Column')
    ]


    def run_node(self):
        table = self.input(1)
        column = self.input(2)

        if not column in table.columns:
            raise ValueError('Column Name不存在！')
        else:
            self.output(1,table[column])
            self.exec_output(0)

@use_struct
class SplitTable(Node):
    stored = False

    package_name = 'Table'
    node_title = 'Split Table'
    node_description = '分解columns'
    # 需要去注册class
    table_class:TableStruct = None

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_type='data', pin_class=VGDtypes.Table, pin_name='Table')
    ]

    def __init__(self):

        if self.table_class is None:
            raise ValueError('SplitTable Node没有指定表格的结构体！')

        self.output_pins = [
            NodeOutput(pin_type='exec')
        ]
        for column in self.table_class.columns:
            self.output_pins.append(NodeOutput(pin_type='data',pin_name=column,pin_class=VGDtypes.Column))

        super().__init__()


    def run_node(self):

        table = self.input(1)
        headers = table.columns

        if len(headers) != len(self.output_pins)-1:
            raise ValueError('SplitTable Node 输入的table与指定的table结构体大小不一致')

        for i in range(1,len(self.output_pins)):

            column_name = self.get_output_port_name(i)

            if column_name not in headers:
                raise ValueError(f'table中没有{column_name}列！')

            self.output(i,table[column_name])

        self.exec_output(0)

class CombineTable(Node):

    package_name = 'Table'
    node_title = 'Combine Columns'
    node_description = '合并多个列成为成的table'

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_type='data',
                  pin_class=VGDtypes.Column,
                  pin_name='Column1'),
        NodeInput(pin_type='data',
                  pin_class=VGDtypes.Column,
                  pin_name='Column2')
    ]

    output_pins = [
        NodeOutput(pin_type='exec'),
        NodeOutput(pin_type='data',pin_class=VGDtypes.Table,pin_name='Table')
    ]

    def run_node(self):

        column1 = self.input(1)
        column2 = self.input(2)

        if column1.size != column2.size:
            raise ValueError('多个列的长度不一致！')

        self.output(1,pd.DataFrame([column1,column2]))

        self.exec_output(0)


class MergeTable(Node):

    package_name = 'Table'
    node_title = 'Merge Table'
    node_description = '根据指定的key将两个table进行合并'

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_type='data',pin_class=VGDtypes.Table,pin_name='Table 1'),
        NodeInput(pin_type='data',pin_class=VGDtypes.Table,pin_name='Table 2'),
        NodeInput(pin_type='data',pin_class=VGDtypes.String,pin_name='key')
    ]

    output_pins = [
        NodeOutput(pin_type='exec'),
        NodeOutput(pin_type='data',pin_class=VGDtypes.Table,pin_name='New Table')
    ]

    def run_node(self):

        key = self.input(3)

        table1 = self.input(1)
        table2 = self.input(2)

        if key not in table1.columns:
            raise ValueError(f'table1 不包含列{key}！')

        if key not in table2.columns:
            raise ValueError(f'table2 不包含列{key}！')

        new_table = pd.merge(table1,table2,on=[key],how='inner')

        self.output(1,new_table)

        self.exec_output(0)


class Table(pd.DataFrame):

    @register_node(name='Table Size',input={'Table':VGDtypes.Table},output={'Size':VGDtypes.Integer},package='Table',is_pure=True)
    def tableSize(self:VGDtypes.Table)->VGDtypes.Integer:
        return self.size

    @register_node(name='Table Rows Count',input={'Table':VGDtypes.Table},output={'Rows Count':VGDtypes.Integer},package='Table',is_pure=True)
    def tableRowsCount(self):
        return self.shape[0]

    @register_node(name='Save Table',input={'Table':VGDtypes.Table,'File Path':VGDtypes.String},output={'Table':VGDtypes.Table},package='Table')
    def saveTable(self:VGDtypes.Table,FilePath:VGDtypes.String):
        self.to_csv(FilePath,index=False)
        return self

    @register_node(name='Print Table',input={'Table':VGDtypes.Table},output={'Table':VGDtypes.Table},package='Table')
    def printTable(table):
        print(tabulate(table, headers='keys', tablefmt='psql'))
        return table

    @register_node(name='N Rows of Table',
                   output={'Table': VGDtypes.Table},
                   package='Table')
    def headTable(table:VGDtypes.Table,num:VGDtypes.Integer):
        # print(tabulate(table, headers='keys', tablefmt='psql'))
        return table.head(num)
    
    @register_node(name='Sub Table',package='Table',output={'SubTable':VGDtypes.Table})
    def subTable(table:VGDtypes.Table,columns:VGDtypes.Array):
        return table[columns]

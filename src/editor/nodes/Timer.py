import sys

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes
from time import sleep
from vg_env import register_node
from vg_config import NodeConfig
from typing import TypeVar

KT = TypeVar('KT')
VT = TypeVar('VT')

NodeConfig.node_title_back_color['Timer'] = '#458899'


class SleepNode(Node):

    package_name = 'Timer'
    node_title = 'Delay'
    node_description = 'Sleep Node'

    input_pins = [
        NodeInput(pin_type='exec'),
        NodeInput(pin_name='secs', pin_class=VGDtypes.Float, pin_type='data')
    ]

    output_pins = [NodeOutput(pin_name='Completed', pin_type='exec')]

    def run_node(self):
        t = float(self.input(1))
        sleep(t)
        self.exec_output(0)


@register_node(name='Add',
               input={
                   'a': int,
                   'b': int
               },
               output={'sum': int},
               package='Timer',
               is_pure=True)
def Add(a: int, b: int) -> int:
    '''基础运算加法'''
    return a + b


@register_node(output={
                   'divide': int,
                   'mode': int
               },
               package='Timer',
               is_pure=True)
def Divide(a:int, b:int)->int:
    '''基础运算加法'''
    return a / b, a % b

@register_node(name='Print To Console',package='Timer',output={'str':str})
def PrintString(str:str)->str:
    print(str)

# TODO control的即多个分支的无法使用这种进行


# 这种类的执行方法是可以的
# class VGDict(dict):

#     key_cls = int
#     v_cls = int

#     def set_kv_class(self,keycls,vcls):
#         self.key_cls = keycls
#         self.v_cls = vcls

#     @register_node(name='get',output={'value':v_cls},package='Timer',is_pure=True)
#     def get(self:dict,key:key_cls):
#         return self.get(key,None)


class VDict(dict[KT,VT]):

    @register_node(name='get',
                   output={'value': KT},
                   package='Timer',
                   is_pure=True)
    def get(self: dict, key: VT)->VT:
        return self.get(key, None)

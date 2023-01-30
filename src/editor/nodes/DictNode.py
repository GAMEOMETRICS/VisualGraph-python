#coding:utf-8
import sys
from tools.vg_tools import PrintHelper

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes

from vg_env import register_node
from vg_config import NodeConfig
import json

NodeConfig.node_title_back_color['Dict Action'] = '#FFA500'


class JsonNode:

    @register_node(name='Load Json From File',
                   output={'json': VGDtypes.Dict},
                   package='Dict Action')
    def LoadJosnFromFile(path: str):

        return json.loads(open(path).read())

    @register_node(name='Load Json From String',
                   input={'json string': VGDtypes.String},
                   output={'json': VGDtypes.Dict},
                   package='Dict Action')
    def LoadJosnFromFile(jsonStr: str):
        return json.loads(jsonStr)


class DictNode:

    @register_node(name='Size (Dict)',output={'size':VGDtypes.Integer},package='Dict Action',is_pure=True)
    def dictSize(dic:VGDtypes.Dict):
        return len(dic.keys())
    
    @register_node(name='Keys (Dict)',output={'Keys':VGDtypes.Array},package='Dict Action',is_pure=True)
    def dictKeys(dic:VGDtypes.Dict):
        return list(dic.keys())
    
    @register_node(name='Get (Dict)',output={'value':VGDtypes.Class},package='Dict Action', is_pure=True)
    def dictGet(dic:VGDtypes.Dict,key:VGDtypes.String):
        return dic.get(key,None)
    
    @register_node(name='Set (Dict)',output={'dic':VGDtypes.Dict},package='Dict Action')
    def dictSet(dic:VGDtypes.Dict,key:VGDtypes.String,value:VGDtypes.Any):
        dic[key] = value
        return dic
    
    


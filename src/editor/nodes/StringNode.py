#ocoding:utf-8
import sys
from tools.vg_tools import PrintHelper

sys.path.append('..')
from vg_node_port import NodeInput, NodeOutput
from vg_node import Node
from vg_dtypes import VGDtypes

from vg_env import register_node
from vg_config import NodeConfig

NodeConfig.node_title_back_color['StringAction'] = '#800080'


class StringAction(str):

    @register_node(name='StartsWith',input={'target':VGDtypes.String,'prefix':VGDtypes.String},output={'Is':bool},package='StringAction')
    def StartsWith(self:VGDtypes.String,prefix:VGDtypes.String):

        return self.startswith(prefix)

    @register_node(name='Strip',input={'target':VGDtypes.String},output={'str':VGDtypes.String},package='StringAction')
    def Strip(self:VGDtypes.String):
        return self.strip()
    
    @register_node(name='Split',input={'target':VGDtypes.String,'seperator':VGDtypes.String},output={'Splits':VGDtypes.Array},package='StringAction')
    def Split(self:VGDtypes.String,seperator:VGDtypes.String):
        return self.split(seperator)
    
        

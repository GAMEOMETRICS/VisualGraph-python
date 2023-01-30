#coding:utf-8
'''
1 定义变量

2 变量管理



'''

from vg_dtypes import VGDtypes


class Variable:

    def __init__(self,name,VGType,value,group='Default',manager=None):

        self.name = name
        self.type = VGType
        self.value = value
        self.group = group

        self.manager:VariableManager = manager

    def setManager(self,manager):
        self.manager = manager

    def getManager(self):
        return self.manager

    def setName(self,name):
        if self.manager:
            self.manager.removeVariable(self.name)

            self.name = name
            self.manager.variables[name] = self
            # TODO 需要的是在所有值改变之前进行过滤的action的重用

    def getName(self):
        return self.name

    def setValue(self,value):
        self.value = value

    def getValue(self):
        return self.value

    def setType(self,dtype_name):
        dtype = VGDtypes.dtypes_clses[dtype_name]
        # 然后需要实例化
        dv = VGDtypes.get_default_value(dtype)
        self.setValue(dv)
        self.type = dtype

    def getType(self):
        return self.type

    def setGroup(self,group):
        self.group = group

    def getGroup(self):
        return self.group

    def reset(self):
        dv = VGDtypes.get_default_value(self.type)
        self.setValue(dv)
    
    @staticmethod
    def fromJson(json):
        dtype = VGDtypes.dtypes_clses[json['type']]
        return Variable(json['name'],dtype,json['value'],json['group'])

    def toJson(self):

        type_name = self.type
        if not isinstance(self.type, str):
            type_name = self.type.__name__
            dv = VGDtypes.get_default_value(self.type)

        return {'name':self.name,'type':type_name,'value':dv,'group':self.group}

    def __repr__(self) -> str:
        type_name = self.type
        if not isinstance(self.type,str):
            type_name = self.type.__name__
            dv = VGDtypes.get_default_value(self.type)

        return '{'+f'name:{self.name},type:{type_name},value:{dv},group:{self.group}'+'}'


class VariableManager:

    def __init__(self):
        self.variables:dict[str:Variable] = {}

    def clearVariable(self):
        self.variables = {}
    
    def resetAllVariables(self):
        for k,v in self.variables.items():
            v.reset()
    
    def getAllVariables(self):
        return self.variables

    def getVariable(self,name)->Variable:
        return self.variables[name]

    def getVariableValue(self,name):
        return self.getVariable(name).getValue()

    def setVariableValue(self,name,value):
        self.getVariable(name).setValue(value)

    def addVariable(self,variable:Variable):

        if self.isVariableExists(variable.getName()):
            print('变量名已存在，添加失败！')
        else:
            variable.setManager(self)
            self.variables[variable.getName()] = variable


    def removeVariable(self,name):
        self.variables[name] = None
        self.variables.pop(name)

    def renameVariable(self,preName,currentName):
        variable:Variable = self.variables[preName]
        # 这里已经完成了添加
        variable.setName(currentName)
        # self.removeVariable(preName)
        # self.addVariable(variable)

    def changeVariableType(self,name,dtype_name):
        # 首先获得dtype name对应的class
        self.getVariable(name).setType(dtype_name)

    def changeVariableGroup(self,name,group):
        self.getVariable(name).setGroup(group)

    def isVariableExists(self,name):
        if self.variables.get(name,None) is None:
            return False

        return True

    def toJson(self):
        json = []
        for _,variable in self.variables.items():
            json.append(variable.toJson())

        return json

    def loadFromJson(self,varList):
        self.clearVariable()
        for var in varList:
            dtype_name = var['type']
            dtype_cls = VGDtypes.dtypes_clses[dtype_name]
            dtype_dv = VGDtypes.get_default_value(dtype_cls)
            self.addVariable(Variable(var['name'],dtype_cls,dtype_dv,var['group']))
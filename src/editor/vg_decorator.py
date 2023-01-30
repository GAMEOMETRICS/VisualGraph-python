#coding:utf-8
'''
    定义本项目需要的decorator

    一种是方法的

    一种是类对象

'''

import functools
from vg_node import Node

def DecoTest(func):

    @functools.wraps(func)
    def inner(*args):
        print(func.__annotations__)
        return func(*args)

    return inner

class FUNC:

    def __init__(self,func):
        self.func = func 
    
    def __call__(self, *args, **kwds):
        
        def inner(self,*args,**kwds):

            self.func(*args,**kwds)

        return inner

class VGNODE:

    def __init__(self,func,name=None,input=None,output=None,package='Default'):

        self.name = name
        self.input = input
        self.output = output
        self.package = package
        self.func = func

        print(self.name,self.func.__name__)

    def register_node(self):
        # 首先生成Node
        node_cls =  type(f'{self.name}', (Node, ), {
            'package_name': self.package,
            'node_title': self.name,
            'node_description':self
        })


    def __call__(self,func):

        @functools.wraps(func)
        def wrapper(*args,**kwargs):

            return self.func(*args,**kwargs)

        return wrapper

def test(a,b)->str:
    '''haha'''

    return 'hah'


if __name__=='__main__':
    # test(1,1)
    # print(test.__name__,test.__doc__)
    # Add(1,1)
    # Divide(1,1)
    print(test.__annotations__)

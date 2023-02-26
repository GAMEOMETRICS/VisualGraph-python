## Visual Graph in python - dev branch
基于PySide6的python节点编辑器实现，目前只实现了基础功能。

`dev`是用来开发使用，稳定以后会推送到`main`分支。

### 1. 2023年任务列表

  - 重构代码结构
    - editor: 前台显示功能, graph、node绘制以及编辑，将node的绘制与运行分开。
    - compiler: graph的运行。
    - node_manager: 库管理。
    - plugin_manager
    - types 

  - editor
    - 简化editor 
    - 插件式变成
    - 自定义node的UI 

  - compiler
    - 异步运行graph 
    - graph的debug 
    - graph转换为python代码
    - 后台运行与进程管理

  - node_manager
    - node manager用于管理所有的节点库以及节点运行需要的环境问题
    - node基类，虽有的节点都必须继承该类
    - node的事件定义
  
  - type_manager
    - 类型管理 主要是管理整个项目的类型及其对应的class
  
### 2. 开发进度计划
  
  - 2023年3月份：editor的展示、编辑与运行完全分离，即任意一个新的graph的json文件，就算本地没有库，也可以进行展示。
    * editor重构，实习graph编辑与执行分离，graph、node显示完全基于json进行。
    * editor_config文件，记录editor的状态，例如浏览历史、保存状态等等。
    * 使用QDockWdiget对界面进行重构。
    
     




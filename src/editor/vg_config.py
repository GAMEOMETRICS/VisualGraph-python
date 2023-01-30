#coding:utf-8
'''
editor的一些可设置的项目

'''

class EditorConfig:

    editor_scene_background_color = '#212121'
    editor_scene_grid_normal_line_color = '#313131'
    editor_scene_grid_dark_line_color = '#151515'

    editor_scene_grid_normal_line_width= 1.0
    editor_scene_grid_dark_line_width = 1.5

    editor_scene_grid_size = 20
    editor_scene_grid_chunk = 10

    editor_scene_width = 32000
    editor_scene_height = 32000

    editor_node_title_font_size = 16
    editor_node_title_font = 'Arial'
    editor_node_pin_label_size = 14
    editor_node_pin_label_font = 'Consolas'


class NodeConfig:

    port_icon_size = 25

    node_title_back_color = {
        'Action Default':'#f5232e',
        'Basic Operation':'#88df00',
        'Node Converter':'#fa8b17',
        'Basic Control':'#4e90fe'
    }

class GroupConfig:

    group_title_bak_color = '#2db694'
    group_title_pen_color = '#ddd'
    group_title_font_size = 16
    group_title_font = 'Arial'
    group_content_bak_color = '#333333'


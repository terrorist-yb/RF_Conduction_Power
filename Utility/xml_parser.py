# -*- coding:utf-8 -*-
import xml.etree.ElementTree as ET


def get_tasklist():
    '''
    用于配置xml文件解析，返回制式以及对应的频段配置
    '''
    task_tree = ET.parse('Power.xml')
    root = task_tree.getroot()
    task_list = []
    for mobile_format in root:
        task = mobile_format.attrib
        task['configuration'] = []
        for configuration in mobile_format:
            task['configuration'].append(configuration.attrib)
        task_list.append(task)
    return task_list

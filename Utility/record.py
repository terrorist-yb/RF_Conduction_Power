# -*- coding:utf-8 -*-
###############################################################################
# Copyright (C), 2018, TP-LINK Technologies Co., Ltd.
#
# 作者：吴扬波
# 版本：V1.0
# 变更历史:
# 1，2018-08-20， 吴扬波——首次创建：DataRecorder类，用于数据记录
# 若引用或修改API，请保留API变更历史。
###############################################################################
import global_variable
import os
import xlsxwriter


class DataRecorder(object):
    '''
    用于数据记录
    '''

    def __init__(self):
        self.folder_name = global_variable.file_folder

    def record_result(self, result_file_name, configuration, power, current):
        '''
        将配置、测量功率、测量电流记录至目标文件。
        result_file_name：文件名；
        configuration：配置说明，字符串；
        power: 测量功率；
        current: 测量电流
        '''
        result_file_rounine = self.folder_name + '.\\' + result_file_name
        content = configuration + '\t' + str(power) + '\t' + str(current) + '\n'
        with open(result_file_rounine, 'a') as f:
            f.write(content)

    def save_xlsx(self):
        '''
        该方法用于将过程存储的txt文件汇总到excel文件，用于实例调用。
        '''
        self.save_to_xlsx(self.folder_name)

    @staticmethod
    def save_to_xlsx(folder_name=None):
        '''
        该方法用于将过程存储的txt文件汇总到excel文件，用于独立调用。
        '''
        file_list = os.listdir(folder_name)
        work_book = xlsxwriter.Workbook(folder_name + '\\result.xlsx', )
        bold = work_book.add_format({'bold': 1})

        for file_name in file_list:
            if not file_name.startswith('log'):
                # 创建sheet
                sheet = work_book.add_worksheet(file_name.split('.')[0])
                row = 0
                col = 0
                # 写表头
                for item in ['Configuration', 'Actual Power(dbm)', 'Current(mA)']:
                    sheet.write(row, col, item, bold)
                    col += 1

                # 按txt的行写入excel
                row = 1
                text_file = open(folder_name + '.\\' + file_name)
                for line in text_file.readlines():
                    col = 0
                    for item in line.strip().split('\t'):
                        try:
                            temp = float(item)
                            item = temp
                        except Exception, e:
                            str(e)
                        sheet.write(row, col, item)
                        col += 1
                    row += 1
                text_file.close()
        work_book.close()

# -*- coding:utf-8 -*-
###############################################################################
# Copyright (C), 2018, TP-LINK Technologies Co., Ltd.
#
# 作者：吴扬波
# 版本：V1.0
# 变更历史:
# 1，2018-08-20， 吴扬波——首次创建：TestCase类，用于执行传导业务电流测试用例
# 若引用或修改API，请保留API变更历史。
###############################################################################
from CMW500 import cmw500 as cmw
from DCSource import dcsource as dcsrc
from Utility import xml_parser, record, pylogger, global_variable
from datetime import datetime
import sys
import os


class TestCase(object):
    '''
    TestCase类，用于执行传导业务电流测试用例
    '''

    def __init__(self):

        # 创建用例执行文件夹
        case_dir = sys.path[0]
        case_folder_name = case_dir + '.\\' + datetime.now().strftime("%Y%m%d_%H%M%S")
        global_variable.file_folder = case_folder_name
        try:
            os.makedirs(case_folder_name)
        except Exception as e:
            print 'folder:%s existed!' % e

        self.logger = pylogger.setup_logger(self.__class__.__name__)
        # 创建数据记录器
        self.data_recorder = record.DataRecorder()
        # 获得仪器控制引用
        self.cmw500, self.dc_source = self.init_instr()

    def init_instr(self):
        '''
        根据仪器地址获取仪器控制引用，并进行初步设置
        '''
        # 连接CMW500
        cmw500 = cmw.CMW500('192.168.2.10')
        # 在仪器界面上显示指令流
        cmw500.start_trace()
        # 设置信号路由
        cmw500.set_signal_routing('1', '1')
        # 配置线损表
        cmw500.set_correction_table('800', '0.4', '1800', '0.6')

        # 连接DC Source
        dc_source = dcsrc.DCSource('GPIB0::15::INSTR')
        # 配置电源电压
        dc_source.set_voltage(4)
        # 使能输出
        dc_source.enable_output()

        return cmw500, dc_source

    def run_lte_task(self, configuration):
        '''
        该方法用于执行LTE传导业务电流测试用例
        configuration：需要遍历的不同配置列表
        '''
        # 实例化CMW500的LTE模块
        self.cmw500.init_lte()

        is_first_loop = True
        # 遍历配置列表中的配置项
        for item in configuration:
            # 配置频段、信道、带宽
            self.cmw500.lte.set_downlink_channel(item['Band'], item['DlChannel'], item['Bandwidth'])
            # 配置RB数量、位置
            self.cmw500.lte.config_rmc(item['RbNumber'], item['RbPosition'])
            # 首次运行时设置下行信号强度、UE开环功率
            if is_first_loop:
                self.cmw500.lte.set_rsep_level('-85')
                self.cmw500.lte.set_openloop_power('20')
                # 使能输出
                self.cmw500.lte.enable_output()
                # 等待UE附着网络
                self.cmw500.lte.attach()
                is_first_loop = False

            # 建立RRC连接
            self.cmw500.lte.connect_rrc()

            # 遍历需要测试的上行功率，并测量电流
            power_list = ['0', '10', '25']
            for target_power in power_list:
                self.cmw500.lte.set_closeloop_power(target_power)
                actual_power = self.cmw500.lte.measure_average_tx_power()
                if self.dc_source.check_current_stability(60):
                    current = self.dc_source.measure_current(30)
                else:
                    current = 'Current unstable'
                config_info = '@Band:%s, DLCH:%s, BW:%sMHz, Power:%s dbm' % (
                    item['Band'], item['DlChannel'], item['Bandwidth'], target_power)
                self.data_recorder.record_result('LTE.txt', config_info, actual_power, current)

        # 测试结束后关闭输出
        self.cmw500.lte.disable_output()

    def run_wcdma_task(self, configuration):
        '''
        该方法用于执行WCDMA传导业务电流测试用例
        configuration：需要遍历的不同配置列表
        '''
        # 实例化CMW500的WCDMA模块
        self.cmw500.init_wcdma()

        is_first_loop = True
        # 遍历配置列表中的配置项
        for item in configuration:
            # 配置频段、信道、带宽
            self.cmw500.wcdma.set_downlink_channel(item['Band'], item['DlChannel'])
            # 首次运行
            if is_first_loop:
                self.cmw500.wcdma.set_downlink_power('-80')
                self.cmw500.wcdma.set_voice_connection()
                # 使能输出
                self.cmw500.wcdma.enable_output()
                # 等待UE注册网络
                self.cmw500.wcdma.register()
                is_first_loop = False

            # 建立CS域通话连接
            self.cmw500.wcdma.setup_cs_connection()

            # 遍历需要测试的上行功率，并测量电流
            power_list = ['0', '10', '25']
            for target_power in power_list:
                self.cmw500.wcdma.set_closeloop_power(target_power)
                actual_power = self.cmw500.wcdma.measure_average_tx_power()
                if self.dc_source.check_current_stability(60):
                    current = self.dc_source.measure_current(30)
                else:
                    current = 'Current unstable'
                config_info = '@Band:%s, DLCH:%s, Power:%s dbm' % (
                    item['Band'], item['DlChannel'], target_power)
                self.data_recorder.record_result('WCDMA.txt', config_info, actual_power, current)

        # 测试结束后关闭输出
        self.cmw500.wcdma.disable_output()

    def run_gsm_task(self, configuration):
        '''
        该方法用于执行GSM传导业务电流测试用例
        configuration：需要遍历的不同配置列表
        '''
        # 实例化CMW500的GSM模块
        self.cmw500.init_gsm()

        is_first_loop = True
        # 遍历配置列表中的配置项
        for item in configuration:
            # 首次运行配置BCCH的频段、下行功率，并使能输出建立与UE的通话连接
            if is_first_loop:
                self.cmw500.gsm.set_bcch_downlink_channel('GSM850', '128')
                self.cmw500.gsm.set_tch_downlink_channel('128')
                self.cmw500.gsm.set_bcch_level('-80')
                self.cmw500.gsm.set_tch_level('-80')
                self.cmw500.gsm.enable_output()
                self.cmw500.gsm.synchronize()
                is_first_loop = False

            # 建立CS域连接，若已连接，则不再建立
            self.cmw500.gsm.setup_cs_connection()
            # 切换到不同的信道或频段，若和原来相同，则不切
            self.cmw500.gsm.handover(item['Band'], item['DlChannel'])

            # 控制UE以最大闭环功率输出，并测量电流
            if item['Band'] in ['DCS1800', 'PCS1900']:
                target_power = '0'
            else:
                target_power = '5'
            self.cmw500.gsm.set_tch_pcl(target_power)
            actual_power = self.cmw500.gsm.measure_average_tx_power()
            if self.dc_source.check_current_stability(60):
                current = self.dc_source.measure_current(30)
            else:
                current = 'Current unstable'
            config_info = '@Band:%s, DLCH:%s, Power:%s dbm' % (
                item['Band'], item['DlChannel'], target_power)
            self.data_recorder.record_result('GSM.txt', config_info, actual_power, current)

        # 测试结束后关闭输出
        self.cmw500.gsm.disable_output()

    def run(self):
        '''
        该方法用于依照GSM、WCDMA、LTE的顺序执行用例。
        '''
        try:
            task_func = [self.run_gsm_task, self.run_wcdma_task, self.run_lte_task]
            tasklist = xml_parser.get_tasklist()
            seq = [-1, -1, -1]
            for index, task in enumerate(tasklist):
                if not cmp(task['Format'], 'GSM'):
                    seq[0] = index
                elif not cmp(task['Format'], 'WCDMA'):
                    seq[1] = index
                elif not cmp(task['Format'], 'LTE_FDD'):
                    seq[2] = index
            for index, item in enumerate(seq):
                if cmp(item, -1):
                    task_func[index](tasklist[item]['configuration'])
        except Exception, e:
            self.logger.error(e)
            self.cmw500.stop_trace()

        self.data_recorder.save_xlsx()


if __name__ == '__main__':
    testcase = TestCase()
    testcase.run()

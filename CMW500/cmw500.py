# -*- coding:utf-8 -*-
###############################################################################
# Copyright (C), 2018, TP-LINK Technologies Co., Ltd.
#
# 作者：吴扬波
# 版本：V1.0
# 变更历史:
# 1，2018-08-20， 吴扬波——首次创建：CMW500类，用于CMW500通用参数设置等
# 若引用或修改API，请保留API变更历史。
###############################################################################

import visa
from Utility import pylogger
import lte
import time
import wcdma
import gsm
from datetime import datetime


class CMW500(object):
    '''
    CMW500类，用于CMW500通用参数设置等。
    '''

    def __init__(self, ip):
        '''
        初始化日志、仪器连接、复位
        '''
        self.logger = pylogger.setup_logger(self.__class__.__name__)

        # 与仪器通过VXI协议建立连接
        self._inst = self._connect(ip)
        self.reset()

        # 射频物理链路实例变量
        self.converter = ''
        self.connector = ''

    def start_trace(self):
        '''
        该方法用于与配置仪器调试相关参数，并启动调试。
        启动调试后，仪器的面板上会显示输入、返回的SCPI指令流；
        并在调用stop_trace方法后，将指令流保存于仪器的Log文件夹中，文件名为PC端的日期。
        '''
        self._inst.write('SYSTEM:DISPlay:UPDate OFF')
        self._inst.write('TRACe:REMote:MODE:DISPlay:CLEar')
        self._inst.write('TRACe:REMote:MODE:DISPlay:ENABle LIVE')
        self._inst.write('''TRACe:REMote:MODE:FILE1:NAME "@LOG\%s\conduction.xml"'''
                         % datetime.now().strftime("%Y%m%d_%H%M%S"))
        self._inst.write('TRACe:REMote:MODE:FILE1:ENABle ON')

    def stop_trace(self):
        '''
        该方法用于停止记录调试指令流，与start_trace方法成对使用。
        '''
        self._inst.write('TRACe:REMote:MODE:FILE1:ENABle OFF')

    def init_lte(self):
        '''
        该方法用于实例化LTE模块实例。
        '''
        self.lte = lte.LTE(self._inst, self.connector, self.converter)

    def init_wcdma(self):
        '''
        该方法用于实例化WCDMA模块实例。
        '''
        self.wcdma = wcdma.WCDMA(self._inst, self.connector, self.converter)

    def init_gsm(self):
        '''
        该方法用于实例化GSM模块实例。
        '''
        self.gsm = gsm.GSM(self._inst, self.connector, self.converter)

    def _connect(self, ip):
        '''
        该方法用于与仪器建立连接并返回控制实例。
        ip：仪器的ip地址；
        返回仪器引用。
        '''
        rm = visa.ResourceManager()
        dev_addr = 'TCPIP0::%s::inst0::INSTR' % ip
        try:
            inst = rm.open_resource(dev_addr)
            self.logger.info('connect successfully!')
            # 设置仪器返回值终止符，visa会自动去除终止符
            inst.read_termination = '\n'
            # 设置等待仪器返回超时时间为10s
            inst.timeout = 10000
            return inst

        except Exception, e:
            self.logger.error('connect failed!')
            self.logger.error(e)

    def reset(self):
        '''
        该方法用于复位仪器参数至默认值。
        '''
        self._inst.write('*RST')
        self._wait_for_operation_done()

    def _wait_for_operation_done(self):
        '''
        该方法用于等待仪器完成操作，用于设置参数的方法后。
        '''
        done = False
        while not done:
            temp = self._inst.query('*OPC?')
            if not cmp(temp.strip(), '1'):
                done = True
            time.sleep(0.1)

    def set_signal_routing(self, connector, converter):
        '''
        该方法用于配置信号链路。
        connector：连接器端口编号，如使用RF1COM，则参数传入‘1’；
        converter：信号变换器编号，如使用Converter1，则参数传入‘1’。
        '''
        self._inst.write('ROUTe:LTE:SIGN:SCENario:SCELl RF%sC,RX%s, RF%sC,TX%s'
                         % (connector, converter, connector, converter))
        self.connector = connector
        self.converter = converter

    def set_correction_table(self, f1, corr1, f2, corr2):
        '''
        该方法用于配置线损表。
        f1，f2，为线损表两端的频率；
        corr1，corr2为线损表两端的补偿值。
        '''
        table_name = "'custom'"
        self._inst.write("CONFigure:BASE:FDCorrection:CTABle:CREate %s, %sMHz, %s, %sMHz, %s" %
                         (table_name, f1, corr1, f2, corr2))
        self._wait_for_operation_done()
        self.logger.debug(
            self._inst.query("CONFigure:BASE:FDCorrection:CTABle:DETails? %s" % table_name))
        self.logger.info('Create correction table.')
        self._inst.write("CONFigure:FDCorrection:ACTivate RF%sC, %s, RXTX, RF%s" %
                         (self.connector, table_name, self.converter))
        self._wait_for_operation_done()
        self.logger.debug('correction table:' + self._inst.query
        ("CONFigure:FDCorrection:USAGe?  RF%sC,RF%s" % (self.connector, self.converter)))

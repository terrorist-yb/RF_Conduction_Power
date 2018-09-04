# -*- coding:utf-8 -*-
###############################################################################
# Copyright (C), 2018, TP-LINK Technologies Co., Ltd.
#
# 作者：吴扬波
# 版本：V1.0
# 变更历史:
# 1，2018-08-20， 吴扬波——首次创建：WCDMA类，用于WCDMA信号模块配置、测量等
# 若引用或修改API，请保留API变更历史。
###############################################################################
from Utility import pylogger
import time


class WCDMA(object):
    '''
    WCDMA类，用于WCDMA信号模块配置、测量等。
    '''

    def __init__(self, inst, connector, converter):
        '''
        初始化配置参数实例变量、信号路由、测量配置。
        '''
        self.logger = pylogger.setup_logger(self.__class__.__name__)
        self._inst = inst
        self.set_signal_routing(connector, converter)
        self.band = ''
        self.dl_channel = ''
        self._config_measurement()

    def _wait_for_operation_done(self):
        '''
        该方法用于等待仪器完成操作，用于设置参数的方法后。
        '''
        done = False
        while not done:
            temp = self._inst.query('*OPC?')
            if not cmp(temp, '1'):
                done = True
            time.sleep(0.1)

    def set_signal_routing(self, connector, converter):
        '''
        该方法用于配置WCDMA信号链路。
        connector：连接器端口编号，如使用RF1COM，则参数传入‘1’；
        converter：信号变换器编号，如使用Converter1，则参数传入‘1’。
        '''
        self._inst.write('ROUTe:WCDMa:SIGN:SCENario:SCELl RF%sC,RX%s, RF%sC,TX%s'
                         % (connector, converter, connector, converter))
        self.logger.debug('WCDMA route: ' + self._inst.query('ROUTe:WCDMa:SIGN:SCENario:SCELl?'))

    def enable_output(self):
        '''
        该方法用于使能WCDMA信号输出。
        '''
        state = self._inst.query('SOURce:WCDMa:SIGN:CELL:STATe:ALL?')
        if not state.startswith('ON'):
            self._inst.write('SOURce:WCDMa:SIGN:CELL:STATe ON')
            while True:
                state = self._inst.query('SOURce:WCDMa:SIGN:CELL:STATe:ALL?')
                if state.startswith('ON,ADJ'):
                    self.logger.info('Output on.')
                    break
                time.sleep(0.1)

    def disable_output(self):
        '''
        该方法用于关闭WCDMA信号输出。
        '''
        self._inst.write('SOURce:WCDMa:SIGN:CELL:STATe OFF')
        is_output_disable = False
        while not is_output_disable:
            state = self._inst.query('SOURce:WCDMa:SIGN:CELL:STATe:ALL?')
            if state.startswith('OFF,ADJ'):
                is_output_disable = True
                self.logger.info('Output off.')
            time.sleep(0.1)

    def register(self):
        '''
        该方法用于等待UE驻网。
        '''
        state = self._inst.query('FETCh:WCDMa:SIGN:CSWitched:STATe?')
        if not state.startswith('REG'):
            while True:
                state = self._inst.query('FETCh:WCDMa:SIGN:CSWitched:STATe?')
                if state.startswith('REG'):
                    self.logger.info('UE registers successfully!')
                    break
                time.sleep(0.1)

    def setup_cs_connection(self):
        '''
        该方法用于建立UE与WCDMA网络CS域连接。
        '''
        state = self._inst.query('FETCh:WCDMa:SIGN:CSWitched:STATe?')
        if not state.startswith('CEST'):
            self._inst.write('CALL:WCDMa:SIGN:CSWitched:ACTion CONNect')
            while True:
                state = self._inst.query('FETCh:WCDMa:SIGN:CSWitched:STATe?')
                if state.startswith('CEST'):
                    self.logger.info('CS domain establishes successfully!')
                    break
                time.sleep(0.1)

    def set_downlink_channel(self, band, dl_channel):
        '''
        该方法用于设置WCDMA下行信道参数。
        band：频段，如使用band1，则传入参数‘1’；
        dl_channel：信道号，如使用信道10562，则传入参数‘10562’。
        '''
        self._inst.write('CONFigure:WCDMa:SIGN:RFSettings:CARRier:DL OB%s, %s' % (band, dl_channel))
        self._wait_for_operation_done()

        self.band = self._inst.query('CONFigure:WCDMa:SIGN:CARRier:BAND?')[2]
        self.dl_channel = self._inst.query('CONFigure:WCDMa:SIGN:RFSettings:CARRier:CHANnel:DL?')
        self.logger.info('@BAND: OB%s,DLCH: %s' % (self.band, self.dl_channel))

    def set_downlink_power(self, power='-80'):
        '''
        该方法用于设置下行功率。
        '''
        self._inst.write('CONFigure:WCDMa:SIGN:RFSettings:CARRier:COPower %s' % power)
        self._wait_for_operation_done()
        self.logger.info('Set downlink power as %sdbm' % power)

    def set_voice_connection(self):
        '''
        该方法用于建立3G语音通话。
        '''
        self._inst.write('CONFigure:WCDMa:SIGN:CONNection:UETerminate VOICe')

    def set_prach_drxcycle(self, cycle='7'):
        '''
        该方法用于设置DRX周期。
        '''
        self._inst.write('CONFigure:WCDMa:SIGN:UL:PRACh:DRXCycle %s' % cycle)

    def set_closeloop_power(self, power):
        '''
        该方法用于配置UE闭环功控功率。
        power：目标闭环功率值，单位dbm。
        '''
        self._inst.write('CONFigure:WCDMa:SIGN:UL:TPC:SET CLOop')
        self._wait_for_operation_done()
        self._inst.write('CONFigure:WCDMa:SIGN:UL:TPC:TPOWer %s' % power)
        self._wait_for_operation_done()
        self.logger.info('Set close loop tx power as %sdbm' % power)

    def set_max_power(self):
        '''
        该方法用于配置UE以最大功率发射信号。
        power：最大功率数值，单位dbm。
        '''
        self._inst.write('CONFigure:WCDMa:SIGN:UL:TPC:SET ALL1')
        self._wait_for_operation_done()
        self.logger.info('Set tx power as max power')

    def _config_measurement(self):
        '''
        该方法用于配置测量相关参数。
        '''
        # 测量参数关联LTE信号发生器
        self._inst.write("ROUTe:WCDMa:MEAS:SCENario:CSPath 'WCDMA Sig1'")
        # 设置单次测量-默认
        self._inst.write('CONFigure:WCDMa:MEAS:MEValuation:REPetition SINGleshot')
        self._inst.write('CONFigure:WCDMa:MEAS:MEValuation:RESult:UEPower ON')

    def measure_average_tx_power(self):
        '''
        该方法用于测量UE平均上行功率。
        返回上行平均功率。
        '''
        self._inst.write('INIT:WCDMa:MEAS:MEValuation')
        self._wait_for_operation_done()
        is_measurement_done = False
        while not is_measurement_done:
            temp = self._inst.query('FETCh:WCDMa:MEAS:MEValuation:STATe:ALL?')
            if not cmp(temp, 'RDY,ADJ,INV'):
                is_measurement_done = True
            time.sleep(0.1)

            result = self._inst.query('FETCh:WCDMa:MEAS:MEValuation:TRACe:UEPower:AVERage?')
        tx_power = round(float(result.split(',')[1]), 2)
        self.logger.info('Tx power: %sdbm' % str(tx_power))
        return tx_power

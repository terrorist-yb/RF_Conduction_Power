# -*- coding:utf-8 -*-
###############################################################################
# Copyright (C), 2018, TP-LINK Technologies Co., Ltd.
#
# 作者：吴扬波
# 版本：V1.0
# 变更历史:
# 1，2018-08-20， 吴扬波——首次创建：GSM类，用于GSM信号模块配置、测量等
# 若引用或修改API，请保留API变更历史。
###############################################################################
from Utility import pylogger
import time


class GSM(object):
    '''
    GSM类，用于GSM信号模块配置、测量等。
    '''

    def __init__(self, inst, connector, converter):
        '''
        初始化配置参数实例变量、信号路由、测量配置。
        '''
        self.logger = pylogger.setup_logger(self.__class__.__name__)
        self._inst = inst
        self.set_signal_routing(connector, converter)
        self.bcch_band = ''
        self.bcch_dl_channel = ''
        self.tch_band = ''
        self.tch_dl_channel = ''
        self._switch_off_ps_domain()
        self._config_measurement()

    def set_signal_routing(self, connector, converter):
        '''
        该方法用于配置GSM信号链路。
        connector：连接器端口编号，如使用RF1COM，则参数传入‘1’；
        converter：信号变换器编号，如使用Converter1，则参数传入‘1’。
        '''
        self._inst.write('ROUTe:GSM:SIGN:SCENario:SCELl RF%sC,RX%s, RF%sC,TX%s'
                         % (connector, converter, connector, converter))
        self.logger.debug('GSM route: ' + self._inst.query('ROUTe:WCDMa:SIGN:SCENario:SCELl?'))

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

    def enable_output(self):
        '''
        该方法用于使能GSM信号输出。
        '''
        state = self._inst.query('SOURce:GSM:SIGN:CELL:STATe:ALL?')
        if not state.startswith('ON'):
            self._inst.write('SOURce:GSM:SIGN:CELL:STATe ON')
            while True:
                state = self._inst.query('SOURce:GSM:SIGN:CELL:STATe:ALL?')
                if state.startswith('ON,ADJ'):
                    self.logger.info('Output on.')
                    break
                time.sleep(0.1)

    def disable_output(self):
        '''
        该方法用于关闭GSM信号输出。
        '''
        self._inst.write('SOURce:GSM:SIGN:CELL:STATe OFF')
        is_output_disable = False
        while not is_output_disable:
            state = self._inst.query('SOURce:GSM:SIGN:CELL:STATe:ALL?')
            if state.startswith('OFF,ADJ'):
                is_output_disable = True
                self.logger.info('Output off.')
            time.sleep(0.1)

    def synchronize(self):
        '''
        该方法用于等待UE同步网络。
        '''
        state = self._inst.query('FETCh:GSM:SIGN:CSWitched:STATe?')
        if not (state.startswith('SYNC') or state.startswith('CEST')):
            while True:
                state = self._inst.query('FETCh:GSM:SIGN:CSWitched:STATe?')
                if state.startswith('SYNC'):
                    self.logger.info('UE synchronizes successfully!')
                    break
                time.sleep(0.1)

    def setup_cs_connection(self):
        '''
        该方法用于建立UE与网络的CS域连接。
        '''
        state = self._inst.query('FETCh:GSM:SIGN:CSWitched:STATe?')
        if not state.startswith('CEST'):
            self._inst.write('CALL:GSM:SIGN:CSWitched:ACTion CONNect')
            while True:
                state = self._inst.query('FETCh:GSM:SIGN:CSWitched:STATe?')
                if state.startswith('CEST'):
                    self.logger.info('CS domain establishes successfully!')
                    break
                time.sleep(0.1)

    def set_bcch_downlink_channel(self, band, dl_channel):
        '''
        该方法用于设置bcch的频段和下行通道。
        band：频段，如使用GSM850，则传入参数‘GSM850’；
        dl_channel：信道号，如使用信道128，则传入参数‘128’；
        '''
        # 设置bcch频段
        symbol = {'GSM850': 'G085', 'GSM900': 'G09', 'DCS1800': 'G18', 'PCS1900': 'G19'}
        self._inst.write('CONFigure:GSM:SIGN:BAND:BCCH %s' % symbol[band])
        self._wait_for_operation_done()
        # 设置bcch信道
        self._inst.write('CONFigure:GSM:SIGN:RFSettings:CHANnel:BCCH %s' % dl_channel)
        self._wait_for_operation_done()

        # 根据仪器返回值修改信道实例变量
        result = self._inst.query('CONFigure:GSM:SIGN:BAND:BCCH?')
        for key, val in symbol.items():
            if not cmp(result, val):
                self.bcch_band = key
        self.bcch_dl_channel = self._inst.query('CONFigure:GSM:SIGN:RFSettings:CHANnel:BCCH?')
        self.logger.info('Set BCCH --- @BAND: %s,DLCH: %s' % (self.bcch_band, self.bcch_dl_channel))

    def set_tch_downlink_channel(self, dl_channel):
        '''
        该方法用于设置tch的频段和下行通道。
        dl_channel：信道号，如使用信道128，则传入参数‘128’；
        '''
        symbol = {'GSM850': 'G085', 'GSM900': 'G09', 'DCS1800': 'G18', 'PCS1900': 'G19'}
        self._inst.write('CONFigure:GSM:SIGN:RFSettings:CHANnel:TCH %s' % dl_channel)
        self._wait_for_operation_done()
        result = self._inst.query('SENSe:GSM:SIGN:BAND:TCH?')
        for key, val in symbol.items():
            if not cmp(result, val):
                self.tch_band = key
        self.tch_dl_channel = self._inst.query('CONFigure:GSM:SIGN:RFSettings:CHANnel:TCH?')
        self.logger.info('Set TCH --- @BAND: %s,DLCH: %s' % (self.tch_band, self.tch_dl_channel))

    def set_bcch_level(self, level):
        '''
        该方法用于设置bcch的信号电平。
        level：bcch信号电平，例如设置成-80dbm，则传入参数为‘-85’。
        '''
        self._inst.write('CONFigure:GSM:SIGN:RFSettings:LEVel:BCCH %s' % level)
        self._wait_for_operation_done()
        self.logger.info('Set BCCH level: %s'
                         % self._inst.query('CONFigure:GSM:SIGN:RFSettings:LEVel:BCCH?'))

    def set_tch_level(self, level):
        '''
        该方法用于设置tch的信号电平。
        level：tch信号电平，例如设置成-80dbm，则传入参数为‘-85’。
        '''
        self._inst.write('CONFigure:GSM:SIGN:RFSettings:LEVel:TCH %s' % level)
        self._wait_for_operation_done()
        self.logger.info('Set TCH level: %s'
                         % self._inst.query('CONFigure:GSM:SIGN:RFSettings:LEVel:TCH?'))

    def _switch_off_ps_domain(self):
        '''
        该方法用于关闭PS域连接。
        '''
        self._inst.write('CONFigure:GSM:SIGN:CELL:PSDomain OFF')

    def disable_dtx(self):
        '''
        该方法用于关闭dtx。
        '''
        self._inst.write('CONFigure:GSM:SIGN:DTX OFF')

    def set_bspamfrms(self, frames='5'):
        '''
        该方法用于设置寻呼信道复帧数。
        '''
        self._inst.write('CONFigure:GSM:SIGN:CELL:BSPamfrms %s' % frames)

    def _set_band_indicator(self, band):
        '''
        该方法用于配置频段indicator，在切换至1800或1900时，必须得修改该参数。
        '''
        symbol = {'GSM850': 'NA', 'GSM900': 'NA', 'DCS1800': 'G18', 'PCS1900': 'G19'}
        result = self._inst.query('CONFigure:GSM:SIGN:CELL:BINDicator?')
        if cmp(symbol[band], 'NA'):
            if cmp(symbol[band], result):
                self._inst.write('CONFigure:GSM:SIGN:CELL:BINDicator %s' % symbol[band])
                time.sleep(5)
                self._wait_for_operation_done()

    def set_tch_pcl(self, pcl):
        '''
        该方法用于设置tch的功率等级。
        pcl：tch功率等级，例如设置功率等级为5，则传入参数为‘5’。
        '''
        self._inst.write('CONFigure:GSM:SIGN:RFSettings:PCL:TCH:CSWitched %s' % pcl)
        self._wait_for_operation_done()
        self.logger.info('Set TCH PCL as %s' % pcl)

    def handover(self, band, dl_channel):
        '''
        该方法用于频段之间的切换。
        '''
        symbol = {'GSM850': 'G085', 'GSM900': 'G09', 'DCS1800': 'G18', 'PCS1900': 'G19'}
        tch_channel = self._inst.query('CONFigure:GSM:SIGN:RFSettings:CHANnel:TCH?')
        tch_band = self._inst.query('SENSe:GSM:SIGN:BAND:TCH?')
        if cmp(symbol[band], tch_band):
            self._set_band_indicator(band)
            self._inst.write('PREPare:GSM:SIGN:HANDover:TARGet %s' % symbol[band])
            self._wait_for_operation_done()
            self._inst.write('PREPare:GSM:SIGN:HANDover:CHANnel:TCH %s' % dl_channel)
            self._wait_for_operation_done()
            self._inst.write('PREPare:GSM:SIGN:HANDover:LEVel:TCH -80')
            self._wait_for_operation_done()
            self._inst.write('PREPare:GSM:SIGN:HANDover:TSLot 3')
            self._wait_for_operation_done()
            self._inst.write('CALL:GSM:SIGN:HANDover:STARt')
            while True:
                state = self._inst.query('FETCh:GSM:SIGN:CSWitched:STATe?')
                if state.startswith('CEST'):
                    self.logger.debug('Handover --> %s'
                                      % self._inst.query('SENSe:GSM:SIGN:BAND:TCH?'))
                    self.logger.info('Handover @BAND: OB%s,DLCH: %s' % (band, dl_channel))
                    break
                time.sleep(0.1)
        elif cmp(tch_channel, dl_channel):
            self._inst.write('CONFigure:GSM:SIGN:RFSettings:CHANnel:TCH %s' % dl_channel)
            self.logger.info('@BAND: OB%s,DLCH: %s' % (band, dl_channel))

    def _config_measurement(self):
        '''
        该方法用于测量参数配置。
        '''
        # 测量参数关联GSM信号发生器
        self._inst.write("ROUTe:GSM:MEAS:SCENario:CSPath 'GSM Sig1'")
        # 设置单次测量-默认
        self._inst.write('CONFigure:GSM:MEAS:MEValuation:REPetition SINGleshot')

    def measure_average_tx_power(self):
        '''
        该方法用于上行平均功率测量。
        返回上行平均功率。
        '''
        self._inst.write('INIT:GSM:MEAS:MEValuation')
        self._wait_for_operation_done()
        while True:
            state = self._inst.query('FETCh:GSM:MEAS:MEValuation:STATe:ALL?')
            if not cmp(state, 'RDY,ADJ,INV'):
                break
            time.sleep(0.1)

        result = self._inst.query('FETCh:GSM:MEAS:MEValuation:PVTime?')
        tx_power = round(float(result.split(',')[5]), 2)
        self.logger.info('Tx power: %sdbm' % str(tx_power))
        return tx_power

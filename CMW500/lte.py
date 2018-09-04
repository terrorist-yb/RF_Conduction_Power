# -*- coding:utf-8 -*-
###############################################################################
# Copyright (C), 2018, TP-LINK Technologies Co., Ltd.
#
# 作者：吴扬波
# 版本：V1.0
# 变更历史:
# 1，2018-08-20， 吴扬波——首次创建：LTE类，用于LTE信号模块配置、测量等
# 若引用或修改API，请保留API变更历史。
###############################################################################
from Utility import pylogger
import time


class LTE(object):
    '''
    LTE类，用于LTE信号模块配置、测量等。
    '''

    def __init__(self, inst, connector, converter):
        '''
        初始化配置参数实例变量、信号路由、测量配置。
        '''
        self.logger = pylogger.setup_logger(self.__class__.__name__)
        self._inst = inst
        self._max_power = 0
        self.band = ''
        self.ul_channel = ''
        self.dl_channel = ''
        self.band_width = ''
        self.ul_rb_position = ''
        self.ul_rb_num = ''
        # 配置信号路由
        self._set_signal_routing(connector, converter)
        # 测量通道设置
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

    def _set_signal_routing(self, connector, converter):
        '''
        该方法用于配置LTE信号链路。
        connector：连接器端口编号，如使用RF1COM，则参数传入‘1’；
        converter：信号变换器编号，如使用Converter1，则参数传入‘1’。
        '''
        self._inst.write('ROUTe:LTE:SIGN:SCENario:SCELl RF%sC,RX%s, RF%sC,TX%s'
                         % (connector, converter, connector, converter))
        self.logger.debug('LTE route: ' + self._inst.query('ROUTe:LTE:SIGN:SCENario:SCELl?'))

    def set_downlink_channel(self, band, dl_channel, band_width):
        '''
        该方法用于设置LTE下行信道参数。
        band：频段，如使用band1，则传入参数‘1’；
        dl_channel：信道号，如使用信道25，则传入参数‘25’；
        band_width： 带宽，如带宽为5MHz，则传入参数‘5’。
        '''
        # 配置频段
        self._inst.write('CONFigure:LTE:SIGN:BAND OB%s' % band)
        self._wait_for_operation_done()
        # 配置信道
        self._inst.write('CONFigure:LTE:SIGN:RFSettings:CHANnel:DL %s' % dl_channel)
        self._wait_for_operation_done()
        # 配置带宽
        bw = {
            '1.4': 'B014', '3': 'B030', '5': 'B050', '10': 'B100', '15': 'B150', '20': 'B200',
        }
        self._inst.write('CONFigure:LTE:SIGN:CELL:BANDwidth:DL %s' % bw[band_width])
        self._wait_for_operation_done()

        # 从仪器端返回生效的配置值
        self.ul_channel = self._inst.query('CONFigure:LTE:SIGN:RFSettings:CHANnel:UL?')
        self.band = band
        self.dl_channel = dl_channel
        self.band_width = band_width
        self.logger.info('@BAND: OB%s,DLCH: %s,BW: %sMHz'
                         % (self.band, self.dl_channel, self.band_width))
        self.logger.debug('ULCH: %s' % self.ul_channel)

    def handover(self):
        '''
        该方法用于配置信道参数后的切换。
        由于调用set_downlink_channel方法后，信道直接生效，可不用该方法切换。
        '''
        bw = {
            '1.4': 'B014', '3': 'B030', '5': 'B050', '10': 'B100', '15': 'B150', '20': 'B200',
        }
        self._inst.write('PREPare:LTE:SIGN:HAND OB%s, %s, %s, NS01'
                         % (self.band, self.dl_channel, bw[self.band_width]))
        self._wait_for_operation_done()
        self._inst.write('CALL:LTE:SIGN:PSWitched:ACTion HANDover')
        while True:
            state = self._inst.query('FETCH:LTE:SIGN:PSWitched:STATe?')
            if state.startswith('CEST'):
                self.logger.info('Handover successfully!')
                self.logger.debug(self._inst.query('CONFigure:LTE:SIGN:RFSettings:CHANnel:DL?'))
                break
            time.sleep(0.1)

    def set_max_power(self, power='33'):
        '''
        该方法用于配置UE以最大功率发射信号。
        power：最大功率数值，单位dbm。
        '''
        if self._max_power > power:
            self._inst.write('CONFigure:LTE:SIGN:UL:PMAX %s' % power)
            self._wait_for_operation_done()
            self._max_power = power
        self._inst.write('CONFigure:LTE:SIGN:UL:PUSCh:TPC:SET MAXPower')
        self._wait_for_operation_done()
        self.logger.info('Set tx power as MAXPower.')

    def set_closeloop_power(self, power):
        '''
        该方法用于配置UE闭环功控功率。
        power：目标闭环功率值，单位dbm。
        '''
        self._inst.write('CONFigure:LTE:SIGN:UL:PUSCh:TPC:SET CLOop')
        self._wait_for_operation_done()
        self._inst.write('CONFigure:LTE:SIGN:UL:PUSCh:TPC:CLTPower %s' % power)
        self._wait_for_operation_done()
        self.logger.info('Set close loop tx power as %sdbm' % power)

    def set_openloop_power(self, power):
        '''
        该方法用于配置UE开环功率。
        power：目标开环功率值，单位dbm。
        '''
        self._inst.write('CONFigure:LTE:SIGN:UL:OLNPower %s' % power)
        self._wait_for_operation_done()
        self.logger.info('Set open loop tx power as %sdbm' % power)

    def disable_output(self):
        '''
        该方法用于关闭LTE信号输出。
        '''
        self._inst.write('SOURce:LTE:SIGN:CELL:STATe OFF')
        is_output_disable = False
        while not is_output_disable:
            state = self._inst.query('SOURce:LTE:SIGN:CELL:STATe:ALL?')
            if state.startswith('OFF,ADJ'):
                is_output_disable = True
                self.logger.info('Output off.')
            time.sleep(0.1)

    def enable_output(self):
        '''
        该方法用于使能LTE信号输出。
        '''
        state = self._inst.query('SOURce:LTE:SIGN:CELL:STATe:ALL?')
        if not state.startswith('ON'):
            self._inst.write('SOURce:LTE:SIGN:CELL:STATe ON')
            while True:
                state = self._inst.query('SOURce:LTE:SIGN:CELL:STATe:ALL?')
                if state.startswith('ON,ADJ'):
                    self.logger.info('Output on.')
                    break
                time.sleep(0.1)

    def attach(self):
        '''
        该方法用于等待UE附着网络。
        '''
        state = self._inst.query('FETCH:LTE:SIGN:PSWitched:STATe?')
        if not state.startswith('ATT'):
            while True:
                state = self._inst.query('FETCH:LTE:SIGN:PSWitched:STATe?')
                if state.startswith('ATT'):
                    self.logger.info('UE attach successfully!')
                    break
                time.sleep(0.1)

    def connect_rrc(self):
        '''
        该方法用于建立网络RRC连接。
        '''
        state = self._inst.query('FETCH:LTE:SIGN:PSWitched:STATe?')
        if not state.startswith('CEST'):
            self._inst.write('CALL:LTE:SIGN:PSWitched:ACTion CONNect')
            while True:
                state = self._inst.query('FETCH:LTE:SIGN:PSWitched:STATe?')
                if state.startswith('CEST'):
                    self.logger.info('UE Connect RRC successfully!')
                    break
                time.sleep(0.1)

    def set_paging_cycle(self, cycle='128'):
        '''
        该方法用于配置paging周期。
        '''
        list = {
            '32': 'P032', '64': 'P064', '128': 'P128', '256': 'P256'
        }
        self._inst.write('CONFigure:LTE:SIGN:CONNection:DPCYcle %s' % list[cycle])
        self._wait_for_operation_done()
        self.logger.info('Set paging cycle as %s' % cycle)

    def disable_rrc_connection_after_attach(self):
        '''
        该方法用于配置UE附着网络后，断开RRC连接。
        '''
        self._inst.write('CONFigure:LTE:SIGN:CONNection:KRRC OFF')

    def _config_measurement(self):
        '''
        该方法用于配置测量相关参数。
        '''
        # 测量参数关联LTE信号发生器
        self._inst.write("ROUTe:LTE:MEAS:SCENario:CSPath 'LTE Sig1'")
        self._inst.write('CONFigure:LTE:MEAS:MEValuation:REPetition SING')
        # 设置单次测量-默认
        self._inst.write('CONFigure:LTE:MEAS:MEValuation:MODulation:MSCHeme AUTO')
        # 调制策略设置-默认
        self._inst.write('CONFigure:LTE:MEAS:MEValuation:RBALlocation:AUTO ON')
        self._inst.write("TRIGger:LTE:MEAS:MEValuation:SOURce 'LTE Sig1: FrameTrigger'")
        self._inst.write('CONFigure:LTE:MEAS:MEValuation:RESult:TXM ON')

    def measure_average_tx_power(self):
        '''
        该方法用于测量UE平均上行功率。
        返回上行平均功率。
        '''
        self._inst.write('INIT:LTE:MEAS:MEValuation')
        self._wait_for_operation_done()
        is_measurement_done = False
        while not is_measurement_done:
            temp = self._inst.query('FETCh:LTE:MEAS:MEValuation:STATe:ALL?')
            if not cmp(temp, 'RDY,ADJ,INV'):
                is_measurement_done = True
            time.sleep(0.1)

        result = self._inst.query('FETCh:LTE:MEAS:MEValuation:MODulation:AVERage?')
        tx_power = round(float(result.split(',')[17]), 2)
        self.logger.info('Actual tx power: %sdbm' % str(tx_power))
        return tx_power

    def config_rmc(self, rb_num, rb_pos):
        '''
        该方法用于配置RMC参数。
        rb_num：RB数量，例如RB数为1，则传入参数为‘1’；
        rb_pos：RB位置，例如RB位置为低，则传入参数为‘LOW’。
        '''
        self._inst.write('CONFigure:LTE:SIGN:CONNection:STYPe RMC')
        self._wait_for_operation_done()
        self._inst.write('CONFigure:LTE:SIGN:CONNection:RMC:UL N%s,KEEP,KEEP' % rb_num)
        self._inst.write('CONFigure:LTE:SIGN:CONNection:RMC:RBPosition:UL %s' % rb_pos)
        self.ul_rb_position = self._inst.query('CONFigure:LTE:SIGN:CONNection:RMC:RBPosition:UL?')
        temp = self._inst.query('CONFigure:LTE:SIGN:CONNection:RMC:UL?')
        self.ul_rb_num = temp.split(',')[0][1:]
        self.logger.info('RB position: %s, RB number: %s' % (self.ul_rb_position, self.ul_rb_num))

    def set_rsep_level(self, level):
        '''
        该方法用于配置上行功率电平。
        level：上行功率电平，单位为dbm。
        '''
        self._inst.write('CONF:LTE:SIGN:DL:RSEP:LEV %s' % level)
        self._wait_for_operation_done()
        self.logger.info('RSEP level: %s' % self._inst.query('CONF:LTE:SIGN:DL:RSEP:LEV?'))

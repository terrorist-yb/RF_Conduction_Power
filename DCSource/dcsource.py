# -*- coding:utf-8 -*-
###############################################################################
# Copyright (C), 2018, TP-LINK Technologies Co., Ltd.
#
# 作者：吴扬波
# 版本：V1.0
# 变更历史:
# 1，2018-08-20， 吴扬波——首次创建：DCSource类，用于66319B参数配置、测量等
# 若引用或修改API，请保留API变更历史。
###############################################################################
import visa
from Utility import pylogger
import time
import struct
import collections


class DCSource(object):
    '''
    DCSource类，用于Agilent 66319B参数配置、测量
    '''

    def __init__(self, addr):
        '''
        初始化配置参数实例变量、信号路由、测量配置。
        '''
        self.logger = pylogger.setup_logger(self.__class__.__name__)
        self._inst = self.connect(addr)
        self.sampling_period = 15.6E-6
        self.current_range = '3A'
        self.max_voltage = 4.4
        # 设置输出电压上限
        self._set_protection(self.max_voltage)
        # 配置最初的采样周期和量程
        self._config_measurement(self.sampling_period, self.current_range)

    def connect(self, addr):
        '''
        建立PC与DC source连接
        addr: GPIB地址
        返回仪器引用。
        '''
        rm = visa.ResourceManager()
        try:
            inst = rm.open_resource(addr)
            self.logger.info('Connect DC source successfully!')
            inst.read_termination = '\n'
            inst.timeout = 10000
            return inst

        except Exception, e:
            self.logger.error('Connect DC source failed!')
            self.logger.error(e)

    def _wait_for_operation_done(self):
        '''
        该方法用于等待仪器完成操作，用于设置参数的方法后。
        '''
        done = False
        while not done:
            temp = self._inst.query('*OPC?')
            if not cmp(temp.strip(), '+1'):
                done = True
            time.sleep(0.1)

    def reset(self):
        '''
        该方法用于复位仪器参数至默认值。
        '''
        self._inst.write('*rst; status:preset; *cls')

    def _set_protection(self, max_voltage):
        '''
        该方法用于设置DC Source的输出电压上限值。
        max_voltage：输出电压上限值，例如希望电压不超过4.1V，则传入参数4.1
        '''
        self._inst.write('voltage:protection:level %.1f;state on' % max_voltage)
        self._wait_for_operation_done()

    def set_measure_current_range(self, current_range='3A'):
        '''
        该方法用于设置电流测试的量程。
        current_range：电流范围，仪器可以选的值为0.02A，1A，3A。
        '''
        self._inst.write('sense:current:detector dc;range %s' % current_range)
        self._wait_for_operation_done()
        self.current_range = current_range

    def _config_measurement(self, sampling_period, current_range):
        '''
        该方法用于设置电流测试的量程。
        sampling_period：采样频率；
        current_range：电流范围，仪器可以选的值为0.02A，1A，3A。
        '''
        self._inst.write('sense:sweep:points 4096;tinterval %e' % sampling_period)
        self._wait_for_operation_done()
        self.set_measure_current_range(current_range)

    def set_voltage(self, voltage):
        '''
        该方法用于设置输出电压幅值。
        voltage：输出电压值，例如希望电压为4.1V，则传入参数4.1
        '''
        if (voltage - self.max_voltage) > 1e-7:
            self.logger.error('ERROR:OVP!')
        else:
            self._inst.write('voltage %.1f' % voltage)
            self._wait_for_operation_done()
            self.logger.info('Set voltage: %.1fV' % voltage)

    def enable_output(self):
        '''
        该方法用于使能电源电压输出。
        '''
        self._inst.write('output1 on')
        self._wait_for_operation_done()
        self._inst.write('display on')

    def measure_current(self, seconds):
        '''
        该方法用于平均电流测量（外部调用）。
        seconds：单次测量时长，例如希望获得30s的电流平均值，则传入参数30。
        '''
        average_current = self._measure_current(seconds)
        self.logger.info('Average current: %.1fmA' % average_current)
        return average_current

    def _measure_current(self, seconds):
        '''
        该方法用于平均电流测量。
        seconds：单次测量时长，例如希望获得30s的电流平均值，则传入参数30；
        返回平均测量电流。
        '''
        total_loop = int(round(seconds / (self.sampling_period * 4096)))
        loop_count = 0
        current_list = []
        while loop_count < total_loop:
            current_list.append(float(self._inst.query('MEAS:CURR?')))
            loop_count += 1
        average_current = round(sum(current_list) / (len(current_list) * 1.0) * 1000, 1)
        return average_current

    def _convert(self, raw_data):
        '''
        该方法用于将电源返回的二进制字节流转成浮点列表
        raw_data：字节流。
        返回转换后的浮点列表。
        '''
        raw_data_list = raw_data.split('#')
        current_data = []
        for index, data in enumerate(raw_data_list):
            if cmp(index, 0):
                data = data.strip('\n')
                digit_num = int(str(data[0]))
                bytes_num = int(''.join(data[1:1 + digit_num]))
                data_num = bytes_num / 4
                raw_current_data = data[1 + digit_num:]
                current_data.extend(list(struct.unpack('%df' % data_num, raw_current_data)))
        return current_data

    def check_current_stability(self, timeout=30, window_width=10, max_deviation=50.0):
        '''
        该方法利用移动的矩形窗，计算窗内的最大偏差是否符合电流门限，判断电流的稳定性。
        timeout：超时，单位秒；
        window_width：观测窗宽度，单位秒；
        max_deviation：偏差阈值，如果在观测窗内，离差平均值大于偏差阈值，则认为电流不稳定，单位mA；
        返回电流测量是否超时，布尔值。
        '''
        sample_interval = 0.5
        fifo_depth = window_width / sample_interval
        is_current_stable = True

        filter_fifo = collections.deque([], fifo_depth)
        filter_fifo.clear()
        count = 0
        t0 = time.time()
        while True:
            if count < fifo_depth:
                filter_fifo.append(self._measure_current(sample_interval))
                count += 1
            else:
                filter_fifo.append(self._measure_current(sample_interval))
                deviation = []
                average_current = sum(filter_fifo) / len(filter_fifo)
                for item in filter_fifo:
                    deviation.append(abs(item - average_current))
                average_deviation = sum(deviation) / len(deviation)
                t1 = time.time()
                if average_deviation < max_deviation:
                    self.logger.debug('Current is stable.')
                    break
                elif (t1 - t0) > timeout:
                    is_current_stable = False
                    self.logger.error('Current is unstable, and time runs out.')
                    break
        return is_current_stable

import logging
import numpy as np

import time

from pycqed.measurement import detector_functions as det
from pycqed.measurement import mc_parameter_wrapper as pw
from pycqed.measurement import sweep_functions as swf
from pycqed.analysis import measurement_analysis as ma

from pycqed.instrument_drivers.meta_instrument.qubit_objects.qubit_object \
    import Qubit

from qcodes.instrument.parameter import ManualParameter

class QLab_Neon(Qubit):
    def __init__(self, name, MC, vna_instr, sgen_instr = None, QDac_instr = None, gs_instr=None,yoga_1 = None, yoga_2=None, **kw):
        super().__init__(name, **kw)

        self.MC = MC
        #self.heterodyne_instr = heterodyne_instr
        #self.cw_source = cw_source
        self.vna_instr = vna_instr
        self.QDac_instr = QDac_instr
        print(QDac_instr)
        self.sgen_instr =sgen_instr
        self.gs_instr = gs_instr
        self.yoga_instr_1 = yoga_1
        self.yoga_instr_2 = yoga_2
        
        self.add_parameter('f_RO_resonator', label='RO resonator frequency',
                           unit='Hz', initial_value=0,
                           parameter_class=ManualParameter)
        self.add_parameter('Q_RO_resonator', label='RO resonator Q factor',
                           initial_value=0, parameter_class=ManualParameter)
        self.add_parameter('optimal_acquisition_delay', label='Optimal '
                           'acquisition delay', unit='s', initial_value=0,
                           parameter_class=ManualParameter)
        self.add_parameter('f_qubit_spectroscopy', label='Qubit frequency '
                           'from spectroscopy', unit='Hz', initial_value=0,
                           parameter_class=ManualParameter)
        self.add_parameter('kappa_qubit_spectroscopy',
                           label='Width of qubit from spectroscopy',
                           unit='Hz', initial_value=0,
                           parameter_class=ManualParameter)


    def prepare_for_continuous_wave(self):
        # heterodyne instrument is a separate instrument and should always be
        # prepared for cw experiments
        pass
    
    def measure_resonator_spectroscopy_vna(self, start=None, stop = None, 
                                            if_bandwidth = None,npts=None,
                                            averages = None, delay_t = 5.28e-8,
                                            segment_list = None,
                                            MC=None,power=None, measure = 'S21',
                                            
                                            analyze=True,close_fig=False):
        """use vna_instr to measure the resonator transmission
        """
        print(start, stop)
        if start  is None:
            raise ValueError("Unspecified frequency start for measure_"
                             "vna_spectroscopy")
        if stop  is None:
            raise ValueError("Unspecified frequency stop for measure_"
                             "vna_spectroscopy")
        
        if if_bandwidth and self.vna_instr.bandwidth() is None:
            raise ValueError("Unspecified if_bandwidth for measure_vna_"
                             "spectroscopy")
        self.vna_instr.bandwidth(if_bandwidth)
    
        
        if npts and self.vna_instr.npts() is None:
            raise ValueError("Unspecified npts for measure_vna_spectroscopy")
        
        if averages and self.vna_instr.avg() is None:
            raise ValueError("Unspecified averages for measure_vna_"
                             "spectroscopy")
        else:
            self.vna_instr.timeout(300)
            self.vna_instr.avg(averages)
            self.vna_instr.average_state("on")
            self.vna_instr.average_mode("POIN")
            
        
        
        if MC is None:
            MC = self.MC
            
        VNA_instr = self.vna_instr
        
        MC.set_sweep_function(swf.KST_VNA_sweep(VNA_instr,
                                                start_freq=start,
                                                stop_freq=stop,
                                                npts=npts, 
                                                if_bandwidth = if_bandwidth,
                                                power = power,
                                                delay_t = delay_t,
                                                segment_list = segment_list,
                                                measure = measure,
                                                force_reset=False))
        
        MC.set_detector_function(det.KST_VNA_detector(VNA_instr))  
        
        MC.run(name='resonator_vna_scan_frquency_{}_to_{}_power_{}_'.format(start,stop,power)+self.msmt_suffix)
        
        if analyze:
            ma.VNA_Analysis(label='resonator_vna_scan_frquency_{}_to_{}_power_{}_'.format(start,stop,power)+self.msmt_suffix,auto=True, close_fig=close_fig)
    
            
    def measure_resonator_spectroscopy_power_sweep_vna(self, start=None, stop = None, 
                                            if_bandwidth = None,npts=None,
                                            averages = None, delay_t = 5.28e-8,
                            
                                            MC=None,power_start=None, power_stop = None, power_npts = None,
                                            
                                            measure = 'S21',
                                            
                                            analyze=True,close_fig=False):
        """use vna_instr to measure the resonator transmission
        """
        print(start, stop)
        if start  is None:
            raise ValueError("Unspecified frequency start for measure_"
                             "vna_spectroscopy")
        if stop  is None:
            raise ValueError("Unspecified frequency stop for measure_"
                             "vna_spectroscopy")
        
        if power_start  is None:
            raise ValueError("Unspecified power start for measure_"
                             "vna_spectroscopy")
        if power_stop  is None:
            raise ValueError("Unspecified power stop for measure_"
                             "vna_spectroscopy")
        
        if if_bandwidth and self.vna_instr.bandwidth() is None:
            raise ValueError("Unspecified if_bandwidth for measure_vna_"
                             "spectroscopy")
        self.vna_instr.bandwidth(if_bandwidth)
    
        
        if npts and self.vna_instr.npts() is None:
            raise ValueError("Unspecified npts for measure_vna_spectroscopy")
        
        if power_npts and self.vna_instr.npts() is None:
            raise ValueError("Unspecified power npts for measure_vna_spectroscopy")
        
        if averages and self.vna_instr.avg() is None:
            raise ValueError("Unspecified averages for measure_vna_"
                             "spectroscopy")
        else:
            self.vna_instr.timeout(300)
            self.vna_instr.avg(averages)
            self.vna_instr.average_state("on")
            self.vna_instr.average_mode("POIN")
            
        
        
        if MC is None:
            MC = self.MC
            
        VNA_instr = self.vna_instr
        
        swf_fct_1D = swf.KST_VNA_sweep(VNA_instr,
                                                start_freq=start,
                                                stop_freq=stop,
                                                npts=npts, 
                                                if_bandwidth = if_bandwidth,
                                                power = power_start,
                                                delay_t = delay_t,
                                                measure = measure,
                                                force_reset=False)
        
        swf_fct_1D.prepare()
        MC.set_sweep_function(swf_fct_1D)
        MC.set_sweep_points(swf_fct_1D.sweep_points)
        
        
        MC.set_sweep_function_2D(VNA_instr.power)                 
        power_step = (power_stop-power_start)/power_npts         
        MC.set_sweep_points_2D(np.arange(power_start,
                                               power_stop,
                                               power_step))
        
        
        MC.set_detector_function(det.KST_VNA_detector(VNA_instr)) 
        
        
        file_name = 'resonator_vna_scan_frquency_{}_to_{}_power_{}_to_{}'.format(start,stop,power_start,power_stop)+self.msmt_suffix
        
        MC.run(name=file_name, mode ='2D')
        
        if analyze:
            ma.TwoD_Analysis(auto=True, label=file_name)
            
    def measure_spectroscopy_VNA_QDac(self, start=None, stop = None, 
                                            if_bandwidth = None,npts=None,
                                            averages = None, power = None,
                                            delay_t = None,
                                            qdac_channel = None, 
                                            qdac_dc_start = None,
                                            qdac_dc_stop = None,
                                            qdac_dc_npts = None,
                                            MC=None, measure = 'S21',
                                            dc_level ='low',dc_climit = 5e-7,
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         print(start, stop)
         if start  is None:
             raise ValueError("Unspecified frequency start for measure_"
                              "vna_spectroscopy")
         if stop  is None:
             raise ValueError("Unspecified frequency stop for measure_"
                              "vna_spectroscopy")
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
         
         if npts and self.vna_instr.npts() is None:
             raise ValueError("Unspecified npts for measure_vna_spectroscopy")
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
             
         
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         
         swf_fct_1D = swf.KST_VNA_sweep(VNA_instr,
                                        start_freq=start,
                                        stop_freq=stop,
                                        npts=npts, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        delay_t = delay_t,
                                        measure = measure,
                                        force_reset=False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         qdac_channel.output_mode(range='high', low_current_limit_A=5e-7)
         
         MC.set_sweep_function_2D(qdac_channel.dc_constant_V)                 
         qdac_dc_step = (qdac_dc_stop-qdac_dc_start)/qdac_dc_npts         
         MC.set_sweep_points_2D(np.arange(qdac_dc_start,
                                                qdac_dc_stop,
                                                qdac_dc_step))
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr)) 
         
         file_name = 'resonator_vna_dc_scan'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
    
    
    def measure_spectroscopy_VNA_QDac_multi_channel(self, start=None, stop = None, 
                                                         if_bandwidth = None,npts=None,
                                                         averages = None, power = None,
                                                         delay_t = None,
                                                         qdac_channel_dummy = None,
                                                         qdac_channels = None, 
                                                         qdac_dc_lists = None,
                                                         MC=None, measure = 'S21',
                                                         dc_level ='low',dc_climit = 5e-7,
                                                         analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         print(start, stop)
         if start  is None:
             raise ValueError("Unspecified frequency start for measure_"
                              "vna_spectroscopy")
         if stop  is None:
             raise ValueError("Unspecified frequency stop for measure_"
                              "vna_spectroscopy")
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
         
         if npts and self.vna_instr.npts() is None:
             raise ValueError("Unspecified npts for measure_vna_spectroscopy")
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
             
         
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         
         swf_fct_1D = swf.KST_VNA_sweep_end_trigger_multi_QDac_list_custom(VNA_instr,
                                                                    start_freq=start,
                                                                    stop_freq=stop,
                                                                    npts=npts, 
                                                                    if_bandwidth = if_bandwidth,
                                                                    power = power,
                                                                    delay_t = delay_t,
                                                                    measure = measure,
                                                                    qdac_channels = qdac_channels, 
                                                                    qdac_dc_lists = qdac_dc_lists,
                                                                    force_reset=False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         qdac_channel_dummy.output_mode(range='high', low_current_limit_A=5e-7)
         
         MC.set_sweep_function_2D(qdac_channel_dummy.dc_constant_V)                 
         qdac_dc_step = (1.0-0.0)/qdac_dc_lists.shape[1]      
         MC.set_sweep_points_2D(np.arange(0.0,
                                          1.0,
                                          qdac_dc_step))
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr)) 
         
         file_name = 'resonator_vna_dc_scan'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
             
    def measure_spectroscopy_VNA_Yoga(self, start=None, stop = None, 
                                            if_bandwidth = None,npts=None,
                                            averages = None, power = None,
                                            delay_t = None,
                                            yoga_instr = None, 
                                            yoga_dc_start = None,
                                            yoga_dc_stop = None,
                                            yoga_dc_npts = None,
                                            MC=None, 
                                            measure = 'S21',
                                            dc_level ='low',dc_climit = 5e-7,
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         print(start, stop)
         if start  is None:
             raise ValueError("Unspecified frequency start for measure_"
                              "vna_spectroscopy")
         if stop  is None:
             raise ValueError("Unspecified frequency stop for measure_"
                              "vna_spectroscopy")
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
         
         if npts and self.vna_instr.npts() is None:
             raise ValueError("Unspecified npts for measure_vna_spectroscopy")
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
             
         
         
         if MC is None:
             MC = self.MC
         
         
         VNA_instr = self.vna_instr
         
         swf_fct_1D = swf.KST_VNA_sweep(VNA_instr,
                                        start_freq=start,
                                        stop_freq=stop,
                                        npts=npts, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        delay_t = delay_t,
                                        measure = measure,
                                        force_reset=False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         #yoga_instr.source_mode('VOLT') 
         yoga_instr.voltage_range(1e0)
         yoga_instr.voltage(yoga_dc_start)
         yoga_instr.output('on')
         MC.set_sweep_function_2D(yoga_instr.voltage)                 
         yoga_dc_step = (yoga_dc_stop-yoga_dc_start)/yoga_dc_npts         
         MC.set_sweep_points_2D(np.arange(yoga_dc_start,
                                                yoga_dc_stop,
                                                yoga_dc_step))
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr)) 
         
         file_name = 'resonator_vna_dc_scan'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
            
    def measure_single_freq_QDac_2D(self,   freq=None, 
                                            if_bandwidth = None,
                                            averages = None, 
                                            power = None,
                                            delay_t = 5.38e-8,
                                            qdac_channel_1 = None, 
                                            qdac_channel_2 = None,
                                            qdac_ch1_start = None,
                                            qdac_ch1_stop = None,
                                            qdac_ch1_npts = None,
                                            qdac_ch2_start = None,
                                            qdac_ch2_stop = None,
                                            qdac_ch2_npts = None,
                                            MC=None, measure = 'S21',
                                            dc_level ='low',dc_climit = 5e-7,
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         if freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         QDac_instr = self.QDac_instr
         
         qdac_channel_1.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         time.sleep(0.5)
         
         print(QDac_instr)
         swf_fct_1D = swf.KST_VNA_single_freq_QDac_list(VNA_instr, QDac_instr,
                                        freq=freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        averages = averages, 
                                        measure =measure,
                                        delay_t = delay_t,
                                        qdac_channel_1 = qdac_channel_1, 
                                        qdac_ch1_start = qdac_ch1_start,
                                        qdac_ch1_stop = qdac_ch1_stop,
                                        qdac_ch1_npts = qdac_ch1_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         qdac_channel_2.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         time.sleep(0.5)
         qdac_channel_2.output_filter('med')
         time.sleep(0.5)
         MC.set_sweep_function_2D(qdac_channel_2.dc_constant_V)
                 
         #qdac_dc_step = (qdac_dc_stop-qdac_dc_start)/qdac_dc_npts 
         
         ''' set the second QDac channel to the initial DC Voltage'''
         qdac_channel_2.dc_constant_V(qdac_ch2_start)

         
         MC.set_sweep_points_2D(np.linspace(qdac_ch2_start,
                                            qdac_ch2_stop,
                                            qdac_ch2_npts))
         
         MC.set_detector_function(det.KST_VNA_QDac_list_detector(VNA_instr,qdac_channel_1,qdac_channel_2)) 
         
         file_name = 'resonator_vna_dc_scan'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             _ma = ma.TwoD_Analysis(auto=True, label=file_name)
             
             self.sweep_points = _ma.sweep_points
             self.sweep_points_2D = _ma.sweep_points_2D
             self.measured_values = _ma.measured_values
    
    def measure_single_freq_QDac_1D(self,   freq=None, 
                                            if_bandwidth = None,
                                            averages = None, 
                                            power = None,
                                            delay_t = 5.38e-8,
                                            qdac_channel_1 = None, 
                                            qdac_ch1_start = None,
                                            qdac_ch1_stop = None,
                                            qdac_ch1_npts = None,
                                            MC=None, measure = 'S21',
                                            dc_level ='low',dc_climit = 5e-7,
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         if freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         QDac_instr = self.QDac_instr
         
         qdac_channel_1.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         time.sleep(0.5)
         
         print(QDac_instr)
         swf_fct_1D = swf.KST_VNA_single_freq_QDac_list(VNA_instr, QDac_instr,
                                        freq=freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        averages = averages, 
                                        measure =measure,
                                        delay_t = delay_t,
                                        qdac_channel_1 = qdac_channel_1, 
                                        qdac_ch1_start = qdac_ch1_start,
                                        qdac_ch1_stop = qdac_ch1_stop,
                                        qdac_ch1_npts = qdac_ch1_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         # qdac_channel_2.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         # time.sleep(0.5)
         # qdac_channel_2.output_filter('med')
         # time.sleep(0.5)
         # MC.set_sweep_function_2D(qdac_channel_2.dc_constant_V)
                 
         # #qdac_dc_step = (qdac_dc_stop-qdac_dc_start)/qdac_dc_npts 
         
         # ''' set the second QDac channel to the initial DC Voltage'''
         # qdac_channel_2.dc_constant_V(qdac_ch2_start)

         
         # MC.set_sweep_points_2D(np.linspace(qdac_ch2_start,
         #                                    qdac_ch2_stop,
         #                                    qdac_ch2_npts))
         
         # MC.set_detector_function(det.KST_VNA_QDac_list_detector(VNA_instr,qdac_channel_1,qdac_channel_2)) 
         MC.set_detector_function(det.KST_VNA_QDac_list_detector(VNA_instr,qdac_channel_1,qdac_channel_1)) 
         
         file_name = 'resonator_vna_dc_scan'+self.msmt_suffix
         MC.run(name=file_name, mode ='1D')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             _ma = ma.TwoD_Analysis(auto=True, label=file_name)
             
             self.sweep_points = _ma.sweep_points
             # self.sweep_points_2D = _ma.sweep_points_2D
             self.measured_values = _ma.measured_values 
    def measure_single_freq_QDac_yoga_2D(self,   freq=None, 
                                            if_bandwidth = None,
                                            averages = None, 
                                            power = None,
                                            delay_t = 5.38e-8,
                                            qdac_channel_1 = None, 
                                            yoga_instr = None,
                                            qdac_ch1_start = None,
                                            qdac_ch1_stop = None,
                                            qdac_ch1_npts = None,
                                            yoga_dc_start = None,
                                            yoga_dc_stop = None,
                                            yoga_dc_npts = None,
                                            MC=None, measure = 'S21',
                                            dc_level ='low',dc_climit = 5e-7,
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         if freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         QDac_instr = self.QDac_instr
         
         qdac_channel_1.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         time.sleep(0.5)
         
         print(QDac_instr)
         swf_fct_1D = swf.KST_VNA_single_freq_QDac_list(VNA_instr, QDac_instr,
                                        freq=freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        averages = averages, 
                                        measure =measure,
                                        delay_t = delay_t,
                                        qdac_channel_1 = qdac_channel_1, 
                                        qdac_ch1_start = qdac_ch1_start,
                                        qdac_ch1_stop = qdac_ch1_stop,
                                        qdac_ch1_npts = qdac_ch1_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         #yoga_instr.source_mode('VOLT') 
         time.sleep(0.5)
         yoga_instr.voltage_range(1e0)
         time.sleep(0.5)
         yoga_instr.voltage(yoga_dc_start)
         time.sleep(0.5)
         yoga_instr.output('on')
         
         #qdac_channel_2.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         #time.sleep(0.5)
         #qdac_channel_2.output_filter('med')
         #time.sleep(0.5)
         MC.set_sweep_function_2D(yoga_instr.voltage)
                 
         #qdac_dc_step = (qdac_dc_stop-qdac_dc_start)/qdac_dc_npts 
         
         ''' set the second QDac channel to the initial DC Voltage'''
        # qdac_channel_2.dc_constant_V(qdac_ch2_start)

         
         MC.set_sweep_points_2D(np.linspace(yoga_dc_start,
                                            yoga_dc_stop,
                                            yoga_dc_npts))
         
         MC.set_detector_function(det.KST_VNA_QDac_list_yoga_step_detector(VNA_instr,qdac_channel_1,yoga_instr)) 
         
         file_name = 'resonator_vna_dc_scan'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
             
    def measure_two_tone_pump_sweep(self,    probe_freq=None, 
                                            if_bandwidth = None,
                                            delay_t = None,
                                            averages = None, 
                                            probe_power=None,
                                            pump_freq_start = None,
                                            pump_freq_stop = None,
                                            pump_f_npts = None,
                                            pump_power_start = None,
                                            pump_power_stop = None,
                                            pump_power_npts = None,
                                            MC=None, measure = 'S21',                                          
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         if probe_freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
             
         else:
             ''' Prepare the VNA '''
             self.vna_instr.continuous_mode_all('off')  # measure only if required
             # optimize the sweep time for the fastest measurement
             self.vna_instr.min_sweep_time('on')
             # start a measurement once the trigger signal arrives
             self.vna_instr.trigger_source('MAN')
             
             # setup which parameter to measure
             str_to_write = "CALC:MEAS:PAR '%s'" % measure
             print(str_to_write)
             self.vna_instr.visa_handle.write(str_to_write)
             
             self.vna_instr.start_frequency(probe_freq)
             self.vna_instr.stop_frequency(probe_freq)
             self.vna_instr.npts(1)
             
             # trigger signal is generated with the command:
             # VNA.start_sweep_all()
             
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         else: 
             self.vna_instr.bandwidth(if_bandwidth)
        
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
             
         self.vna_instr.rf_on()
         self.sgen_instr.on('ON')
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         sgen_instr = self.sgen_instr
         
         VNA_instr.power(probe_power)
         
         swf_fct_1D = swf.KST_VNA_single_freq_Anritsu_list_manual_trigger(VNA_instr, sgen_instr,
                                        freq=probe_freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = probe_power,
                                        averages = averages, 
                                        measure ='S21',
                                        delay_t = delay_t,
                                        
                                        pump_power = pump_power_start,
                                        pump_f_start = pump_freq_start,
                                        pump_f_stop = pump_freq_stop,
                                        pump_f_npts = pump_f_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
        
         MC.set_sweep_function_2D(sgen_instr.power)
                 
         #qdac_dc_step = (qdac_dc_stop-qdac_dc_start)/qdac_dc_npts 
         
         ''' set the second QDac channel to the initial DC Voltage'''
         #qdac_channel_2.dc_constant_V(qdac_ch2_start)

         
         MC.set_sweep_points_2D(np.linspace(pump_power_start,
                                            pump_power_stop,
                                            pump_power_npts))
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr)) 
        
         file_name = 'qubit_two_tone_scan_qubit_freq_VS_pump_power'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         #self.VNA.wait_to_continue()
         #self.vna_instr.rf_off() #turn off the VNA
         #self.sgen_instr.on('OFF')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
    
    def measure_two_tone_pump(self,    probe_freq=None, 
                                            if_bandwidth = None,
                                            delay_t = None,
                                            averages = None, 
                                            probe_power=None,
                                            pump_freq_start = None,
                                            pump_freq_stop = None,
                                            pump_f_npts = None,
                                            pump_power = None,
                                            MC=None, measure = 'S21',                                          
                                            analyze=False,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         if probe_freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
             
         else:
             ''' Prepare the VNA '''
             self.vna_instr.continuous_mode_all('off')  # measure only if required
             # optimize the sweep time for the fastest measurement
             self.vna_instr.min_sweep_time('on')
             # start a measurement once the trigger signal arrives
             self.vna_instr.trigger_source('MAN')
             
             # setup which parameter to measure
             str_to_write = "CALC:MEAS:PAR '%s'" % measure
             print(str_to_write)
             self.vna_instr.visa_handle.write(str_to_write)
             
             self.vna_instr.start_frequency(probe_freq)
             self.vna_instr.stop_frequency(probe_freq)
             self.vna_instr.npts(1)
             
             # trigger signal is generated with the command:
             # VNA.start_sweep_all()
             
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         else: 
             self.vna_instr.bandwidth(if_bandwidth)
        
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else:
             self.vna_instr.timeout(1200)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
             
         self.vna_instr.rf_on()
         self.sgen_instr.on('ON')
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         sgen_instr = self.sgen_instr
         
         VNA_instr.power(probe_power)
         
         swf_fct_1D = swf.KST_VNA_single_freq_Anritsu_list_manual_trigger(VNA_instr, sgen_instr,
                                        freq=probe_freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = probe_power,
                                        averages = averages, 
                                        measure ='S21',
                                        delay_t = delay_t,
                                        
                                        pump_power = pump_power,
                                        pump_f_start = pump_freq_start,
                                        pump_f_stop = pump_freq_stop,
                                        pump_f_npts = pump_f_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
        
         #MC.set_sweep_function_2D(sgen_instr.power)
                 
         #qdac_dc_step = (qdac_dc_stop-qdac_dc_start)/qdac_dc_npts 
         
         ''' set the second QDac channel to the initial DC Voltage'''
         #qdac_channel_2.dc_constant_V(qdac_ch2_start)

         
         #MC.set_sweep_points_2D(np.linspace(pump_power_start,
                                            #pump_power_stop,
                                            #pump_power_npts))
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr)) 
         
         file_name = 'qubit_two_tone_scan_qubit'+self.msmt_suffix
         MC.run(name=file_name, mode ='1D')
         
         #self.VNA.wait_to_continue()
         #self.vna_instr.rf_off() #turn off the VNA
         #self.sgen_instr.on('OFF')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.VNA_Analysis(label=file_name,auto=True,close_fig=close_fig) 
     
    def measure_two_tone_QDac(self,     probe_freq=None, 
                                        if_bandwidth = None,
                                        averages = None, 
                                        power = None,
                                        delay_t = 5.38e-8,
                                        
                                        pump_power = None,
                                        pump_freq_start = None,
                                        pump_freq_stop = None,
                                        pump_f_npts = None,
                                        
                                        qdac_channel = None, 
                                        qdac_dc_start = None,
                                        qdac_dc_stop = None,
                                        qdac_dc_npts = None,
                                        
                                        dc_level ='low',dc_climit = 5e-7,
                                        
                                        MC=None, measure = 'S21',
                                        analyze=True,close_fig=False):
        
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         #print(start, stop)
         if probe_freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         QDac_instr = self.QDac_instr
         sgen_instr = self.sgen_instr
         
         self.vna_instr.rf_on()
         self.sgen_instr.power(pump_power)
         self.sgen_instr.on('ON')
         
         qdac_channel.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         time.sleep(0.5)
         
         print(QDac_instr)
         swf_fct_1D = swf.KST_VNA_single_freq_QDac_list(VNA_instr, QDac_instr,
                                        freq=probe_freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        averages = averages, 
                                        measure =measure,
                                        delay_t = delay_t,
                                        qdac_channel_1 = qdac_channel, 
                                        qdac_ch1_start = qdac_dc_start,
                                        qdac_ch1_stop = qdac_dc_stop,
                                        qdac_ch1_npts = qdac_dc_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
             
         
         
     
         MC.set_sweep_function_2D(sgen_instr.frequency)         
         MC.set_sweep_points_2D(np.linspace(pump_freq_start,
                                          pump_freq_stop,
                                          pump_f_npts))

                 

         
         MC.set_detector_function(det.KST_VNA_QDac_list_two_tone_detector(VNA_instr,qdac_channel)) 
         
         file_name = 'qubit_two_tone_scan_qubit_freq_VS_QDac'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         #self.VNA.wait_to_continue()
         #self.vna_instr.rf_off() #turn off the VNA
         #self.sgen_instr.on('OFF')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
             
    def measure_two_tone_step_QDac_sweep_Fp(self,     probe_freq=None, 
                                                      if_bandwidth = None,
                                                      averages = None, 
                                                      power = None,
                                                      delay_t = 5.38e-8,
                                        
                                                      pump_power = None,
                                                      pump_freq_start = None,
                                                      pump_freq_stop = None,
                                                      pump_freq_npts = None,
                                        
                                                      qdac_channel = None, 
                                                      qdac_dc_start = None,
                                                      qdac_dc_stop = None,
                                                      qdac_dc_npts = None,
                                        
                                                      dc_level ='low',dc_climit = 5e-7,
                                        
                                                      MC=None, measure = 'S21',
                                                      analyze=True,close_fig=False):
        
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         #print(start, stop)
         if probe_freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         QDac_instr = self.QDac_instr
         sgen_instr = self.sgen_instr
         
         self.vna_instr.rf_on()
         #self.sgen_instr.power(pump_power)
         #self.sgen_instr.on('ON')
         
         qdac_channel.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         time.sleep(0.5)
         
         print(QDac_instr)
         swf_fct_1D = swf.KST_VNA_single_freq_Anritsu_list_manual_trigger(VNA_instr, sgen_instr,
                                        freq=probe_freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        averages = averages, 
                                        measure ='S21',
                                        delay_t = delay_t,
                                        
                                        pump_power = pump_power,
                                        pump_f_start = pump_freq_start,
                                        pump_f_stop = pump_freq_stop,
                                        pump_f_npts = pump_freq_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
             
         
         
     
         MC.set_sweep_function_2D(qdac_channel.dc_constant_V)         
         MC.set_sweep_points_2D(np.linspace(qdac_dc_start,
                                          qdac_dc_stop,
                                          qdac_dc_npts))

                 

         
         MC.set_detector_function(det.KST_VNA_Anritsu_list_two_tone_detector(VNA_instr,sgen_instr)) 
         
         file_name = 'qubit_two_tone_scan_qubit_freq_VS_QDac_sweep_fp'+self.msmt_suffix
         
         print("list_index before run",sgen_instr.list_index())
         
         sgen_instr.list_index(0)
         MC.run(name=file_name, mode ='2D')
         
         print("list_index after run",sgen_instr.list_index())
         #self.VNA.wait_to_continue()
         #self.vna_instr.rf_off() #turn off the VNA
         #self.sgen_instr.on('OFF')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
    
    def measure_two_tone_step_yoga_sweep_Fp(self,     probe_freq=None, 
                                                      if_bandwidth = None,
                                                      averages = None, 
                                                      power = None,
                                                      delay_t = 5.38e-8,
                                        
                                                      pump_power = None,
                                                      pump_freq_start = None,
                                                      pump_freq_stop = None,
                                                      pump_freq_npts = None,
                                        
                                                      yoga_instr = None, 
                                                      yoga_dc_start = None,
                                                      yoga_dc_stop = None,
                                                      yoga_dc_npts = None,
                                        
                                                      dc_level ='low',dc_climit = 5e-7,
                                        
                                                      MC=None, measure = 'S21',
                                                      analyze=True,close_fig=False):
        
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         #print(start, stop)
         if probe_freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         #QDac_instr = self.QDac_instr
         sgen_instr = self.sgen_instr
         
         self.vna_instr.rf_on()
         #self.sgen_instr.power(pump_power)
         #self.sgen_instr.on('ON')
         
         
         
         #print(QDac_instr)
         swf_fct_1D = swf.KST_VNA_single_freq_Anritsu_list_manual_trigger(VNA_instr, sgen_instr,
                                        freq=probe_freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        averages = averages, 
                                        measure ='S21',
                                        delay_t = delay_t,
                                        
                                        pump_power = pump_power,
                                        pump_f_start = pump_freq_start,
                                        pump_f_stop = pump_freq_stop,
                                        pump_f_npts = pump_freq_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
           
        
         #yoga_instr.source_mode('VOLT') 
         time.sleep(0.5)
         yoga_instr.voltage_range(1e0)
         time.sleep(0.5)
         yoga_instr.voltage(yoga_dc_start)
         time.sleep(0.5)
         yoga_instr.output('on')
         
         
     
         MC.set_sweep_function_2D(yoga_instr.voltage)         
         MC.set_sweep_points_2D(np.linspace(yoga_dc_start,
                                          yoga_dc_stop,
                                          yoga_dc_npts))

                 

         
         MC.set_detector_function(det.KST_VNA_Anritsu_list_two_tone_detector(VNA_instr,sgen_instr)) 
         
         file_name = 'qubit_two_tone_scan_qubit_freq_VS_QDac_sweep_fp'+self.msmt_suffix
         
         print("list_index before run",sgen_instr.list_index())
         
         sgen_instr.list_index(0)
         MC.run(name=file_name, mode ='2D')
         
         print("list_index after run",sgen_instr.list_index())
         #self.VNA.wait_to_continue()
         #self.vna_instr.rf_off() #turn off the VNA
         #self.sgen_instr.on('OFF')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
    
    def measure_two_tone_power_QDac(self,     probe_freq=None, 
                                        if_bandwidth = None,
                                        averages = None, 
                                        power = None,
                                        delay_t = 5.38e-8,
                                        
                                        pump_freq = None,
                                        pump_power_start = None,
                                        pump_power_stop = None,
                                        pump_power_npts = None,
                                        
                                        qdac_channel = None, 
                                        qdac_dc_start = None,
                                        qdac_dc_stop = None,
                                        qdac_dc_npts = None,
                                        
                                        dc_level ='low',dc_climit = 5e-7,
                                        
                                        MC=None, measure = 'S21',
                                        analyze=True,close_fig=False):
        
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         #print(start, stop)
         if probe_freq  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         QDac_instr = self.QDac_instr
         sgen_instr = self.sgen_instr
         
         self.vna_instr.rf_on()
         self.sgen_instr.frequency(pump_freq)
         self.sgen_instr.on('ON')
         
         self.vna_instr.avg(averages)
         self.vna_instr.average_state("on")
         self.vna_instr.average_mode("POIN")
         
         qdac_channel.output_mode(range=dc_level, low_current_limit_A=dc_climit)
         time.sleep(0.5)
         
         print(QDac_instr)
         swf_fct_1D = swf.KST_VNA_single_freq_QDac_list(VNA_instr, QDac_instr,
                                        freq=probe_freq, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        averages = averages, 
                                        measure =measure,
                                        delay_t = delay_t,
                                        qdac_channel_1 = qdac_channel, 
                                        qdac_ch1_start = qdac_dc_start,
                                        qdac_ch1_stop = qdac_dc_stop,
                                        qdac_ch1_npts = qdac_dc_npts,
                                        force_reset   = False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         
         MC.set_sweep_points(swf_fct_1D.sweep_points)
             
         
         
     
         MC.set_sweep_function_2D(sgen_instr.power)         
         MC.set_sweep_points_2D(np.linspace(pump_power_start,
                                          pump_power_stop,
                                          pump_power_npts))

                 

         
         MC.set_detector_function(det.KST_VNA_QDac_list_two_tone_detector(VNA_instr,qdac_channel)) 
         
         file_name = 'qubit_two_tone_scan_qubit_freq_VS_QDac'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         #self.VNA.wait_to_continue()
         #self.vna_instr.rf_off() #turn off the VNA
         #self.sgen_instr.on('OFF')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
             
    
    def measure_two_tone_probe_sweep(self,  pump_power=None,
                                            pump_freq_start = None,
                                            pump_freq_stop = None,
                                            pump_f_npts = None,
                                            
                                            probe_power= None,
                                            probe_freq_start = None,
                                            probe_freq_stop = None,
                                            probe_f_npts = None,
                                            delay_t = None,
                                            if_bandwidth = None,
                                            averages = None,
                                            
                                            MC=None, measure = 'S21',                                          
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         if probe_freq_start  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
             
         else:
             ''' Prepare the VNA '''
             self.vna_instr.continuous_mode_all('off')  # measure only if required
             # optimize the sweep time for the fastest measurement
             self.vna_instr.min_sweep_time('on')
             # start a measurement once the trigger signal arrives
             self.vna_instr.trigger_source('MAN')
             
             # setup which parameter to measure
             str_to_write = "CALC:MEAS:PAR '%s'" % measure
             print(str_to_write)
             self.vna_instr.visa_handle.write(str_to_write)
             
             #self.vna_instr.start_frequency(probe_freq)
             #self.vna_instr.stop_frequency(probe_freq)
             #self.vna_instr.npts(1)
             
             # trigger signal is generated with the command:
             # VNA.start_sweep_all()
             
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         else: 
             self.vna_instr.bandwidth(if_bandwidth)
        
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else:
             self.vna_instr.timeout(300)
             self.vna_instr.avg(averages)
             self.vna_instr.average_state("on")
             self.vna_instr.average_mode("POIN")
             
         self.vna_instr.rf_on()
         self.sgen_instr.on('ON')
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         sgen_instr = self.sgen_instr
         
         sgen_instr.power(pump_power)
         
         swf_fct_1D = swf.KST_VNA_sweep(VNA_instr,
                                        start_freq=probe_freq_start,
                                        stop_freq=probe_freq_stop,
                                        npts=probe_f_npts, 
                                        if_bandwidth = if_bandwidth,
                                        power = probe_power,
                                        delay_t = delay_t,
                                        measure = measure,
                                        force_reset=False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         MC.set_sweep_function_2D(sgen_instr.frequency)         
         MC.set_sweep_points_2D(np.linspace(pump_freq_start,
                                          pump_freq_stop,
                                          pump_f_npts))
        
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr)) 
         
         file_name = 'qubit_two_tone_scan_qubit_freq_VS_probe_prequency'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         #self.VNA.wait_to_continue()
         #self.vna_instr.rf_off() #turn off the VNA
         #self.sgen_instr.on('OFF')
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
            
                  
        
    def measure_heterodyne_spectroscopy(self, freqs=None, MC=None,
                                        analyze=True, close_fig=True):
        """ Varies the frequency of the microwave source to the resonator and
        measures the transmittance """
        if freqs is None:
            raise ValueError("Unspecified frequencies for measure_heterodyne_"
                             "spectroscopy")

        if MC is None:
            MC = self.MC

        previous_freq = self.heterodyne_instr.frequency()

        self.prepare_for_continuous_wave()
        MC.set_sweep_function(pw.wrap_par_to_swf(
            self.heterodyne_instr.frequency))
        MC.set_sweep_points(freqs)
        MC.set_detector_function(det.Heterodyne_probe(
            self.heterodyne_instr, trigger_separation=5e-6,
            demod_mode='single'))
        MC.run(name='resonator_scan'+self.msmt_suffix)

        self.heterodyne_instr.frequency(previous_freq)

        if analyze:
            ma.MeasurementAnalysis(auto=True, close_fig=close_fig)

    def measure_homodyne_acqusition_delay(self, delays=None, MC=None,
                                          analyze=True, close_fig=True):
        """
        Varies the delay between the homodyne modulation signal and
        acquisition. Measures the transmittance.
        """
        if delays is None:
            raise ValueError("Unspecified delays for measure_homodyne_"
                             "acquisition_delay")

        if MC is None:
            MC = self.MC

        # set number of averages to 1 due to a readout bug
        previous_nr_averages = self.heterodyne_instr.nr_averages()
        self.heterodyne_instr.nr_averages(1)
        previous_delay = self.heterodyne_instr.acquisition_delay()

        self.prepare_for_continuous_wave()
        MC.set_sweep_function(pw.wrap_par_to_swf(
            self.heterodyne_instr.acquisition_delay))
        MC.set_sweep_points(delays)
        MC.set_detector_function(det.Heterodyne_probe(
            self.heterodyne_instr, trigger_separation=5e-6,
            demod_mode='single'))
        MC.run(name='acquisition_delay_scan'+self.msmt_suffix)

        self.heterodyne_instr.acquisition_delay(previous_delay)
        self.heterodyne_instr.nr_averages(previous_nr_averages)

        if analyze:
            ma.MeasurementAnalysis(auto=True, close_fig=close_fig)

    def measure_spectroscopy(self, freqs=None, MC=None, analyze=True,
                             close_fig=True, update=False):
        """ Varies qubit drive frequency and measures the resonator
        transmittance """
        if freqs is None:
            raise ValueError("Unspecified frequencies for "
                                 "measure_spectroscopy and no previous value")

        if MC is None:
            MC = self.MC

        self.prepare_for_continuous_wave()
        self.cw_source.on()

        MC.set_sweep_function(pw.wrap_par_to_swf(self.cw_source.frequency))
        MC.set_sweep_points(freqs)
        MC.set_detector_function(det.Heterodyne_probe(
            self.heterodyne_instr, trigger_separation=2.8e-6,
            demod_mode='single'))
        MC.run(name='spectroscopy'+self.msmt_suffix)

        self.cw_source.off()

        if analyze:
            ma.MeasurementAnalysis(auto=True, close_fig=close_fig)
    
    def measure_JPA_flux_sweep(self,        start=None, stop = None, 
                                            if_bandwidth = None,npts=None,
                                            averages = None, power = None,
                                            delay_t = None,
                                            
                                            flux_start = None,
                                            flux_stop = None,
                                            flux_npts = None,
                                            
                                            MC=None, measure = 'S21',
            
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         print(start, stop)
         if start  is None:
             raise ValueError("Unspecified frequency start for measure_"
                              "vna_spectroscopy")
         if stop  is None:
             raise ValueError("Unspecified frequency stop for measure_"
                              "vna_spectroscopy")
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         self.vna_instr.bandwidth(if_bandwidth)
     
         
         if npts and self.vna_instr.npts() is None:
             raise ValueError("Unspecified npts for measure_vna_spectroscopy")
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         self.vna_instr.avg(averages)
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         gs_instr  = self.gs_instr
         
         swf_fct_1D = swf.KST_VNA_sweep(VNA_instr,
                                        start_freq=start,
                                        stop_freq=stop,
                                        npts=npts, 
                                        if_bandwidth = if_bandwidth,
                                        power = power,
                                        delay_t = delay_t,
                                        measure = measure,
                                        force_reset=False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         gs_instr.off()
         gs_instr.source_mode('CURR')
         gs_instr.current_range(1e-3)
         gs_instr.current_limit(1e-3)
         gs_instr.current(0.0)
         gs_instr.on()
         gs_instr.ramp_current(ramp_to = flux_start, step = 100,delay = 1e-3)
         
         MC.set_sweep_function_2D(gs_instr.current)                 
         flux_step = (flux_stop-flux_start)/(flux_npts-1)         
         MC.set_sweep_points_2D(np.arange(flux_start,
                                          flux_stop,
                                          flux_step))
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr)) 
         
         file_name = 'JPA_vna_flux_scan'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')
         
         gs_instr.ramp_current(ramp_to = 0.0, step = 100,delay = 1e-3)
         gs_instr.off()
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
    
    def measure_JPA_pump_power_sweep(self,  probe_start=None, probe_stop = None, 
                                            if_bandwidth = None,probe_npts=None,
                                            averages = None, probe_power = None,
                                            delay_t = None,
                                            
                                        
                                            pump_freq = None,
                                            pump_power_start = None,
                                            pump_power_stop = None,
                                            pump_power_npts = None,
                                            
                                            flux_current = None,
                                            
                                            MC=None, measure = 'S21',                                          
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         if probe_start  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
             
         else:
             ''' Prepare the VNA '''
             self.vna_instr.continuous_mode_all('off')  # measure only if required
             # optimize the sweep time for the fastest measurement
             self.vna_instr.min_sweep_time('on')
             # start a measurement once the trigger signal arrives
             self.vna_instr.trigger_source('MAN')
             
             # setup which parameter to measure
             str_to_write = "CALC:MEAS:PAR '%s'" % measure
             print(str_to_write)
             self.vna_instr.visa_handle.write(str_to_write)
             
             #self.vna_instr.start_frequency(probe_freq)
             #self.vna_instr.stop_frequency(probe_freq)
             #self.vna_instr.npts(1)
             
             # trigger signal is generated with the command:
             # VNA.start_sweep_all()
             
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         else: 
             self.vna_instr.bandwidth(if_bandwidth)
        
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else: 
             self.vna_instr.avg(averages)
             
         
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         sgen_instr = self.sgen_instr
         gs_instr  = self.gs_instr
         
         
         
         gs_instr.off()
         gs_instr.source_mode('CURR')
         gs_instr.current_range(1e-3)
         gs_instr.current_limit(1e-3)
         gs_instr.current(0.0)
         gs_instr.on()
         gs_instr.ramp_current(ramp_to = flux_current, step = 100,delay = 1e-3)
         
         
         VNA_instr.rf_on()
         
         
         VNA_instr.power(probe_power)
         
         swf_fct_1D = swf.KST_VNA_sweep(VNA_instr,
                                        start_freq=probe_start,
                                        stop_freq=probe_stop,
                                        npts=probe_npts, 
                                        if_bandwidth = if_bandwidth,
                                        power = probe_power,
                                        delay_t = delay_t,
                                        measure = measure,
                                        force_reset=False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         sgen_instr.on('OFF')
         sgen_instr.frequency(pump_freq)
         sgen_instr.power(-20)
         sgen_instr.on('ON')
         
 
         MC.set_sweep_function_2D(sgen_instr.power)
                 
         #qdac_dc_step = (qdac_dc_stop-qdac_dc_start)/qdac_dc_npts 
         
         ''' set the second QDac channel to the initial DC Voltage'''
         #qdac_channel_2.dc_constant_V(qdac_ch2_start)

         
         MC.set_sweep_points_2D(np.linspace(pump_power_start,
                                            pump_power_stop,
                                            pump_power_npts))
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr))  
         
         file_name = 'JPA_calibration_pump_power'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')      
         
         
         sgen_instr.on('OFF')
         gs_instr.ramp_current(ramp_to = 0.0, step = 100,delay = 1e-3)
         gs_instr.off()
         
         
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)
             
    
    def measure_JPA_pump_freq_sweep(self,  probe_start=None, probe_stop = None, 
                                            if_bandwidth = None,probe_npts=None,
                                            averages = None, probe_power = None,
                                            delay_t = None,
                                            
                                        
                                            pump_power = None,
                                            pump_freq_start = None,
                                            pump_freq_stop = None,
                                            pump_freq_npts = None,
                                            
                                            flux_current = None,
                                            
                                            MC=None, measure = 'S21',                                          
                                            analyze=True,close_fig=False):
         """use vna_instr to measure the resonator transmission
         """
         #print(start, stop)
         if probe_start  is None:
             raise ValueError("Unspecified frequency for measure_"
                              "vna_spectroscopy")
             
         else:
             ''' Prepare the VNA '''
             self.vna_instr.continuous_mode_all('off')  # measure only if required
             # optimize the sweep time for the fastest measurement
             self.vna_instr.min_sweep_time('on')
             # start a measurement once the trigger signal arrives
             self.vna_instr.trigger_source('MAN')
             
             # setup which parameter to measure
             str_to_write = "CALC:MEAS:PAR '%s'" % measure
             print(str_to_write)
             self.vna_instr.visa_handle.write(str_to_write)
             
             #self.vna_instr.start_frequency(probe_freq)
             #self.vna_instr.stop_frequency(probe_freq)
             #self.vna_instr.npts(1)
             
             # trigger signal is generated with the command:
             # VNA.start_sweep_all()
             
         
         
         if if_bandwidth and self.vna_instr.bandwidth() is None:
             raise ValueError("Unspecified if_bandwidth for measure_vna_"
                              "spectroscopy")
         else: 
             self.vna_instr.bandwidth(if_bandwidth)
        
     
         
         if averages and self.vna_instr.avg() is None:
             raise ValueError("Unspecified averages for measure_vna_"
                              "spectroscopy")
             
         else: 
             self.vna_instr.avg(averages)
             
         
         
         if MC is None:
             MC = self.MC
             
         VNA_instr = self.vna_instr
         sgen_instr = self.sgen_instr
         gs_instr  = self.gs_instr
         
         
         
         gs_instr.off()
         gs_instr.source_mode('CURR')
         gs_instr.current_range(1e-3)
         gs_instr.current_limit(1e-3)
         gs_instr.current(0.0)
         gs_instr.on()
         gs_instr.ramp_current(ramp_to = flux_current, step = 100,delay = 1e-3)
         
         
         VNA_instr.rf_on()
         
         
         VNA_instr.power(probe_power)
         
         swf_fct_1D = swf.KST_VNA_sweep(VNA_instr,
                                        start_freq=probe_start,
                                        stop_freq=probe_stop,
                                        npts=probe_npts, 
                                        if_bandwidth = if_bandwidth,
                                        power = probe_power,
                                        delay_t = delay_t,
                                        measure = measure,
                                        force_reset=False)
         swf_fct_1D.prepare()
         
         MC.set_sweep_function(swf_fct_1D)
         MC.set_sweep_points(swf_fct_1D.sweep_points)
         
         sgen_instr.on('OFF')
         sgen_instr.frequency(pump_freq_start)
         sgen_instr.power(pump_power)
         sgen_instr.on('ON')
         
 
         MC.set_sweep_function_2D(sgen_instr.frequency)
                 
         #qdac_dc_step = (qdac_dc_stop-qdac_dc_start)/qdac_dc_npts 
         
         ''' set the second QDac channel to the initial DC Voltage'''
         #qdac_channel_2.dc_constant_V(qdac_ch2_start)

         
         MC.set_sweep_points_2D(np.linspace(pump_freq_start,
                                            pump_freq_stop,
                                            pump_freq_npts))
         
         MC.set_detector_function(det.KST_VNA_detector(VNA_instr))  
         
         file_name = 'JPA_calibration_pump_freq'+self.msmt_suffix
         MC.run(name=file_name, mode ='2D')      
         
         
         sgen_instr.on('OFF')
         gs_instr.ramp_current(ramp_to = 0.0, step = 100,delay = 1e-3)
         gs_instr.off()
         
         
         
         if analyze:
             #ma.VNA_Analysis(label='resonator_vna_scan'+self.msmt_suffix,auto=True, close_fig=close_fig)
             ma.TwoD_Analysis(auto=True, label=file_name)

    def measure_rabi(self):
        raise NotImplementedError()

    def measure_T1(self):
        raise NotImplementedError()

    def measure_ramsey(self):
        raise NotImplementedError()

    def measure_echo(self):
        raise NotImplementedError()

    def measure_allxy(self):
        raise NotImplementedError()

    def measure_ssro(self):
        raise NotImplementedError()

    def find_resonator_frequency_vna(self, update=True, start_freq=None, 
                                 stop_freq=None, if_bandwidth =None,
                                 npts=None, averages = None,MC=None,
                                 close_fig=True):
        """
        Finds the resonator frequency by performing a VNA experiment
        if freqs == None it will determine a default range dependent on the
        last known frequency of the resonator.
        """
        if start_freq is None:
            if self.f_RO_resonator() != 0 and self.Q_RO_resonator() != 0:
                start_freq = self.f_RO_resonator()*(1-10/self.Q_RO_resonator())
                stop_freq = self.f_RO_resonator()*(1+10/self.Q_RO_resonator())
                #freqs = np.linspace(fmin, fmax, 100)
            else:
                raise ValueError("Unspecified frequencies for find_resonator_"
                                 "frequency and no previous value exists")
        
        
        if if_bandwidth and self.vna_instr.bandwidth() is None:
            raise ValueError("Unspecified if_bandwidth for measure_vna_"
                             "spectroscopy")
            
        self.vna_instr.bandwidth(if_bandwidth)
    
        
        if npts and self.vna_instr.npts() is None:
            raise ValueError("Unspecified npts for measure_vna_spectroscopy")
        
        if averages and self.vna_instr.avg() is None:
            raise ValueError("Unspecified averages for measure_vna_"
                             "spectroscopy")

        if MC is None:
            MC = self.MC

        self.measure_resonator_spectroscopy_vna(start=start_freq, 
                                                stop = stop_freq, 
                                               if_bandwidth = if_bandwidth,
                                               npts=npts,
                                               averages = averages, MC=MC,
                                               analyze=False,close_fig=False)

        HA = ma.VNA_Peak_Analysis('resonator_vna_scan'+self.msmt_suffix, close_fig=close_fig,
                                  fitting_model='lorentzian')
        
        f0 = HA.fit_results.params['f0'].value
        df0 = HA.fit_results.params['f0'].stderr
        Q = HA.fit_results.params['Q'].value
        dQ = HA.fit_results.params['Q'].stderr
        if f0 > stop_freq or f0 < start_freq:
            logging.warning('exracted frequency outside of range of scan')
        elif df0 > f0:
            logging.warning('resonator frequency uncertainty greater than '
                            'value')
        elif dQ > Q:
            logging.warning('resonator Q factor uncertainty greater than '
                            'value')
        elif update:  # don't update if there was trouble
            self.f_RO_resonator(f0)
            self.Q_RO_resonator(Q)
            self.heterodyne_instr.frequency(f0)
        return f0

    def find_homodyne_acqusition_delay(self, delays=None, update=True, MC=None,
                                         close_fig=True):
        """
        Finds the acquisition delay for a homodyne experiment that corresponds
        to maximal signal strength.
        """
        if delays is None:
            delays = np.linspace(0,1e-6,100)

        if MC is None:
            MC = self.MC

        self.measure_homodyne_acqusition_delay(delays, MC, analyze=False)

        DA = ma.Acquisition_Delay_Analysis(label=self.msmt_suffix,
                                           close_fig=close_fig)
        d = DA.max_delay

        if update:
            self.optimal_acquisition_delay(d)
            self.heterodyne_instr.acquisition_delay(d)
        return d

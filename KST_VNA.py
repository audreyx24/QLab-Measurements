from qcodes import VisaInstrument
from qcodes.utils import validators as vals
from cmath import phase
import numpy as np
from qcodes import MultiParameter, Parameter
from qcodes.utils.delaykeyboardinterrupt import DelayedKeyboardInterrupt


class KST_VNA(VisaInstrument):

    """
    qcodes driver for the Rohde & Schwarz ZNB20

    Author: Stefano Poletto (QuTech)
    """

    def __init__(self, name, address, **kwargs):

        super().__init__(name=name, address=address, timeout = 20, **kwargs)

        self.add_parameter(name='power',
                           label='Power',
                           unit='dBm',
                           get_cmd='SOUR:POW?',
                           set_cmd='SOUR:POW {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(-150, 25))

        #self.add_function('tooltip_on', call_cmd='SYST:ERR:DISP ON')
        #self.add_function('tooltip_off', call_cmd='SYST:ERR:DISP OFF')
        self.add_function('cont_meas_on', call_cmd='INIT:CONT ON')
        self.add_function('cont_meas_off', call_cmd='INIT:CONT OFF')
        self.add_function('update_display_once', call_cmd='DISP:UPD:IMM')
        self.add_function('update_display_on', call_cmd='DISP:VIS ON')
        self.add_function('update_display_off', call_cmd='DISP:VIS OFF')
        self.add_function('rf_off', call_cmd='OUTP:STAT OFF')
        self.add_function('rf_on', call_cmd='OUTP:STAT ON')

        ###################
        # Common commands #
        ###################
        # common commands for all devices as described in IEEE 488.2
        self.add_function('reset', call_cmd='*RST')
        self.add_function('wait_to_continue', call_cmd='*WAI')

        ######################
        # CALCULATE commands #
        ######################
        # commands for post-acquisition data processing
        self.add_parameter('format',
                           set_cmd='CALC:FORMAT {:s}',
                           vals=vals.Enum('MLIN', 'MLOG', 'PHAS', 'UPH', 'IMAG',
                                          'REAL', 'POL', 'SMIT', 'SADM', 'SWR',
                                          'GDEL','KELV','FAHR','CELS','PPH'))

        ####################
        # DISPLAY commands #
        ####################
        # Commands to select and present data on screen
        self.add_function('autoscale_trace', call_cmd='DISP:WIND:TRAC:Y:AUTO')

        #####################
        # INITIATE commands #
        #####################
        # commands to control the initialization of the trigger system and define
        # the scope ot the triggered measurement
        self.add_parameter(name='continuous_mode_all',
                           docstring='My explanation',
                           set_cmd='INIT:CONT {:s}',
                           vals=vals.OnOff())

        self.add_function('start_sweep_all', call_cmd='INIT:IMM')

        ##################
        # SENSE commands #
        ##################
        # commands affecting the receiver settings
        self.add_function('clear_avg', call_cmd='SENS:AVER:CLE')

        self.add_parameter(name='avg',
                           label='Averages',
                           unit='',
                           get_cmd='SENS:AVER:COUN?',
                           set_cmd='SENS:AVER:COUN {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(1, 1000))

        self.add_parameter(name='average_mode',
                           get_cmd='SENS:AVER:MODE?',
                           set_cmd='SENS:AVER:MODE {:s}',
                           vals=vals.Enum('POIN', 'SWEEP'))

        self.add_parameter(name='average_state',
                           get_cmd='SENS:AVER:STAT?',
                           set_cmd='SENS:AVER:STAT {:s}',
                           vals=vals.OnOff())

        self.add_parameter(name='bandwidth',
                           label='Bandwidth',
                           unit='Hz',
                           get_cmd='SENS:BAND?',
                           set_cmd='SENS:BAND {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(1, 1e6))

        self.add_parameter(name='center_frequency',
                           unit='Hz',
                           get_cmd='SENS:FREQ:CENT?',
                           set_cmd='SENS:FREQ:CENT {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(100e3, 20e9))

        self.add_parameter(name='span_frequency',
                           unit='Hz',
                           get_cmd='SENS:FREQ:SPAN?',
                           set_cmd='SENS:FREQ:SPAN {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(0, 20e9))

        self.add_parameter(name='start_frequency',
                           unit='Hz',
                           get_cmd='SENS:FREQ:STAR?',
                           set_cmd='SENS:FREQ:STAR {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(100e3, 20e9))

        self.add_parameter(name='stop_frequency',
                           unit='Hz',
                           get_cmd='SENS:FREQ:STOP?',
                           set_cmd='SENS:FREQ:STOP {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(100e3, 20e9))

        self.add_function('delete_all_segments', call_cmd='SENS:SEGM:DEL:ALL')
        
        self.add_parameter('delay_t',
                          label='Electrical Delay',
                          get_cmd='CALC:CORR:EDEL:TIME?',
                          get_parser=VISA_str_to_float,
                          set_cmd='CALC:CORR:EDEL:TIME {:.6e}',
                          unit='s',
                          vals=vals.Numbers(min_value=0, max_value=10))

        #self.add_parameter(name='number_sweeps_all',
        #                   set_cmd='SENS:SWE:COUN:ALL {:.4f}',
        #                   vals=vals.Ints(1, 100000))

        self.add_parameter(name='npts',
                           get_cmd='SENS:SWE:POIN?',
                           set_cmd='SENS:SWE:POIN {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Ints(1, 100001))

        self.add_parameter(name='min_sweep_time',
                           get_cmd='SENS:SWE:TIME:AUTO?',
                           set_cmd='SENS:SWE:TIME:AUTO {:s}',
                           get_parser=VISA_str_to_int,
                           vals=vals.OnOff())

        self.add_parameter(name='sweep_time',
                           get_cmd='SENS:SWE:TIME?',
                           set_cmd='SENS:SWE:TIME {:.4f}',
                           get_parser=VISA_str_to_float,
                           vals=vals.Numbers(0, 1e5))

        self.add_parameter(name='sweep_type',
                           get_cmd='SENS:SWE:TYPE?',
                           set_cmd='SENS:SWE:TYPE {:s}',
                           get_parser=str,
                           vals=vals.Enum('LIN', 'LOG', 'POW', 'CW',
                                          'SEGM'))

        self.add_parameter(name='sweep_dwell_time', # dwell time per frequency point
                           get_cmd='SENS:SWE:DWEL?',
                           set_cmd='SENS:SWE:DWEL {:.4f}',
                           get_parser=VISA_str_to_float,
                           vals=vals.Numbers(0, 1)) #dwell time in second
        
        self.add_parameter(name='init_sweep_dwell_time',
                           get_cmd='SENS:SWE:DWEL:SDEL?',
                           set_cmd='SENS:SWE:DWEL:SDEL {:.4f}',
                           get_parser=VISA_str_to_float,
                           vals=vals.Numbers(0, 1)) #dwell time in second
        
        #####################
        #  SEGMENT commands #
        #####################
        
        # self.add_parameter(name='segment_power_control',
        #                    get_cmd='SENS:SEGM:POW:CONT?',
        #                    set_cmd='SENS:SEGM:POW:CONT {:s}',
        #                    get_parser=VISA_str_to_int,
        #                    vals=vals.OnOff())
        
        self.add_function('segment_power_control', call_cmd='SENS:SEGM:POW:CONT ON')
        
        self.add_function('add_first_segment', call_cmd='SENS:SEGM1:ADD')
        self.add_function('first_segment_turn_on', call_cmd='SENS:SEGM1 ON')

        self.add_function('add_second_segment', call_cmd='SENS:SEGM2:ADD')
        self.add_function('second_segment_turn_on', call_cmd='SENS:SEGM2 ON')

        self.add_parameter(name='npts_first_segment',
                           get_cmd='SENS:SEGM1:SWE:POIN?',
                           set_cmd='SENS:SEGM1:SWE:POIN {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Ints(1, 100001))

        self.add_parameter(name='npts_second_segment',
                          get_cmd='SENS:SEGM2:SWE:POIN?',
                          set_cmd='SENS:SEGM2:SWE:POIN {:.4f}',
                          get_parser=VISA_str_to_int,
                          vals=vals.Ints(1, 100001))

        self.add_parameter(name='power_first_segment',
                           label='Power S1',
                           unit='dBm',
                           get_cmd='SENS:SEGM1:POW?',
                           set_cmd='SENS:SEGM1:POW {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(-150, 25))

        self.add_parameter(name='power_second_segment',
                          label='Power S2',
                          unit='dBm',
                          get_cmd='SENS:SEGM2:POW?',
                          set_cmd='SENS:SEGM2:POW {:.4f}',
                          get_parser=VISA_str_to_int,
                          vals=vals.Numbers(-150, 25))

        self.add_parameter(name='bandwidth_first_segment',
                           label='Bandwidth S1',
                           unit='Hz',
                           get_cmd='SENS:SEGM1:BAND?',
                           set_cmd='SENS:SEGM1:BAND {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(1, 1e6))

        self.add_parameter(name='bandwidth_second_segment',
                          label='Bandwidth S2',
                          unit='Hz',
                          get_cmd='SENS:SEGM2:BAND?',
                          set_cmd='SENS:SEGM2:BAND {:.4f}',
                          get_parser=VISA_str_to_int,
                          vals=vals.Numbers(1, 1e6))

        self.add_parameter(name='start_freq_first_segment',
                           unit='Hz',
                           get_cmd='SENS:SEGM1:FREQ:STAR?',
                           set_cmd='SENS:SEGM1:FREQ:STAR {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(100e3, 20e9))

        self.add_parameter(name='stop_freq_first_segment',
                           unit='Hz',
                           get_cmd='SENS:SEGM1:FREQ:STOP?',
                           set_cmd='SENS:SEGM1:FREQ:STOP {:.4f}',
                           get_parser=VISA_str_to_int,
                           vals=vals.Numbers(100e3, 20e9))

        self.add_parameter(name='start_freq_second_segment',
                          unit='Hz',
                          get_cmd='SENS:SEGM2:FREQ:STAR?',
                          set_cmd='SENS:SEGM2:FREQ:STAR {:.4f}',
                          get_parser=VISA_str_to_int,
                          vals=vals.Numbers(100e3, 20e9))

        self.add_parameter(name='stop_freq_second_segment',
                          unit='Hz',
                          get_cmd='SENS:SEGM2:FREQ:STOP?',
                          set_cmd='SENS:SEGM2:FREQ:STOP {:.4f}',
                          get_parser=VISA_str_to_int,
                          vals=vals.Numbers(100e3, 20e9))

        
        #####################
        #  TRIGGER commands #
        #####################
        # commands to syncronize analyzer's actions
        self.add_parameter(name='trigger_source',
                           set_cmd='TRIG:SEQ:SOUR {:s}',
                           vals=vals.Enum('IMM', 'EXT', 'MAN'))
        
        ### Aux trigger 1 parameters
        self.add_parameter(name ='trigger_output',
                           get_cmd ='TRIG:CHAN:AUX:ENAB?',
                           set_cmd ='TRIG:CHAN:AUX:ENAB {:s}',
                           vals=vals.OnOff())
        
        self.add_parameter(name ='trigger_output_duration',
                           get_cmd ='TRIG:CHAN:AUX:DUR?',
                           set_cmd ='TRIG:CHAN:AUX:DUR {:.4f}',
                           get_parser=VISA_str_to_float,
                           vals=vals.Numbers(1e-6, 1))
        
        self.add_parameter(name ='trigger_output_delay',
                           get_cmd ='TRIG:CHAN:AUX:OUTP:DEL?',
                           set_cmd ='TRIG:CHAN:AUX:OUTP:DEL {:.4f}',
                           get_parser=VISA_str_to_float,
                           vals=vals.Numbers(1e-6, 1))
        
        self.add_parameter(name ='trigger_output_mode',
                           get_cmd ='TRIG:CHAN:AUX:INT?',
                           set_cmd ='TRIG:CHAN:AUX:INT {:s}',
                           get_parser=str,
                           vals=vals.Enum('POIN','SWE'))
        
        self.add_parameter(name ='trigger_output_pos',
                           get_cmd ='TRIG:CHAN:AUX:POS?',
                           set_cmd ='TRIG:CHAN:AUX:POS {:s}',
                           get_parser=str,
                           vals=vals.Enum('BEF','AFT')) #before or after the data is acquired.
        
        self.add_parameter(name ='trigger_output_sign',
                           get_cmd ='TRIG:CHAN:AUX:OPOL?',
                           set_cmd ='TRIG:CHAN:AUX:OPOL {:s}',
                           get_parser=str,
                           vals=vals.Enum('POS','NEG')) 
        
        ### Aux trigger 2 parameters
        self.add_parameter(name ='trigger2_output',
                           get_cmd ='TRIG:CHAN:AUX2:ENAB?',
                           set_cmd ='TRIG:CHAN:AUX2:ENAB {:s}',
                           vals=vals.OnOff())
        
        self.add_parameter(name ='trigger2_output_duration',
                           get_cmd ='TRIG:CHAN:AUX2:DUR?',
                           set_cmd ='TRIG:CHAN:AUX2:DUR {:.4f}',
                           get_parser=VISA_str_to_float,
                           vals=vals.Numbers(1e-6, 1))
        
        self.add_parameter(name ='trigger2_output_mode',
                           get_cmd ='TRIG:CHAN:AUX2:INT?',
                           set_cmd ='TRIG:CHAN:AUX2:INT {:s}',
                           get_parser=str,
                           vals=vals.Enum('POIN','SWE'))
        
        self.add_parameter(name ='trigger2_output_pos',
                           get_cmd ='TRIG:CHAN:AUX2:POS?',
                           set_cmd ='TRIG:CHAN:AUX2:POS {:s}',
                           get_parser=str,
                           vals=vals.Enum('BEF','AFT')) #before or after the data is acquired.
        
        self.add_parameter(name ='trigger2_output_sign',
                           get_cmd ='TRIG:CHAN:AUX2:OPOL?',
                           set_cmd ='TRIG:CHAN:AUX2:OPOL {:s}',
                           get_parser=str,
                           vals=vals.Enum('POS','NEG')) 
        
     
        
        

        #self.reset()
        self.connect_message()

    def get_stimulus(self):
        '''
        get the frequencies used in the sweep
        '''
    #    stimulus_str = self.ask('CALC:DATA:STIM?')
        if self.start_frequency != None and self.stop_frequency != None:
            start = self.start_frequency()
            stop = self.stop_frequency()
            npts = self.npts()
           # print(start,stop,npts)
            stimulus_double = np.linspace(start,stop,
                                       npts,
                                       dtype = np.double)
           
        elif self.center_frequency != None and self.span_frequency != None:
            center = self.center_frequency()
            span = self.span_frequency()
            npts = self.npts()
            stimulus_double = np.linspace(center-span/2,
                                       center+span/2,
                                       npts,
                                       dtype = np.double)

        return stimulus_double
    
    def get_stimulus_segment(self, segment_list):
        '''
        get the frequencies used in the sweep
        '''

        return np.concatenate((np.linspace(segment_list[0], segment_list[1], segment_list[2]), \
                               np.linspace(segment_list[5], segment_list[6], segment_list[7])))

    def get_real_imaginary_data(self):
        
        self.write("CALC1:FORM REAL")
        data_str = self.ask('CALC1:DATA? FDATA')
       # print(data_str)
        real_data = np.array(data_str.split(','), dtype=np.double)
       # print("real_data", real_data)
        self.write("CALC1:FORM IMAG")
        data_str = self.ask('CALC1:DATA? FDATA')
       # print(data_str)
        imag_data = np.array(data_str.split(','), dtype=np.double)

        return real_data, imag_data

    def get_formatted_data(selft, format):
        print('in progress')
        
    def write_raw(self, cmd: str) -> None:
        """
        Low-level interface to ``visa_handle.write``.

        Args:
            cmd: The command to send to the instrument.
        """
        with DelayedKeyboardInterrupt():
            self.visa_log.debug(f"Writing: {cmd}")
            #print( self.visa_handle.write(cmd))
            ret_code = self.visa_handle.write(cmd)
            #self.check_error(ret_code)


def VISA_str_to_int(message):
    return int(float(message.strip('\\n')))


def VISA_str_to_float(message):
    return float(message.strip('\\n'))

# Ensuring backwards compatibility
print('This is the version by Stefano, there is another version in QCoDeS')
# from .ZNB import ZNB as ZNB20


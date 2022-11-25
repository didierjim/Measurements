import os
import sys
import time
import importlib
import matplotlib.animation as animation
from pymeasure import instruments
from GUIBaseClass_TCC import GUIBase
from GUIBaseClass_TCC import animate_plot
from keithley2400 import Keithley2400
import time

sys.path.append(os.getcwd())  # add path to import dictionary
defaults = importlib.import_module('FieldControls_NewSG_Kepco',
                                   os.getcwd())  # import dictionary based on the name of the computer
mag_settings = getattr(defaults, os.environ.get('USERNAME'))
res_settings = getattr(defaults, os.environ.get('USERNAME') + '_RESOURCES')


def fix_param1(index, output, delay, resources, kwargs):
    if index == 0:  # initialize machines first time around
        keith_2400 = Keithley2400('f')
        keith_2400.setCurrent(0.1)
        keith_2400.outputOn()
        resources['keithley_2400'].measure_voltage(voltage=200)
        resources['keithley_2400'].apply_current(
            compliance_voltage=200)
        resources['keithley_2400'].auto_range_source()
        resources['sig_gen_8257'].amplitude_source = 'internal'
        resources['sig_gen_8257'].low_freq_out_source = 'internal'
        resources['sig_gen_8257'].low_freq_out_amplitude = float(
            kwargs['signal voltage'])
        resources['sig_gen_8257'].enable_low_freq_out()
        resources['sig_gen_8257'].enable_modulation()
        resources['sig_gen_8257'].config_amplitude_modulation(
            frequency=float(kwargs['modulation frequency']),
            depth=99.0,
            shape='sine'
        )
        resources['dsp_lockin'].reference = 'external front'
        resources['dsp_lockin'].sensitivity = kwargs['Sensitivity']
        resources['dsp_lockin'].frequency = float(
            kwargs['modulation frequency'])
        resources['dsp_lockin'].time_constant = 0.2
    resources['keithley_2400'].source_current = output * 1e-3  # set to mA


def fix_param2(output, delay, resources, kwargs):
    resources['sig_gen_8257'].frequency = output * 10**9
    resources['sig_gen_8257'].enable()


def measure_y(output, delay, resources, fix1_output, fix2_output, kwargs):
    resources['sig_gen_8257'].power = 21
    resources['sig_gen_8257'].enable()
    setattr(resources['dsp_lockin'], kwargs['Hx Dac'],
            output / float(kwargs['Hx Conversion']))
    time.sleep(delay)
    # x2 = resources['gaussmeter'].measure()
    x2 = 0.0
    y = 0.0
    for i in range(int(kwargs['averages'])):
        y += resources['dsp_lockin'].x
    y = (y / int(kwargs['averages'])) * (10**6)

    return output, y, x2


def main():
    resource_dict = {
        'dsp_lockin': res_settings['dsp_lockin'],
        'sig_gen_8257': res_settings['sig_gen_8257'],
        'keithley_2000': res_settings['keithley_2000'],
        'keithley_2400': res_settings['keithley_2400'],
        #'gaussmeter': res_settings['gaussmeter'],
    }

    graph_dict = {
        "gui_title": 'DC-modulation',
        "graph_title": "Graph Title",
        "x_title": "Applied Field",
        "y_title": "Lockin Voltage (uV)",
        "x2_title": "",
        "fixed_param_1": "I (mA)",
        "fixed_param_2": "Freq (Ghz)"
    }

    loop_commands = {
        'fixed_func_1': 'fix_param1',  # name of fixed parameter one function
        'fixed_func_2': 'fix_param2',
        'measure_y_func': 'measure_y',
        # directory from which the preceeding modules will be imported from
        'module_path': os.getcwd(),
        # name of the file to get the functions from
        'module_name': 'ST_FMR_NewSG_DC_modulation_TCC',
        'fix1_start': 'current start',
        'fix1_stop': 'current stop',
        'fix1_step': 'current step',
        'fix2_start': 'frequency start',
        'fix2_stop': 'frequency stop',
        'fix2_step': 'frequency step',
        'x_start': 'hx start',
        'x_stop': 'hx stop',
        'x_step': 'hx step',
        'MOKE': False
    }

    controls_dict1 = {
        "title": "Magnet Controls",
        "hx start": 3000,
        "hx stop": -3000,
        "hx step": -30,
    }

    controls_dict2 = {
        "title": "Current Controls",
        "current start": 0,
        "current stop": 1.5,
        "current step": 1.5,
        'averages': 1,
        "total repeat": 1
    }

    controls_dict3 = {
        "title": "Signal Generator Controls",
        #"power start": 25,
        #"power stop": 25,
        #"power step": 0,
        "frequency start": 9,
        "frequency stop": 9,
        "frequency step": 0,
        "modulation frequency": 2000,
        "signal voltage": 0.7
    }

    lockin_controls = {
        "title": "Lockin",
        "Sensitivity": '1mV',
        "averages": 10,
        'Hx Dac': mag_settings['Hx Dac'],
        'Hx Conversion': mag_settings['Hx Conversion'],
        'Hx Max': mag_settings['Hx Max'],

    }

    measurement_gui = GUIBase(graph_dict, resource_dict, loop_commands,
                              controls_dict1, controls_dict2, controls_dict3, lockin_controls)
    ani = animation.FuncAnimation(
        measurement_gui.fig, animate_plot, interval=200, fargs=[measurement_gui.ax, measurement_gui.graph, measurement_gui.results, measurement_gui.progress_bar, measurement_gui.time_var])
    measurement_gui.mainloop()


if __name__ == '__main__':
    main()

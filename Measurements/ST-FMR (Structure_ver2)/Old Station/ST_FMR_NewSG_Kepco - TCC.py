import os
import sys
import time
import importlib
import matplotlib.animation as animation
from pymeasure import instruments
from GUIBaseClass_TCC import GUIBase
from GUIBaseClass_TCC import animate_plot
import time

sys.path.append(os.getcwd())  # add path to import dictionary
defaults = importlib.import_module('FieldControls_NewSG_Kepco',
                                   os.getcwd())  # import dictionary based on the name of the computer
print(os.environ.get('USERNAME'))
mag_settings = getattr(defaults, os.environ.get('USERNAME'))
res_settings = getattr(defaults, os.environ.get('USERNAME') + '_RESOURCES')


def fix_param1(index, output, delay, resources, kwargs):
    if index == 0:  # initialize machines first time around
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
    resources['sig_gen_8257'].power = output


def fix_param2(output, delay, resources, kwargs):
    resources['sig_gen_8257'].frequency = output * 10**9
    resources['sig_gen_8257'].enable()


def measure_y(output, delay, resources, fix1_output, fix2_output, kwargs):
    setattr(resources['dsp_lockin'], kwargs['Hx Dac'],
            output / float(kwargs['Hx Conversion']))
    time.sleep(delay)
    time.sleep(0.05)
    # time.sleep(0.6)


    x2 = 0.0
    #x2 = resources['gaussmeter'].measure()
    y = 0.0
    for i in range(int(kwargs['averages'])):
        #x2 += resources['dsp_lockin'].y

        y += resources['dsp_lockin'].x
    y = (y / int(kwargs['averages'])) * (10**6)
    #x2 = (x2 / int(kwargs['averages'])) * (10**6)

    return output, y, x2


def main():
    resource_dict = {
        'dsp_lockin': res_settings['dsp_lockin'],
        'sig_gen_8257': res_settings['sig_gen_8257'],
        #'gaussmeter': res_settings['gaussmeter'],
        # need to be lighten up if field measurement is applied
    }

    graph_dict = {
        "gui_title": 'ST-FMR',
        "graph_title": "Graph Title",
        "x_title": "Applied Field",
        "y_title": "Lockin Voltage (uV)",
        "x2_title": "Lockin Y (uV)",
        # need to add "Gaussmeter" if the instant field measurement is applied
        "fixed_param_1": "P (dBm)",
        "fixed_param_2": "Freq (Ghz)"
    }

    loop_commands = {
        'fixed_func_1': 'fix_param1',  # name of fixed parameter one function
        'fixed_func_2': 'fix_param2',
        'measure_y_func': 'measure_y',
        # directory from which the preceeding modules will be imported from
        'module_path': os.getcwd(),
        # name of the file to get the functions from
        'module_name': 'ST_FMR_NewSG_Kepco - TCC',
        'fix1_start': 'power start',
        'fix1_stop': 'power stop',
        'fix1_step': 'power step',
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
        "hx start": 4000,
        "hx stop": -4000,
        "hx step": -30,
    }

    controls_dict2 = {
        "title": "Signal Generator Controls",
        "power start": 20,
        "power stop": 20,
        "power step": 0,
        "frequency start": 8,
        "frequency stop": 8,
        "frequency step": 0,
        "modulation frequency": 3388,
        "signal voltage": 2,
        "total repeat": 1
    }

    lockin_controls = {
        "title": "Lockin",
        "Sensitivity": '50uV',
        "averages": 10,
        'Hx Dac': mag_settings['Hx Dac'],
        'Hx Conversion': mag_settings['Hx Conversion'],
        'Hx Max': mag_settings['Hx Max'],

    }

    measurement_gui = GUIBase(graph_dict, resource_dict, loop_commands,
                              controls_dict1, controls_dict2, lockin_controls)
    ani = animation.FuncAnimation(
        measurement_gui.fig, animate_plot, interval=200, fargs=[measurement_gui.ax, measurement_gui.graph, measurement_gui.results, measurement_gui.progress_bar, measurement_gui.time_var])
    measurement_gui.mainloop()


if __name__ == '__main__':
    main()

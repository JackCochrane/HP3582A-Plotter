# -*- coding: utf-8 -*-
"""
Created on Thu Aug  7 15:44:19 2025

Generates a virtual control panal for old HP Spectrum Analyzers pre 1990 using tkinter to
make the GUI, pyvisa to communicate with the SA, matplotlib to generate plots, and numpy to 
create and export data arrays

@author: Jack Cochrane
"""

import tkinter as tk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import pyvisa 
import numpy as np
import time
from pathlib import Path
from datetime import datetime, timezone


#Called by the im checkboxes to ensure that only two cam be selected at any given time
def toggle_im_enable ():
    im_vars_sum=0
    for x in input_mode_vars:
        im_vars_sum += x.get()
    if im_vars_sum >= 2:
        for x in im_cb:
            if input_mode_vars[im_cb.index(x)].get() == 0:
                x['state'] = tk.DISABLED
            else:
                x['state'] = tk.NORMAL
    else:
        for x in im_cb:
            x['state'] = tk.NORMAL

#Allows for one line configuration of tkinter row/column weight
def row_col_config (to_grid, rows, columns):
    rows = enumerate(rows)
    columns = enumerate(columns)
    for x, y in rows:
        to_grid.rowconfigure(x, weight=y)
    for x, y in columns:
        to_grid.columnconfigure(x, weight=y)
        
#Called by buttons/menus to write commands to the spectrum analyzer
def write_data (command):
    SA.write(command)
    time.sleep(0.1)

#refreshes alphanumerics, called by refresh_all_display_widgets
def refresh_alphanumerics ():
    alphanumerics_var.set(SA.query('LAN'))

#refreshes both overloads, called by refresh_all_display widgets
def refresh_overload ():
    SA.write('LST0')
    SA.write('LST1')
    status_word = SA.read_bytes(1)
    if (int.from_bytes(status_word)&4)==4:
        A_overload_var.set('Overload')
    else:
        A_overload_var.set('Normal')
    if (int.from_bytes(status_word)&8)==8:
        B_overload_var.set('Overload')
    else:
        B_overload_var.set('Normal')
    transfer_sens_var.set(SA.query('LXS') + 'dBV')

#Makes the Input Mode list
def make_im_list ():
    im_list =['A Amplitude', 'A Phase', 'B Amplitude', 'B Phase', 'Transfer Amplitude', 'Transfer Phase', 'Coherance']
    if y_scale_var.get() == 1:
        amp_type = 'Amplitude (V)'
    else:
        amp_type = 'Amplitude (dB)'
    im_data_types = [amp_type, 'Phase (Deg)', amp_type, 'Phase (Deg)', amp_type, 'Phase (Deg)', 'Coherance (UL)']
    im_list = list(zip(im_list, input_mode_vars, im_data_types))
    return im_list

#refreshes/generates the figure/plots and toolbar
def refresh_figure_toolbar ():
    #Make and set two vars flag, get vars, make im list
    global two_vars
    two_vars=False
    im_list = make_im_list() #element tuple (name, on/off, datatype)
    global figure_vars
    figure_vars = []
    for x in im_list:
        if x[1].get() == 1:
            figure_vars.append(x)   
    if len(figure_vars) >= 2:
        two_vars=True
    
    #Get value array, split as needed, add to list, zip into figure_vars, need to confirm that ordering is correct
    if two_vars:
         values = np.split(SA.query_ascii_values('LDS', container=np.array), 2)
    else:
        values = [SA.query_ascii_values('LDS', container=np.array)]
    figure_vars = list(zip(figure_vars, values))  #element tuple ((name, on/off, datatype,) data array)
    
    #generate the frequency array
    freq_span_val = ''
    for x in span_var.get():
        if x.isdigit():
            freq_span_val += x
        elif x == 'k':
            freq_span_val += '000'
    freq_span_val = int(freq_span_val)
    
    global freq_vals
    if frequency_mode_var.get() == 1:
        freq_vals = np.linspace(0, 25000, num = values[0].size)
    elif frequency_mode_var.get() == 2:
        freq_vals = np.linspace(0, freq_span_val, num = values[0].size)
    elif frequency_mode_var.get() == 3:
        freq_vals = np.linspace (adjust_var.get() - 0.5 * freq_span_val, adjust_var.get() + 0.5 * freq_span_val, num = values[0].size)
    elif frequency_mode_var.get() == 4:
        freq_vals = np.linspace (adjust_var.get(), freq_span_val + adjust_var.get(), num = values[0].size)
    
    #Clear the figure generate axs to put data in, create axes
    fig.clf()
    
    if data_points_var.get():
        line_type = '-2'
    else:
        line_type = '-'
    
    figure_vars = list(enumerate(figure_vars)) #element tuple (index, ((name, on/off, datatype,) data array))
    if two_vars:
        axs = fig.subplots(2, sharex=True)
        for i, x in figure_vars:
            axs[i].set_title(x[0][0])
            if x_scale_var.get()==1:
                axs[i].semilogx(freq_vals, x[1], line_type)
                axs[i].set_xlabel('Frequency (Hz)')
                axs[i].set_ylabel(x[0][2])
            else:
                axs[i].plot(freq_vals, x[1], line_type)
                axs[i].set_xlabel('Frequency (Hz)')
                axs[i].set_ylabel(x[0][2])
            axs[i].grid()
            
    else:
        ax=fig.subplots()
        for i, x in figure_vars:
            ax.set_title(x[0][0])
            if x_scale_var.get()==1:
                ax.semilogx(freq_vals, x[1], line_type)
            else:
                ax.plot(freq_vals, x[1], line_type)
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel(x[0][2])
            ax.grid()
    
    passband_list = ['error', 'Flattop', 'Hanning', 'Uniform']
    fig.suptitle(t=('Passband Shape: '+ passband_list[passband_var.get()]), size='medium', ha='left', va='bottom', x=0.02, y=0.02)
    
    data_display.draw() #Draws the updated plots on the tkinter canvas object
        
#Generates plot, alphanumerics, and overload on startup and on pressing refresh
def refresh_all_display_widgets ():
    refresh_alphanumerics()
    refresh_overload()
    refresh_figure_toolbar()

#Automatially sets the sensitivity to a value that it doesnt immediately overload
def set_sensitivity ():
    #Turn off average
    avg_type_var.set(1)
    SA.write('AV1')
    
    #Initialize and define needed variables
    A_done = False
    B_done = False
    AS = 2
    BS = 2

    #function loop
    while not (A_done and B_done):
        if not A_done:
            AS += 1
        if not B_done:
            BS += 1
        if AS>10 or BS>10:
            raise ValueError("Sensitivity went out of bounds") #Prevents sending the SA an invalid command
        SA.write('AS' + str(AS) + 'BS' + str(BS) + 'LST0')
        time.sleep(0.1)
        SA.write('LST1')
        status_word = int.from_bytes(SA.read_bytes(1)) #Gets status word
        if (status_word & 4) == 4: #Decreases A sens if A overload flag is raised
            AS -= 1
            A_done = True
        if (status_word & 8) == 8: #Decreases B sens if B overload flag is raised
            BS -= 1
            B_done = True
    
    A_sens_var.set(sens_list[AS-1])
    B_sens_var.set(sens_list[BS-1])
    transfer_sens_var.set(SA.query('LXS') + 'dBV')
    refresh_overload()
     
#Resets display vars to match prs
def preset_values ():
    trace_1.set(0)
    trace_2.set(0)
    passband_var.set(1)
    A_sens_var.set(sens_list[1])
    B_sens_var.set(sens_list[1])
    transfer_sens_var.set(SA.query('LXS') + 'dBV')
    #A_amplitude, A_phase, B_amplitude, B_phase, transfer_amplitude, transfer_phase, coherance
    input_mode_vars[0].set(1)
    input_mode_vars[1].set(0)
    input_mode_vars[2].set(0)
    input_mode_vars[3].set(0)
    input_mode_vars[4].set(0)
    input_mode_vars[5].set(0)
    input_mode_vars[6].set(0)
    x_scale_var.set(0)
    y_scale_var.set(2)
    frequency_mode_var.set(1)
    span_var.set(span_list[13])
    adjust_var.set(0)
    A_coupling_var.set(1)
    B_coupling_var.set(1)
    avg_type_var.set(1)
    sample_num_var.set(1)
    shift_var.set(0)
    free_run_var.set(1)
    repetative_var.set(1)
    alphanumerics_var.set(SA.query('LAN'))
    ref_level_var.set(0)
    toggle_im_enable ()
    trace_1.configure(relief=tk.RAISED)
    trace_2.configure(relief=tk.RAISED)
    free_run.configure(relief=tk.SUNKEN)
    repetative.configure(relief=tk.SUNKEN)
    number_shift.configure(relief=tk.RAISED)
    
#Toggles the display of data points, also used to refresh the display without changing data
def toggle_data_points ():
    #Clear the figure generate axs to put data in, create axes
    fig.clf()
    
    if data_points_var.get():
        line_type = '-2'
    else:
        line_type = '-'
    
    if two_vars:
        axs = fig.subplots(2, sharex=True)
        for i, x in figure_vars:
            axs[i].set_title(x[0][0])
            if x_scale_var.get()==1:
                axs[i].semilogx(freq_vals, x[1], line_type)
            else:
                axs[i].plot(freq_vals, x[1], line_type)
            axs[i].set_xlabel('Frequency (Hz)')
            axs[i].set_ylabel(x[0][2])
            axs[i].grid()
            
    else:
        ax=fig.subplots()
        for i, x in figure_vars:
            ax.set_title(x[0][0])
            if x_scale_var.get()==1:
                ax.semilogx(freq_vals, x[1], line_type)
            else:
                ax.plot(freq_vals, x[1], line_type)
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel(x[0][2])
            ax.grid()
    
    passband_list = ['error', 'Flattop', 'Hanning', 'Uniform']
    fig.suptitle(t=('Passband Shape: '+ passband_list[passband_var.get()]), size='medium', ha='left', va='bottom', x=0.02, y=0.02)
    data_display.draw() #Draws the updated plots on the tkinter canvas object
    
#Sets the amplitude reference level
def set_ref_level ():
    ref_level_val = ref_level_var.get()
    ref_level_val = (ref_level_val / -10) + 1
    SA.write('AM' + str(ref_level_val))

#Exports/saves data
def export_data ():
    #figure_vars element tuple (index, ((name, on/off, datatype,) data array))
    if file_name_var.get() == '' or file_name_var.get().isspace():
        export_name = 'SA_data/data_set_' + datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d_T%H-%M-%S") + '.csv'
    else:
        export_name = 'SA_data/' + file_name_var.get() + '.csv'

    if two_vars:
        export_array = np.rot90(np.array([figure_vars[0][1][1], figure_vars[1][1][1], freq_vals]))
        export_header = figure_vars[0][1][0][0][0] + ' ' + figure_vars[0][1][0][2] + ',' + figure_vars[1][1][0][0][0] + ' ' + figure_vars[1][1][0][2] + ',' + ' Frequency (Hz)'
    else:
        export_array = np.rot90(np.array([figure_vars[0][1][1], freq_vals]))
        export_header = figure_vars[0][1][0][0][0] + ' ' + figure_vars[0][1][0][2] + ',' + 'Frequency (Hz)'
    
    np.savetxt(export_name, export_array, header=export_header, delimiter=',', comments='')

#Allows normal buttons to be used as checkboxes
def toggle_button (button, button_var):
    if button_var.get() == 1:
        button.configure(relief=tk.RAISED)
        button_var.set(0)
    else:
        button.configure(relief=tk.SUNKEN)
        button_var.set(1)


#Create data storage folders if they do not exist already
path_string = "SA_data"
path = Path(path_string)
path.mkdir(parents=False, exist_ok=True)

#Makes the resource manager then spectrum analyzer(SA) objects
rm = pyvisa.ResourceManager()
SA = rm.open_resource('GPIB::11')
SA.read_termination = '\r\n' #Correctly sets the read termination
SA.write_termination = '\r\n' #Correctly sets the write termination

#Initialize the instrument
SA.write('PRS')
time.sleep(0.1)
SA.write('IM2')
time.sleep(0.1)

#Makes the object root which is the base object of the window
root = tk.Tk()
root.wm_title("HP3582A Spectrum Analyzer")


#Make a master frame to store all of the content
content = tk.Frame(root)

#Initialize the variables
trace_1 = tk.IntVar(value=0)
trace_2 = tk.IntVar(value=0)
passband_var = tk.IntVar(value=1)
sens_list = ['CAL', '30 V, + 30 dBV', '10 V, +20 dBV', '3 V, +10 dBV', '1 V, +0 dBV', '.3 V, -10 dBV', '.1 V, -20 dBV', '30 mV, -30 dBV', '10 mV, -40 dBV', '3 mV,-50 dBV']
A_sens_var = tk.StringVar(value=sens_list[1])
B_sens_var = tk.StringVar(value=sens_list[1])
transfer_sens_var = tk.StringVar(value = SA.query('LXS'))
SA.write('LST1')
A_overload_var = tk.StringVar(value='Normal')
SA.write('LST1')
B_overload_var = tk.StringVar(value='Normal')
#A_amplitude, A_phase, B_amplitude, B_phase, transfer_amplitude, transfer_phase, coherance
input_mode_vars = [tk.IntVar(value=1), tk.IntVar(value=0), tk.IntVar(value=0), tk.IntVar(value=0), tk.IntVar(value=0), tk.IntVar(value=0), tk.IntVar(value=0)]
x_scale_var = tk.IntVar(value=0)
y_scale_var = tk.IntVar(value=2)
frequency_mode_var = tk.IntVar(value=1)
span_list = ['1Hz', '2.5Hz', '5Hz', '10Hz', '25Hz', '50Hz', '100Hz', '250Hz', '500Hz', '1kHz', '2.5kHz', '5kHz', '10kHz', '25kHz']
span_var = tk.StringVar(value=span_list[13])
adjust_var = tk.IntVar(value=0)
A_coupling_var = tk.IntVar(value=1)
B_coupling_var = tk.IntVar(value=1)
avg_type_var = tk.IntVar(value=1)
sample_num_var = tk.IntVar(value=1)
shift_var = tk.IntVar(value=0)
free_run_var = tk.IntVar(value=1)
repetative_var = tk.IntVar(value=1)
alphanumerics_var = tk.StringVar(value = SA.query('LAN'))
data_points_var = tk.BooleanVar(value=False)
ref_level_var = tk.IntVar(value=0)
file_name_var = tk.StringVar(value='')
file_counter = 0

#Make a frame to put the display into
display = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Create the data display
fig = Figure(figsize=(5, 4), dpi=100)
data_display = FigureCanvasTkAgg(fig, master=display)  #Initializes the figure as a tk canvas

#create the data display toolbar
tool_bar = NavigationToolbar2Tk(data_display, display, pack_toolbar=False)
tool_bar.update()

#pack display
tool_bar.pack(side=tk.BOTTOM, fill=tk.X)
data_display.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)


#Make a frame to put the trace buttons in
trace = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make the buttons to put into trace
store_trace_1 = tk.Button(trace, text="Store Trace 1", command=lambda: [write_data('TS')])
store_trace_2 = tk.Button(trace, text="Store Trace 2", command=lambda: [write_data('RS')])
recall_trace_1 = tk.Button(trace, text="Recall Trace 1", relief=tk.RAISED, command=lambda: [toggle_button(recall_trace_1, trace_1), write_data('TR'+str(trace_1.get()))])
recall_trace_2 = tk.Button(trace, text="Recall Trace 2", relief=tk.RAISED, command=lambda: [toggle_button(recall_trace_2, trace_2), write_data('RR'+str(trace_2.get()))])

#grid trace, configure rows/columns
store_trace_1.grid(row=0, column=0, sticky='nwes')
store_trace_2.grid(row=0, column=1, sticky='nwes')
recall_trace_1.grid(row=1, column=0, sticky='nwes')
recall_trace_2.grid(row=1, column=1, sticky='nwes')
row_col_config(trace, rows=[1, 1], columns=[1, 1])


#Make a frame to put pasband radiobuttons in, define the intVar for passband
passband = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make the lable and buttons to put in the frame
passband_label = tk.Label(passband, text="Passband Shape")
flattop = tk.Radiobutton(passband, text="Flattop", variable=passband_var, value=1, command=lambda: [write_data('PS'+str(passband_var.get())), toggle_data_points ()])
hanning = tk.Radiobutton(passband, text="Hanning", variable=passband_var, value=2, command=lambda: [write_data('PS'+str(passband_var.get())), toggle_data_points ()])
uniform = tk.Radiobutton(passband, text="Uniform", variable=passband_var, value=3, command=lambda: [write_data('PS'+str(passband_var.get())), toggle_data_points ()])

#grid passband, configure rows/col
passband_label.grid(row=0, column=0, sticky='nwes')
flattop.grid(row=1, column=0, sticky='nwes')
hanning.grid(row=2, column=0, sticky='nwes')
uniform.grid(row=3, column=0, sticky='nwes')
row_col_config(passband, rows=[1,1,1,1], columns=[1])


#Make a frame to put sensetivity widgets in, define nessesary variables
sensitivity = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make the OptionMenus, Overload Indecators, Transfer Sensitivity, AutoSense Button, and labels
A_sens = tk.OptionMenu(sensitivity, A_sens_var, *sens_list, command=lambda x: [write_data(('AS' + str(sens_list.index(A_sens_var.get())+1))), refresh_overload()])
B_sens = tk.OptionMenu(sensitivity, B_sens_var, *sens_list, command=lambda x: [write_data(('BS' + str(sens_list.index(B_sens_var.get())+1))), refresh_overload()])
transfer_sens = tk.Label(sensitivity, textvariable = transfer_sens_var, highlightbackground="grey", highlightthickness=1)
auto_sens = tk.Button(sensitivity, text="Auto Sensitivity", command=set_sensitivity)
A_sens_label = tk.Label(sensitivity, text="A Sensitivity", highlightbackground="grey", highlightthickness=1)
B_sens_label = tk.Label(sensitivity, text="B Sensitivity", highlightbackground="grey", highlightthickness=1)
transfer_sens_label = tk.Label(sensitivity, text="Transfer Sensitivity", highlightbackground="grey", highlightthickness=1)
A_overload_label = tk.Label(sensitivity, text="A Overload", highlightbackground="grey", highlightthickness=1)
B_overload_label = tk.Label(sensitivity, text="B Overload", highlightbackground="grey", highlightthickness=1)
A_overload = tk.Label(sensitivity, textvariable=A_overload_var, highlightbackground="grey", highlightthickness=1)
B_overload = tk.Label(sensitivity, textvariable=B_overload_var, highlightbackground="grey", highlightthickness=1)

#grid sensitivity, congigure rows/comlumns
A_sens_label.grid(row=0, column=0, sticky='nwes')
A_sens.grid(row=1, column=0, sticky='nwes')
A_overload_label.grid(row=0, column=1, sticky='nwes')
A_overload.grid(row=1, column=1, sticky='nwes')
B_sens_label.grid(row=0, column=2, sticky='nwes')
B_sens.grid(row=1, column=2, sticky='nwes')
B_overload_label.grid(row=0,column=3, sticky='nwes')
B_overload.grid(row=1, column=3, sticky='nwes')
transfer_sens_label.grid(row=0, column=4, sticky='nwes')
transfer_sens.grid(row=1, column=4, sticky='nwes')
auto_sens.grid(row=0, rowspan=2, column=5, sticky='nwes')
row_col_config(sensitivity, rows=[1,1], columns=[4,2,4,2,4,2])


#make a frame to put input mode widgets in and to define checkbutton variables and function
input_mode = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make the needed widgets, add checkboxes to a list to allow for ease of use in enable function
im_label = tk.Label(input_mode, text="Input Mode")
im_amp_label = tk.Label(input_mode, text="Amplitude:")
im_phase_label = tk.Label(input_mode, text="Phase:")
A_amplitude = tk.Checkbutton(input_mode, text="A", variable=input_mode_vars[0], command=lambda: [toggle_im_enable(), write_data('AA'+str(input_mode_vars[0].get()))])
A_phase = tk.Checkbutton(input_mode, text="A", variable=input_mode_vars[1], command=lambda: [toggle_im_enable(), write_data('PA'+str(input_mode_vars[1].get()))])
B_amplitude = tk.Checkbutton(input_mode, text="B", variable=input_mode_vars[2], command=lambda: [toggle_im_enable(), write_data('AB'+str(input_mode_vars[2].get()))])
B_phase = tk.Checkbutton(input_mode, text="B", variable=input_mode_vars[3], command=lambda: [toggle_im_enable(), write_data('PB'+str(input_mode_vars[3].get()))])
transfer_amplitude = tk.Checkbutton(input_mode, text="Transfer", variable=input_mode_vars[4], command=lambda: [toggle_im_enable(), write_data('AX'+str(input_mode_vars[4].get()))])
transfer_phase = tk.Checkbutton(input_mode, text="Transfer", variable=input_mode_vars[5], command=lambda: [toggle_im_enable(), write_data('PX'+str(input_mode_vars[5].get()))])
coherance = tk.Checkbutton(input_mode, text="Coherance", variable=input_mode_vars[6], command=lambda: [toggle_im_enable(), write_data('CH'+str(input_mode_vars[6].get()))])
im_cb = [A_amplitude, A_phase, B_amplitude, B_phase, transfer_amplitude, transfer_phase, coherance]

#Grid input mode, configure rows/colums 
im_label.grid(row=0, column=0, columnspan=1, sticky='nwes')
im_amp_label.grid(row=1, column=0, sticky='nwes')
im_phase_label.grid(row=2, column=0, sticky='nwes')
A_amplitude.grid(row=1, column=1, sticky='nwes')
B_amplitude.grid(row=1, column=2, sticky='nwes')
transfer_amplitude.grid(row=1, column=3, sticky='nwes')
coherance.grid(row=0, column=3, sticky='nwes')
A_phase.grid(row=2, column=1, sticky='nwes')
B_phase.grid(row=2, column=2, sticky='nwes')
transfer_phase.grid(row=2, column=3, sticky='nwes')
row_col_config(input_mode, rows=[1,1,1], columns=[1,1,1,1])


#Make a frame to put the scale in, and define needed variables
scale = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make the needed widgets
x_scale_label = tk.Label(scale, text = "X Scale")
y_scale_label = tk.Label(scale, text = "Y Scale")
y_scale_lin = tk.Radiobutton(scale, text= "Linear", variable=y_scale_var, value=1, command=lambda: [write_data('SC' + str(y_scale_var.get()))])
y_scale_10dB = tk.Radiobutton(scale, text="10dB/DIV", variable=y_scale_var, value=2, command=lambda: [write_data('SC' + str(y_scale_var.get()))])
y_scale_20dB = tk.Radiobutton(scale, text="20dB/DIV", variable=y_scale_var, value=3, command=lambda: [write_data('SC' + str(y_scale_var.get()))])
x_scale_lin = tk.Radiobutton(scale, text="Linear", variable=x_scale_var, value=0, command=toggle_data_points)
x_scale_log = tk.Radiobutton(scale, text="Log", variable=x_scale_var, value=1, command=toggle_data_points)
data_points = tk.Button(scale, text ="Show Datapoints", relief=tk.RAISED, command=lambda: [toggle_button(data_points, data_points_var), toggle_data_points()])


#Grid scale, configure rows/cols
y_scale_label.grid(row=0, column=0, sticky='nwes')
x_scale_label.grid(row=0, column=1, sticky='nwes')
y_scale_lin.grid(row=1, column=0, sticky='nwes')
x_scale_lin.grid(row=1, column=1, sticky='nwes')
y_scale_10dB.grid(row=2, column=0, sticky='nwes')
x_scale_log.grid(row=2, column=1, sticky='nwes')
y_scale_20dB.grid(row=3, column=0, sticky='nwes')
data_points.grid(row=3, column=1, sticky='nwes')
row_col_config(scale, rows=[1,1,1], columns=[1,1])


#Make a frame to put frequency in, and define needed variables
frequency = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make the needed widgets
frequency_mode_label = tk.Label(frequency, text="Frequency Mode")
frequency_mode_1 = tk.Radiobutton(frequency, text="0-25kHz", variable=frequency_mode_var, value=1, command=lambda: [write_data('MD' + str(frequency_mode_var.get())), write_data('RE')])
frequency_mode_2 = tk.Radiobutton(frequency, text="0-Span", variable=frequency_mode_var, value=2, command=lambda: [write_data('MD' + str(frequency_mode_var.get())), write_data('RE')])
frequency_mode_3 = tk.Radiobutton(frequency, text="Adjust Start, Span", variable=frequency_mode_var, value=4, command=lambda: [write_data('MD' + str(frequency_mode_var.get())), write_data('RE')])
frequency_mode_4 = tk.Radiobutton(frequency, text="Ajust Center, Span", variable=frequency_mode_var, value=3, command=lambda: [write_data('MD' + str(frequency_mode_var.get())), write_data('RE')])
span_label = tk.Label(frequency, text="Freqency Span")
span_menu = tk.OptionMenu(frequency, span_var, *span_list, command=lambda x: [write_data('SP' + str(span_list.index(span_var.get())+1)), write_data('RE')])
adjust_slider = tk.Scale(frequency, label="Frequncy Adjust (Hz)", variable=adjust_var, from_=0, to=24999, orient=tk.HORIZONTAL, command=lambda x: [write_data('AD' + str(adjust_var.get()))])
ref_level_slider = tk.Scale(frequency, label="Amplitude Reference Level (dB)", variable=ref_level_var, from_=0, to=-80, orient=tk.HORIZONTAL, resolution=10, command=lambda x: [set_ref_level()])

#Grid frequency and configure rows/columns
frequency_mode_label.grid(row=0, column=1, columnspan=2, sticky='nwes')
span_label.grid(row=0, column=0, sticky='nwes')
span_menu.grid(row=1, column=0, sticky='nwes')
frequency_mode_1.grid(row=1, column=1, sticky='nwes')
frequency_mode_2.grid(row=2, column=1, sticky='nwes')
frequency_mode_3.grid(row=1, column=2, sticky='nwes')
frequency_mode_4.grid(row=2, column=2, sticky='nwes')
adjust_slider.grid(row=3, column=0, columnspan=3, sticky='nwes')
ref_level_slider.grid(row=4, column=0, columnspan=3, sticky='nwes')
row_col_config(frequency, rows=[1,1,1,4,4], columns=[1,1,1])


#Make frame to put coupling in, initiate vars
coupling = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make the needed widgets
A_coupling_label = tk.Label(coupling, text="A Coupling")
B_coupling_label = tk.Label(coupling, text="B Coupling")
A_ac = tk.Radiobutton(coupling, text="AC", variable=A_coupling_var, value=1, command=lambda: [write_data('AC' + str(A_coupling_var.get()))])
A_dc = tk.Radiobutton(coupling, text="DC", variable=A_coupling_var, value=2, command=lambda: [write_data('AC' + str(A_coupling_var.get()))])
B_ac = tk.Radiobutton(coupling, text="AC", variable=B_coupling_var, value=1, command=lambda: [write_data('BC' + str(B_coupling_var.get()))])
B_dc = tk.Radiobutton(coupling, text="DC", variable=B_coupling_var, value=2, command=lambda: [write_data('BC' + str(B_coupling_var.get()))])

#Grid coupling, config rows/columns
A_coupling_label.grid(row=0, column=0, sticky='nwes')
B_coupling_label.grid(row=0, column=1, sticky='nwes')
A_ac.grid(row=1, column=0, sticky='nwes')
B_ac.grid(row=1, column=1, sticky='nwes')
A_dc.grid(row=2, column=0, sticky='nwes')
B_dc.grid(row=2, column=1, sticky='nwes')
row_col_config(coupling, rows=[1,1,1], columns=[1,1])


#Make frame to put average in, initiate vars
average = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make the needed widgets
avg_type_label = tk.Label(average, text="Average Type")
sample_num_label = tk.Label(average, text="Sample Number")
avg_type_1 = tk.Radiobutton(average, text="Off", variable=avg_type_var, value=1, command=lambda: [write_data('AV' + str(avg_type_var.get()))])
avg_type_2 = tk.Radiobutton(average, text="RMS", variable=avg_type_var, value=2, command=lambda: [write_data('AV' + str(avg_type_var.get()))])
avg_type_3 = tk.Radiobutton(average, text="Time", variable=avg_type_var, value=3, command=lambda: [write_data('AV' + str(avg_type_var.get()))])
avg_type_4 = tk.Radiobutton(average, text="Peak", variable=avg_type_var, value=4, command=lambda: [write_data('AV' + str(avg_type_var.get()))])
sample_num_1 = tk.Radiobutton(average, text="4/64", variable=sample_num_var, value=1, command=lambda: [write_data('NU' + str(sample_num_var.get()))])
sample_num_2 = tk.Radiobutton(average, text="8/128", variable=sample_num_var, value=2, command=lambda: [write_data('NU' + str(sample_num_var.get()))])
sample_num_3 = tk.Radiobutton(average, text="16/256", variable=sample_num_var, value=3, command=lambda: [write_data('NU' + str(sample_num_var.get()))])
sample_num_4 = tk.Radiobutton(average, text="32/Exp", variable=sample_num_var, value=4, command=lambda: [write_data('NU' + str(sample_num_var.get()))])
restart_average = tk.Button(average, text="Restart", command=lambda: [write_data('RE')])
number_shift = tk.Button(average, text="Shift", command=lambda: [toggle_button(number_shift, shift_var), write_data('SH' + str(shift_var.get()))])

#Grid average, config rows/columns
avg_type_label.grid(row=0, column=0, sticky='nwes')
sample_num_label.grid(row=0, column=1, sticky='nwes')
restart_average.grid(row=1, column=2, rowspan=2, sticky='nwes')
avg_type_1.grid(row=1, column=0, sticky='nwes')
avg_type_2.grid(row=2, column=0, sticky='nwes')
avg_type_3.grid(row=3, column=0, sticky='nwes')
avg_type_4.grid(row=4, column=0, sticky='nwes')
sample_num_1.grid(row=1, column=1, sticky='nwes')
sample_num_2.grid(row=2, column=1, sticky='nwes')
sample_num_3.grid(row=3, column=1, sticky='nwes')
sample_num_4.grid(row=4, column=1, sticky='nwes')
number_shift.grid(row=3, column=2, rowspan=2, sticky='nwes')
row_col_config(average, rows=[1,1,1,1,1], columns=[2,2,1])


#Make frame to put export into
export = tk.Frame(content, highlightbackground="grey", highlightthickness=2)

#Make needed widgets
export_label = tk.Label(export, text="Export Data")
file_name_label = tk.Label(export, text="File Name:")
file_name = tk.Entry(export, textvariable=file_name_var)
save_button = tk.Button(export, text="Save", command=lambda :[export_data()])
clear_button = tk.Button(export, text='Clear', command=lambda :[file_name_var.set('')])

#Grid export, config rows/columns
export_label.grid(row=0, column=0, columnspan=2, sticky='nwes')
file_name_label.grid(row=1, column=0, columnspan=2, sticky='nwes')
file_name.grid(row=2, column=0, columnspan=2, sticky='nwes')
save_button.grid(row=3, column=0, sticky='nwes')
clear_button.grid(row=3, column=1, sticky='nwes')
row_col_config(export, rows=[1,1,1,2], columns=[1,1])


#Make misc widgets that arent in a frame
refresh_display = tk.Button(content, text="Refresh\nDisplay", command=lambda: [refresh_all_display_widgets()])
preset = tk.Button(content, text="Preset", command=lambda: [write_data('PRSIM2'), preset_values()])
alphanumerics = tk.Label(content, textvariable=alphanumerics_var, highlightbackground="grey", highlightthickness=2)
free_run = tk.Button(content, relief=tk.SUNKEN, text="Free Run", command=lambda: [toggle_button(free_run, free_run_var), write_data('FR' + str(free_run_var.get()))])
repetative = tk.Button(content, relief=tk.SUNKEN, text="Repetative", command=lambda: [toggle_button(repetative, repetative_var), write_data('RP' + str(repetative_var.get()))])
arm = tk.Button(content, text="Arm", command=lambda: [write_data('AR')])

#Update all display widgets before going to main
refresh_all_display_widgets()

#Grid everything into content, configure
display.grid(row=0, column=0, rowspan=14, columnspan=15, sticky='nwes')
refresh_display.grid(row=14, column=0, rowspan=2, columnspan=2, sticky='nwes')
preset.grid(row=16, column=0, rowspan=2, columnspan=2, sticky='nwes')
trace.grid(row=14, column=2, rowspan=4, columnspan=8, sticky='nwes')
passband.grid(row=14, column=10, rowspan=4, columnspan=5, sticky='nwes')
alphanumerics.grid(row=0, column=15, rowspan=2, columnspan=17, sticky='nwes')
sensitivity.grid(row=2, column=15, rowspan=2, columnspan=17, sticky='nwes')
input_mode.grid(row=4, column=15, rowspan=4, columnspan=12, sticky='nwes')
scale.grid(row=4, column=27, rowspan=4, columnspan=5, sticky='nwes')
frequency.grid(row=8, column=15, rowspan=5, columnspan=11, sticky='nwes')
free_run.grid(row=8, column=26, rowspan=2, columnspan=2, sticky='nwes')
repetative.grid(row=8, column=28, rowspan=2, columnspan=2, sticky='nwes')
arm.grid(row=8, column=30, rowspan=2, columnspan=2, sticky='nwes')
coupling.grid(row=10, column=26, rowspan=3, columnspan=6, sticky='nwes')
average.grid(row=13, column=15, rowspan=5, columnspan=12, sticky='nwes')
export.grid(row=13, column=27, rowspan=5, columnspan=5, sticky='nwes')
row_col_config(content, rows=[1]*18, columns=[1]*32)

#Grid content into root, configure
content.grid(row=0, column=0, sticky='nwes')
row_col_config(root, rows=[1], columns=[1])

root.mainloop() #Initiates the main loop for Tkinter
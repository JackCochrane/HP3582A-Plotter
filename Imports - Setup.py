# -*- coding: utf-8 -*-
"""
Created on Fri Jul 25 10:11:47 2025

@author: jackc

Run this file to use the MakePlot function to get data from the Spectrum Analyzer
"""

import pyvisa 
import numpy as np
import matplotlib.pyplot as plt
import re
import time

def initialize ():
    rm = pyvisa.ResourceManager() #Assigns the resource manager to an easier to use form
    
    resource_tuple = rm.list_resources() #Gets a tuple with resources available to pyvisa
    
    #This loop iterates through the tuple retuned by list_resources to find the instrument using GPIB
    #Then connects to it, assigning it to SA or 'Spectrum Analyzer'
    for x in resource_tuple: 
        if re.search("^GPIB", x) != None:
            SA = rm.open_resource(x)
            break
    
    SA.read_termination = '\r\n' #Correctly sets the read termination
    SA.write_termination = '\r\n' #Correctly sets the write termination
    return rm, SA

def make_plot (MD = 1, AD = 0, SP = 14, IM = 'bodefull', PM = 'lin', PHAS = 0, line = 1, point_mark = 0):
    #Checking for error states from the given inputs
    if not (type(MD) or type(AD) or type(SP) or type(PHAS) or type(line) or type (point_mark)) is int:
        raise TypeError("MD, AD, SP, SENS, line, and point_mark must all be integers")
    if MD<1 or MD>4:
        raise ValueError("MD must be between 1-4")
    if AD<0 or AD>24999:
        raise ValueError("AD must be between 0-24999")
    if SP<1 or SP>14:
        raise ValueError("SP must be 1-14")
    if PHAS<0 or PHAS>1:
        raise ValueError("PHAS must be 0 or 1")
    if line<0 or line<1:
        raise ValueError("line must be 0 or 1")
    if point_mark<0 or point_mark>1:
        raise ValueError("point_mark must be 0 or 1")
    if not (type(IM) or type(PM)) is str:
        raise TypeError("IM and PM must be strings")
    IM = IM.lower()
    if IM not in {'bodefull', 'bodehalf', 'a', 'b', 'bothhalf', 'bothfull'}:
        raise ValueError("IM must be 'bodehalf' 'bodefull' 'a' 'b' 'bothhalf' or 'bothfull'")
    PM = PM.lower()
    if PM not in {'lin', 'logx', 'log', 'logy', 'logxy'}:
        raise ValueError("PM must be 'lin' 'log' 'logx' 'logy' or 'logxy'")
    if MD in {1, 2} and AD != 0:
        raise ValueError("In MD 1 or 2 AD must be 0")
        
    #Initialize the connection, sets to PRS
    rm, SA = initialize()
    SA.write('PRS')
    
    #Implement the range selection and sets the sensitivity
    SA.write('MD' + str(MD) + 'AD' + str(AD) + 'SP' + str(SP))
    set_sensitivity()
    
    #Generate y array, time.sleep is there because SA is old and slow
    if PHAS == 0:
        if IM == 'bodefull':
            AValues = SA.query_ascii_values('LDS', container=np.array)
            time.sleep(0.5)
            SA.write('IM3AA0AB1')
            time.sleep(0.5)
            BValues = SA.query_ascii_values('LDS', container=np.array)
            YValues = BValues / AValues
        elif IM == 'bodehalf':
            SA.write('IM2AB1')
            time.sleep(0.5)
            AValues, BValues = np.split(SA.query_ascii_values('LDS', container=np.array), 2)
            YValues = BValues / AValues
        elif IM == 'a':
            YValues = SA.query_ascii_values('LDS', container=np.array)
        elif IM == 'b':
            SA.write('IM3AA0AB1')
            time.sleep(0.5)
            YValues = SA.query_ascii_values('LDS', container=np.array)
        elif IM == 'bothhalf':
            SA.write('IM2AB1')
            time.sleep(0.5)
            YValues, YYValues = np.split(SA.query_ascii_values('LDS', container=np.array), 2)
        else:
            YValues = SA.query_ascii_values('LDS', container=np.array)
            time.sleep(0.5)
            SA.write('IM3AA0AB1')
            time.sleep(0.5)
            YYValues = SA.query_ascii_values('LDS', container=np.array)
    else:
        SA.write('AA0PA1')
        if IM == 'bodefull':
            AValues = SA.query_ascii_values('LDS', container=np.array)
            time.sleep(0.5)
            SA.write('IM3PA0PB1')
            time.sleep(0.5)
            BValues = SA.query_ascii_values('LDS', container=np.array)
            YValues = BValues / AValues
        elif IM == 'bodehalf':
            SA.write('IM2PB1')
            time.sleep(0.5)
            AValues, BValues = np.split(SA.query_ascii_values('LDS', container=np.array), 2)
            YValues = BValues / AValues
        elif IM == 'a':
            YValues = SA.query_ascii_values('LDS', container=np.array)
        elif IM == 'b':
            SA.write('IM3PA0PB1')
            time.sleep(0.5)
            YValues = SA.query_ascii_values('LDS', container=np.array)
        elif IM == 'bothhalf':
            SA.write('IM2PB1')
            time.sleep(0.5)
            YValues, YYValues = np.split(SA.query_ascii_values('LDS', container=np.array), 2)
        else:
            YValues = SA.query_ascii_values('LDS', container=np.array)
            time.sleep(0.5)
            SA.write('IM3PA0PB1')
            time.sleep(0.5)
            YYValues = SA.query_ascii_values('LDS', container=np.array)
    
    
    #Generate Frequency array
    if MD == 4:
        FreqValues = np.linspace (SA.query_ascii_values('LAD')[0] - 0.5 * SA.query_ascii_values('LSP')[0], SA.query_ascii_values('LAD')[0] + 0.5 * SA.query_ascii_values('LSP')[0], num = YValues.size)
    else:
        FreqValues = np.linspace (SA.query_ascii_values('LAD')[0], SA.query_ascii_values('LSP')[0] + SA.query_ascii_values('LAD')[0], num = YValues.size)
        
    #Sets the line and point types
    line_point = ''
    if line == 1:
        line_point = line_point + '-'
    if point_mark == 1:
        line_point = line_point + 'o'
    if 1 not in {line, point_mark}:
        line_point = '-'
    
    #Generate the plot
    if IM != 'bothhalf' and IM != 'bothfull':
        fig, ax = plt.subplots()
        if PM == 'lin':
            ax.plot(FreqValues, YValues, line_point)
        elif PM == 'log' or PM == 'logx':
            ax.semilogx(FreqValues, YValues, line_point)
        elif PM == 'logy':
            ax.semilogy(FreqValues, YValues, line_point)
        else:
            ax.loglog(FreqValues, YValues, line_point)
        return_values = [FreqValues, YValues]
    else:
        fig, axs = plt.subplots(2, sharex=True)
        axs[0].set_title('Plot of A')
        axs[1].set_title('Plot of B')
        if PM == 'lin':
            axs[0].plot(FreqValues, YValues, line_point)
            axs[1].plot(FreqValues, YYValues, line_point)
        elif PM == 'log' or PM == 'logx':
            axs[0].semilogx(FreqValues, YValues, line_point)
            axs[1].semilogx(FreqValues, YYValues, line_point)
        elif PM == 'logy':
            axs[0].semilogy(FreqValues, YValues, line_point)
            axs[1].semilogy(FreqValues, YYValues, line_point)
        else:
            axs[0].loglog(FreqValues, YValues, line_point)
            axs[1].loglog(FreqValues, YYValues, line_point)
        return_values = [FreqValues, YValues, YYValues]
    
    #return a list with the x/y arrays inside of it
    return return_values
    
#Sets the sensitivity of the spectrum analyzer to the most sensitive it can be without overloading
def set_sensitivity():
    rm, SA = initialize() #initializes the resource manager and the spectrum analyzer
    
    AS = 10 #Starting value for A sensitivity
    BS = 10 #Starting value for B sensitivity
    
    SA.write('AS' + str(AS) + 'BS' + str(BS) + 'IM2') #sets the sensitivities to the starting values
    time.sleep(0.1)
    status_word = SA.query_binary_values('LST1', datatype = 'uint8') #Reads the status word
    
    #This loop sets the sensitivity to the most sensitive option
    while status_word & 4 or status_word & 8: #Checks if A overload or B overload flags are raised
        if status_word & 4: #Decreases A sens if A overload flag is raised
            AS=AS-1
        if status_word & 8: #Decreases B sens if B overload flag is raised
            BS=BS-1
        if AS<2 or BS<2:
            raise ValueError("Sensitivity went out of bounds") #Prevents sending the SA an invalid command
        SA.write('AS' + str(AS) + 'BS' + str(BS))
        SA.write('LST0') #reset status word
        time.sleep(0.25) #waits to make sure an overload is caught if it will occur
        status_word = SA.query_binary_values('LST1', datatype = 'uint8') #reads the status word


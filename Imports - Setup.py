# -*- coding: utf-8 -*-
"""
Created on Fri Jul 25 10:11:47 2025

@author: jackc

Run this file to use the MakePlot function to get data from the Spectrum Analyzer
"""

import pyvisa 
import numpy
import matplotlib.pyplot as plt
import re
import time

rm = pyvisa.ResourceManager() #Assigns the resource manager to an easier to use form

resource_tuple = rm.list_resources() #Gets a tuple with resources available to pyvisa

#This loop iterates through the tuple retuned by list_resources to find the instrument using GPIB
#Then connects to it, assigning it to SA or 'Spectrum Analyzer'
for x in resource_tuple: 
    if re.search("^GPIB", x) != None:
        SA = rm.open_resource(x)
        del x
        del resource_tuple
        break

SA.read_termination = '\r\n' #Correctly sets the read termination
SA.write_termination = '\r\n' #Correctly sets the write termination

SA.write('PRS') #Sets the spectrum analyzer into preset state

def MakePlot (MD = 1, AD = 0, SP = 14, SENS = 2, IM = 'bodefull', PM = 'lin', PHAS = 0):
    #Checking for error states from the given inputs
    if not (type(MD) or type(AD) or type(SP) or type(SENS) or type(PHAS)) is int:
        raise TypeError("MD, AD, SP, and SENS must all be integers")
    if MD<1 or MD>4:
        raise ValueError("MD must be between 1-4")
    if AD<0 or AD>24999:
        raise ValueError("AD must be between 0-24999")
    if SP<1 or SP>14:
        raise ValueError("SP must be 1-14")
    if SENS<1 or SENS>10:
        raise ValueError("SENS must be 1-10")
    if PHAS<0 or PHAS>1:
        raise ValueError("PHAS must be 0 or 1")
    if not (type(IM) or type(PM)) is str:
        raise TypeError("IM and PM must be strings")
    IM = IM.lower()
    if IM != 'bodefull' and IM != 'bodehalf' and IM != 'a' and IM != 'b' and IM != 'bothhalf' and IM != 'bothfull':
        raise ValueError("IM must be 'bodehalf' 'bodefull' 'a' 'b' 'bothhalf' or 'bothfull'")
    PM = PM.lower()
    if PM != 'lin' and PM != 'logx' and PM != 'log' and PM != 'logy' and PM != 'logxy':
        raise ValueError("PM must be 'lin' 'log' 'logx' 'logy' or 'logxy'")
    if (MD == (1 or 2)) and AD != 0:
        raise ValueError("In MD 1 or 2 AD must be 0")
    
    #Set the instrument to known values
    SA.write('PRS')
    
    #Implement the range and sensitivity selections
    SA.write('MD' + str(MD) + 'AD' + str(AD) + 'SP' + str(SP) + 'AS' + str(SENS) + 'BS' + str(SENS))
    
    #Generate y array, time.sleep is there because SA is old and slow
    if PHAS == 0:
        if IM == 'bodefull':
            AValues = SA.query_ascii_values('LDS', container=numpy.array)
            time.sleep(0.5)
            SA.write('IM3AA0AB1')
            time.sleep(0.5)
            BValues = SA.query_ascii_values('LDS', container=numpy.array)
            YValues = BValues / AValues
            del BValues, AValues
        elif IM == 'bodehalf':
            SA.write('IM2AB1')
            time.sleep(0.5)
            AValues, BValues = numpy.split(SA.query_ascii_values('LDS', container=numpy.array), 2)
            YValues = BValues / AValues
            del BValues, AValues
        elif IM == 'a':
            YValues = SA.query_ascii_values('LDS', container=numpy.array)
        elif IM == 'b':
            SA.write('IM3AA0AB1')
            time.sleep(0.5)
            YValues = SA.query_ascii_values('LDS', container=numpy.array)
        elif IM == 'bothhalf':
            SA.write('IM2AB1')
            time.sleep(0.5)
            YValues, YYValues = numpy.split(SA.query_ascii_values('LDS', container=numpy.array), 2)
        else:
            YValues = SA.query_ascii_values('LDS', container=numpy.array)
            time.sleep(0.5)
            SA.write('IM3AA0AB1')
            time.sleep(0.5)
            YYValues = SA.query_ascii_values('LDS', container=numpy.array)
    else:
        SA.write('AA0PA1')
        if IM == 'bodefull':
            AValues = SA.query_ascii_values('LDS', container=numpy.array)
            time.sleep(0.5)
            SA.write('IM3PA0PB1')
            time.sleep(0.5)
            BValues = SA.query_ascii_values('LDS', container=numpy.array)
            YValues = BValues / AValues
            del BValues, AValues
        elif IM == 'bodehalf':
            SA.write('IM2PB1')
            time.sleep(0.5)
            AValues, BValues = numpy.split(SA.query_ascii_values('LDS', container=numpy.array), 2)
            YValues = BValues / AValues
            del BValues, AValues
        elif IM == 'a':
            YValues = SA.query_ascii_values('LDS', container=numpy.array)
        elif IM == 'b':
            SA.write('IM3PA0PB1')
            time.sleep(0.5)
            YValues = SA.query_ascii_values('LDS', container=numpy.array)
        elif IM == 'bothhalf':
            SA.write('IM2PB1')
            time.sleep(0.5)
            YValues, YYValues = numpy.split(SA.query_ascii_values('LDS', container=numpy.array), 2)
        else:
            YValues = SA.query_ascii_values('LDS', container=numpy.array)
            time.sleep(0.5)
            SA.write('IM3PA0PB1')
            time.sleep(0.5)
            YYValues = SA.query_ascii_values('LDS', container=numpy.array)
    
    
    #Generate Frequency array
    if MD == 4:
        FreqValues = numpy.linspace (SA.query_ascii_values('LAD')[0] - 0.5 * SA.query_ascii_values('LSP')[0], SA.query_ascii_values('LAD')[0] + 0.5 * SA.query_ascii_values('LSP')[0], num = YValues.size)
    else:
        FreqValues = numpy.linspace (SA.query_ascii_values('LAD')[0], SA.query_ascii_values('LSP')[0] + SA.query_ascii_values('LAD')[0], num = YValues.size)
        
    #Generate the plot
    if IM != 'bothhalf' and IM != 'bothfull':
        fig, ax = plt.subplots()
        if PM == 'lin':
            ax.plot(FreqValues, YValues)
        elif PM == 'log' or PM == 'logx':
            ax.semilogx(FreqValues, YValues)
        elif PM == 'logy':
            ax.semilogy(FreqValues, YValues)
        else:
            ax.loglog(FreqValues, YValues)
    else:
        fig, axs = plt.subplots(2, sharex=True)
        axs[0].set_title('Plot of A')
        axs[1].set_title('Plot of B')
        if PM == 'lin':
            axs[0].plot(FreqValues, YValues)
            axs[1].plot(FreqValues, YYValues)
        elif PM == 'log' or PM == 'logx':
            axs[0].semilogx(FreqValues, YValues)
            axs[1].semilogx(FreqValues, YYValues)
        elif PM == 'logy':
            axs[0].semilogy(FreqValues, YValues)
            axs[1].semilogy(FreqValues, YYValues)
        else:
            axs[0].loglog(FreqValues, YValues)
            axs[1].loglog(FreqValues, YYValues)
    
    
    

    
    
    
    


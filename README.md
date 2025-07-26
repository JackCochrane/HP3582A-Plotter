# HP3582A-Plotter

For use in Spyder IDE, initializes connection with the HP3582A and creates the MakePlot function. I have only tested it in Spyder, and have not done so thouroughly. If you have any issues email me at jackcochrane119@gmail.com and ill see if I cant help fix the issue.

# External Requirements

Installed from NI: NI-Visa, NI-488.2.  
Installed packages in Spyder: pyvisa, numpy, matplotlib, re, time.

# MakePlot function

The make plot function allows you to generate a number of plots from the spectrum analyzer using various arguments. Each argument has a default value, and any of the arguments of datatype string (str) are case insensitive.  
The function: MakePlot (**MD**, **AD**, **SP**, **SENS**, **IM**, **PM**, **PHAS**)  
**MD** (Frequency Select **M**o**D**e) accepts integers 1-4, defaults to 1. The modes can be found in the attached PDF and are:
1. 0 to 25 kHz
2. 0 to **SP**
3. **AD** to **SP**+**AD**
4. **AD**-0.5$$\times$$**SP** to **AD**+0.5$$\times$$**SP**

**AD** (Frequency **AD**just) accepts integers 0-24999 and is in Hz, defaults to 0 (Note: **AD** *MUST* be 0 for **MD** 1 and 2.)  
**SP** (Frequency **SP**an) accepts integers 1-14, defaults to 14. The spans can be found in the attached PDF and are:  
1. 1Hz
2. 2.5Hz
3. 5Hz
4. 10Hz
5. 25Hz
6. 50Hz
7. 100Hz
8. 250Hz
9. 500Hz
10. 1kHz
11. 2.5kHz
12. 5kHz
13. 10kHz
14. 25kHz

**SENS** (CH A **SENS**itivity and CH B **SENS**itivity) accepts integers 1-10, defaults to 2. The sensitivities can be found in the attached PDF as **AS** and **BS** and are:
1. CAL
2. 30V, +30dBV
3. 10V, +20dBV
4. 3V, +10dBV
5. 1V, +0dBV
6. 300mV, -10dBV
7. 100mV, -20dBV
8. 30mV, -30dBV
9. 10mV, -40dBV
10. 3mV, -50dBV

**IM** (**I**nput **M**ode) accepts 'bodehalf' 'bodefull' 'a' 'b' 'bothhalf' or 'bothfull', defaults to 'bodefull'. Tells MakePlot what inputs to take. The options are:
- 'bodefull'. Which takes the inputs from CH A and then CH B and devides CH B by CH A, with a resolution of 256 points over the span each.
- 'a'. Which takes the inputs from CH A with a resolution of 256 points over the span.  
- 'b'. Which takes the inputs from CH B with a resolution of 256 points over the span.  
- 'bothhalf'. Which takes the inputs from CH A and CH B at the same time, with a resolution of 128 points over the span each.  
- 'bothfull'. Which takes the inputs from CH A and then CH B, with a resolution of 256 points over the span each.  

**PM** (**P**lot **M**ode) accepts 'lin' 'log' 'logx' 'logy' or 'logxy', defaults to 'lin'. Tells MakePlot what type of scale to use. The options are:
- 'lin'. Which makes all axes linear.
- 'log' and 'logx'. Which makes all x axes log scale.
- 'logy'. Which makes all y axes log scale.
- 'logxy'. Which makes all axes log scale.

**PHAS** (CH A **PHAS**e and CH B **PHAS**e) accepts 0 and 1, defaults to 0. If 0 the amplitude will be plotted. If 1 the phase will be plotted.





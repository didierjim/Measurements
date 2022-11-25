#================================20211103 version========================================#
#   Applied voltages of the three Kepcos are predicted with Keras deep learning models
#   The code should be run under the "tensorflow" environment   
#   Field scan limits of field scan
#       Hx = +-1900 Oe
#       Hy = +-2500 Oe
#       Hz = +-1600 Oe   
#   Field scan limits of angle scan
#       phi scan   = 1900 Oe
#       theta scan = 1000 Oe
#   Field scan limits of loop shift
#       Hx = +-1500 Oe
#       Hz = +-600  Oe
#========================================================================================#

from tkinter import *
from tkinter import ttk
import tkinter
from tkinter import filedialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import pylab
from pylab import *
import os
import math
import numpy as np
import nidaqmx
import csv
from LockinAmp_TCC import lockinAmp
from keithley6221 import Keithley6221
from GMW import GMW
import time
import multiprocessing
import threading
from datetime import datetime
import re
from pymeasure import instruments

root = Tk()
root.title("Harmonic Hall Angular Scan with K6221")

def main():

    global result, func, average, sense, signal, freq, tc, maxV, directory, dot_size, dot_edge

    directory = os.getcwd()


    func='1st' #Set a default mode (1st or 2nd)
    sense='100nV' #Set a default sensitivity range
    signal=5 #Set a default OSC signal voltage (V)
    freq=85 #Set a default OSC frequency (Hz)
    tc = '1ms' #Set a default time constant
    maxV = 0

    read_me = 'This program delivers a AC current by Keithley 6221 and senses current from the Lock-in. Hall resistance is measured per angle.'

    print(read_me)

    dot_size=10 #Set a default data dot size
    dot_edge=0.5 #Set a default data dot edge width

    result=['']
    values_y=[]
    values_x=[]

    createWidgit()

    root.protocol('WM_DELETE_WINDOW', quit)
    root.mainloop()

#************************Main End Here***************************#
def Convert(string):
        li = list(string.split("/"))
        lii=[]
        for i in li:
            lii.append(float(i))
        return lii

def measureMethod(_number, _average, _signal, _frequency, _Hin, _sample, _angle, _resistance):
    global state

    num=int(_number)       # number of points measured per anglefield sweep
    average=int(_average)  # number of measurements averaged by Lock-in Amp
    sig=float(_signal)     # K6221 output ac current (mA)
    freq=float(_frequency) # K6221 signal frequency (Hz)
    res=float(_resistance)
    if _Hin == '*':
        Hlist = [800.0,1000.0,1300.0,1500.0,1700.0,1900.0]
    else:
        Hlist = Convert(_Hin)     # In-plane field magnitude
    [angi,angf] = Convert(_angle) # Set initiating angle and final angle
    state = "measure"
        

    def event():

        for H in Hlist:

            sen_uni = re.findall(r'(\d+)(\w+)',sense)[0][1]
            tc_uni  = re.findall(r'(\d+)(\w+)',tc)[0][1]
            tc_n   = re.findall(r'(\d+)(\w+)',tc)[0][0]
            if tc_uni=="ms":
                t_py = float(tc_n)*10**(-3)
            else:
                t_py = float(tc_n)*1
            print('Time constant is set to:',t_py)
            res_uni = 'ohm'
            if sen_uni == 'mV':
                res_uni = 'ohm'
            elif sen_uni == 'uV':
                res_uni = 'mohm'
            amp = lockinAmp(func,sense,0,freq,tc) #Initiate Lock-in
            time.sleep(0.5)
            #to make sure the time constant is changed to the nominal value
            amp_pymeasure = instruments.signalrecovery.DSP7265('GPIB1::12::INSTR')
            amp_pymeasure.time_constant = t_py
            amp_pymeasure.frequency = freq
            #double check tc
            tc_try = 0
            tc_flag = 'successful'
            while amp_pymeasure.time_constant != t_py and tc_try<10:
                amp_pymeasure.time_constant = t_py
                print('Time constant is wrong:',amp_pymeasure.time_constant,'s')
                tc_try+=1
            if tc_try ==10:
                tc_flag = 'failed'
                print('Measurement is terminated due to tc issue')
            K6221 = Keithley6221('GPIB1::10')
            K6221.ac_output_on(freq=freq, current=sig, duration=600, waveform='SIN') #Initiate Keithley6221
            gmw = GMW()                             #Initiate GMW Magnet
            recipe_list=[30,50,70,100,200,500,800,1000,1300,1500,1700,1900]
            if H in recipe_list:
                angmagV = np.loadtxt('C:\\Users\\doc\\Desktop\\GUI_Harmonic_Measurement\\recipe-60\\'+str(H)+'.csv',delimiter=',')
                ang=np.arange(0,363,6)
            else:
                ang, angmagV = gmw.anglescan(H, num, angi, angf, "xy")
                ang = ang*180/np.pi
            maxV = np.max(angmagV)
            
            

            ax.clear()
            ax.grid(True)
            ax.set_title("Harmonic Hall Voltage vs Angle Plot")
            ax.set_xlabel("Applied Field Angle (degree)")
            ax.set_ylabel("Lock-In A-B/Iapplied (Ohm)")
            graph_name = "Harmonic Angular Scan "+str(round(H,2))+"Oe "+str(round(sig,2))+"mA"
            ax.set_title(graph_name)
            listbox_l.insert('end',"Now measuring with Iac = %f (mA)" %(sig))
            listbox_l.insert('end',"Now measuring with Hin = %f (Oe)" %(H))
            listbox_l.see(END)


            #Prepare data entries
            global values_x, values_y, result

            values_y1=[]
            values_y2=[]
            values_y3=[]
            values_x=[]
            result=[]

            gmw.write([0,0,0])

            for g in range(num+1):
                if state == "stop" or tc_flag == "failed":
                    #gmw.zero()
                    #gmw.shutdown()
                    #K6221.ac_output_off()
                    #K6221.shutdown()
                    #amp_pymeasure.shutdown()
                    #amp.shutdown()
                    if g == num+1:
                        print('end')
                    #root.quit()

                elif state == "measure":
                    gmw.writetask.write(angmagV[g])
                    if g == 0:
                        time.sleep(10)
                        trial = amp.readX(20)

                    #sleep to obtain stable signals
                    if tc_uni=="ms":
                        t = float(tc_n)*10**(-3)*3
                    else:
                        t = float(tc_n)*1

                    time.sleep(t)
                    data1, data2 = 0,0
                    data1 = amp.readX(average)/sig *(-1)*np.sqrt(2)# mV/mA=Ohm
                    print(amp.readX(average))
                    data2 = amp.readY(average)/sig *(-1)*np.sqrt(2)#correction for phase and Vrms

                    values_y1.append(data1)
                    values_y2.append(data2)
                    values_y3.append((data1**2+data2**2)**0.5)
                    values_x.append(ang[g])


                    if g>0:
                        ax.plot(values_x[g-1:g+1], values_y1[g-1:g+1],'b-o', ms=dot_size, mew=dot_edge, alpha=0.5)
                        canvas.draw()
                    #listbox_l.insert('end', "Resistance:" + str(round(data1,4)) + "\t \t AppliedFieldAngle:" + str(round(ang[g],4)))
                    #listbox_l.see(END)
                    print("AppliedFieldAngle: " + str(round(ang[g],4)),end='\r')

            

            #Setup timestamp
            if state == "measure" and tc_flag == 'successful':
                stamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
                listbox_l.insert('end', str(stamp))

                file = open(str(directory)+"/"+str(_sample)+"_K6221_"+str(func)+"_"+str(H)+"Oe"+"_"+str(freq)+"Hz"+"_"+str(sig)+"mA"+"_"+str(stamp)+".csv", "w")
                file.write(""+str(_sample)+ "\n")
                file.write("Applied field: "+str(H)+"(Oe)\n")
                file.write("Sensitivity: "+str(sense)+"\n")
                file.write("Time Constant: "+str(tc)+"\n")
                file.write("Frequency: "+str(freq)+"(Hz)\n")
                #file.write("2P Resistance: "+str(res)+"(kohm)\n")
                file.write("Number"+","+"Angle(degree)"+","+"X(Ohm)"+","+"Y(Ohm) \n" )

                cnt=1
                #output all data
                for a in range(len(values_y1)):

                    file.write(str(cnt)+","+str(values_x[a])+","+str(values_y1[a])+","+str(values_y2[a])+"\n")
                    cnt +=1

                file.close()

            gmw.zero()
            gmw.shutdown()
            K6221.ac_output_off()
            K6221.shutdown()
            amp_pymeasure.shutdown()
            amp.shutdown()

            listbox_l.insert('end', "The Measurement data is saved.")
            listbox_l.see(END)
            listbox_l.insert('end',"Measurement finished")
            listbox_l.see(END)

    #Hlist = Convert(_Hin)

    if (float(maxV))<=10:

        th = threading.Thread(target=event)
        th.start()

    else:
        listbox_l.insert('end',"Your output field is TOO LARGE!")
        listbox_l.see(END)
        print("Your output field is TOO LARGE!")


def stopMethod():
    global state
    state = "stop"
    listbox_l.insert('end',"Stop Measurement")
    listbox_l.see(END)

def measurethread(  _Hin, _average, _current, _sample, _number, _angle):
    t1=threading.Thread(target= lambda : measureMethod(_number, _average, _signal, _frequency, _Hin, _sample,_angle,_resistance), daemon=True)
    t1.start()

# Option:1st or 2nd harmonic
def optionMethod(val):

    global func

    func = val

    listbox_l.insert('end', "Detecting the %s harmonic voltage" %func)
    listbox_l.see(END)

# Sensitivity: How many mVs or uVs
def senseMethod(val):

    global sense

    sense = val

    listbox_l.insert('end', "Sensing range set to:",sense)
    listbox_l.see(END)

def tcMethod(val):

    global tc

    tc = val

    listbox_l.insert('end', "Time constant set to:",tc)
    listbox_l.see(END)


def dirMethod():

    global directory

    directory = filedialog.askdirectory()

    listbox_l.insert('end', directory)
    listbox_l.see(END)


def clearMethod():

    ax.clear()
    ax.grid(True)
    ax.set_title("Average Hall Resistance vs H Plot")
    ax.set_xlabel("Applied Field Angle (degree)")
    ax.set_ylabel("Lock-In X (mV)")
    ax.axis([-1, 1, -1, 1])

    canvas.draw()
    listbox_l.delete(0, END)

    print("clear all")


def quitMethod():

    amp = lockinAmp(func,sense,tc)
    gmw.zero()

    listbox_l.insert('end', "All fields set to zero.")
    listbox_l.see(END)
    time.sleep(1)

    global root

    root.quit()

def createWidgit():

    global ax, canvas, listbox_l, result, func, frame, sense

    fig = pylab.figure(1)

    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_title("Harmonic Hall Voltage vs Angle Plot")
    ax.set_xlabel("Applied Field Angle (degree)")
    ax.set_ylabel("Lock-In A-B (mV)")
    ax.axis([-1, 1, -1, 1])


    content = ttk.Frame(root, padding=(3,3,12,12))

    #plotting area
    frame = ttk.Frame(content, borderwidth=0, relief="sunken",padding=(3,3,12,12))
    frame_setting = ttk.Frame(content)
    frame_information = ttk.Frame(content, padding = (3,3,12,12))
    frame_buttomArea = ttk.Frame(content)

    #Save Variables
    entry_sample = ttk.Entry(frame_information); entry_sample.insert(0, "sample_name")

    #Function Variables
    entry_number = ttk.Entry(frame_setting); entry_number.insert(0,"60")
    entry_average = ttk.Entry(frame_setting); entry_average.insert(0,"5")
    entry_signal = ttk.Entry(frame_setting); entry_signal.insert(0,"1")
    entry_frequency = ttk.Entry(frame_setting); entry_frequency.insert(0,"1000")
    entry_Hin = ttk.Entry(frame_setting); entry_Hin.insert(0,"1000")
    entry_angle =  ttk.Entry(frame_setting); entry_angle.insert(0,"0/360")
    entry_resistance = ttk.Entry(frame_setting); entry_resistance.insert(0,"1")


    value = tkinter.StringVar() #mode
    value2 = tkinter.StringVar() #sensitivity
    value3 = tkinter.StringVar() #time constant


    mode = ["1st","1st","2nd"]
    sensitivity = ["50mV","1V","500mV","200mV","100mV","50mV","20mV","10mV","5mV","2mV","1mV","500uV","200uV","100uV","50uV","20uV","10uV","5uV","2uV","1uV"]
    tc = ["200ms","5ms","10ms","20ms","50ms","100ms","200ms","500ms","1s","2s"]


    option_mode = ttk.OptionMenu(frame_setting, value, *mode, command = optionMethod)
    option_sensitivity = ttk.OptionMenu(frame_setting, value2, *sensitivity, command = senseMethod)
    option_tc = ttk.OptionMenu(frame_setting, value3, *tc, command = tcMethod)



    listbox_l = Listbox(frame_information,height=5)
    scrollbar_s = ttk.Scrollbar(frame_information, orient=VERTICAL, command=listbox_l.yview)

    #Save setings
    label_sample = ttk.Label(frame_information, text = "Sample Name")

    #Funciton settings
    label_mode = ttk.Label(frame_setting, text="Harmonic mode:")
    label_sensitivity = ttk.Label(frame_setting, text="Sensitivity:")
    label_average = ttk.Label(frame_setting, text="Averages:")
    label_signal = ttk.Label(frame_setting, text="AC current (mA):")
    label_frequency = ttk.Label(frame_setting, text="Freq (Hz):")
    label_Hin = ttk.Label(frame_setting, text="Hin field (Oe):")
    label_number = ttk.Label(frame_setting, text="Points per scan:")
    label_tc = ttk.Label(frame_setting, text="Time Constant:")
    label_angle = ttk.Label(frame_setting, text="Scan Angle Range (degree):")
    label_resistance = ttk.Label(frame_setting, text="2P Resistance (kohm):")
    label_empty = ttk.Label(frame_setting, text="")




    button_measure = ttk.Button(frame_buttomArea, text ="Measure", \
        command = lambda : measureMethod(entry_number.get(),\
            entry_average.get(),entry_signal.get(),entry_frequency.get(),\
            entry_Hin.get(), entry_sample.get(), entry_angle.get(), entry_resistance.get() ))

    button_dir  = ttk.Button(frame_buttomArea, text="Change directory", command = dirMethod)
    button_stop = ttk.Button(frame_buttomArea, text="Stop", command = stopMethod)
    button_output = ttk.Button(frame_buttomArea, text="Output", \
        command = lambda : outputMethod(entry_signal.get(),entry_frequency.get()))
    button_clear = ttk.Button(frame_buttomArea, text="Clear", command = clearMethod)

    #Attatch Plot
    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.get_tk_widget().grid(row=0, column =0, pady =0, padx =0,sticky='nsew')
    content.grid(column=0, row=0, sticky=(N, S, E, W))
    frame.grid(column=0, row=0, columnspan=3, rowspan=30, sticky=(N, S, E, W))


    frame_setting.grid(column=3, row=0, columnspan=2, rowspan=30, sticky=(N, S, E, W))

    #Frame setting grid

    label_mode.grid(column=0, row=1, columnspan=2, sticky=(N, W), padx=5)
    option_mode.grid(column=0, row=2, columnspan=2, sticky=(N, W), padx=5)
    label_sensitivity.grid(column=0, row=3, columnspan=2, sticky=(N, W), padx=5)
    option_sensitivity.grid(column=0, row=4, columnspan=2, sticky=(N, W), padx=5)
    label_tc.grid(column=0, row=5, columnspan=2, sticky=(N, W), padx=5)
    option_tc.grid(column=0, row=6, columnspan=2, sticky=(N, W), padx=5)
    label_Hin.grid(column=0, row=7, columnspan=2, sticky=(N, W), padx=5)
    entry_Hin.grid(column=0, row=8, columnspan=2, sticky=(N, W), padx=5)
    label_number.grid(column=0, row=9, columnspan=2, sticky=(N, W), padx=5)
    entry_number.grid(column=0, row=10, columnspan=2, sticky=(N, W), padx=5)
    label_signal.grid(column=0, row=11, columnspan=2, sticky=(N, W), padx=5)
    entry_signal.grid(column=0, row=12, columnspan=2, sticky=(N, W), padx=5)
    label_frequency.grid(column=0, row=13, columnspan=2, sticky=(N, W), padx=5)
    entry_frequency.grid(column=0, row=14, columnspan=2, sticky=(N, W), padx=5)
    label_average.grid(column=0, row=15, columnspan=2, sticky=(N, W), padx=5)
    entry_average.grid(column=0, row=16, columnspan=2, sticky=(N, W), padx=5)
    label_angle.grid(column=0, row=17, columnspan=2, sticky=(N, W), padx=5)
    entry_angle.grid(column=0, row=18, columnspan=2, sticky=(N, W), padx=5)
    #label_resistance.grid(column=0, row=19, columnspan=2, sticky=(N, W), padx=5)
    #entry_resistance.grid(column=0, row=20, columnspan=2, sticky=(N, W), padx=5)
    #label_xchan.grid(column=0, row=23, columnspan=2, sticky=(N, W), padx=5)
    #label_ychan.grid(column=0, row=24, columnspan=2, sticky=(N, W), padx=5)
    #label_zchan.grid(column=0, row=25, columnspan=2, sticky=(N, W), padx=5)



    label_empty.grid(column=0, row=24, columnspan=2, sticky=(N, W), padx=5)


    frame_information.grid(column=0, row=31,columnspan=3,sticky=(N,W,E,S))

    listbox_l.grid(column=0, row=0,columnspan=3,sticky=(N,W,E,S))
    scrollbar_s.grid(column=1, row=0, sticky=(N,S))

    listbox_l['yscrollcommand'] = scrollbar_s.set

    label_sample.grid(column=0, row=2, columnspan=1, sticky=(N,W,E,S), padx=5)
    entry_sample.grid(column=0, row=3, columnspan=1, sticky=(N,W,E,S), padx=5)

    frame_information.grid_columnconfigure(0, weight=1)
    frame_information.grid_rowconfigure(0, weight=1)


    frame_buttomArea.grid(column =3, row=31,columnspan=2,sticky=(N, S, E, W))

    button_output.grid(column=0, row=0,columnspan = 2,sticky=(N, S, E, W))
    button_measure.grid(column =0, row=1, columnspan = 2,sticky=(N, S, E, W))
    button_clear.grid(column = 0, row = 3, columnspan = 1, sticky=(N, S, E, W))
    button_dir.grid(column=0, row=2,columnspan = 2,sticky=(N, S, E, W))
    button_stop.grid(column=1, row=3,columnspan = 1,sticky=(N, S, E, W))


    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    content.columnconfigure(0, weight=3)
    content.columnconfigure(1, weight=3)
    content.columnconfigure(2, weight=3)
    content.columnconfigure(3, weight=1)
    content.columnconfigure(4, weight=1)
    content.rowconfigure(1, weight=1)



if __name__ == '__main__':
    main()
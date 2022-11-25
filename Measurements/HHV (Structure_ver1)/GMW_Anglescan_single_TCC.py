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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pylab
from pylab import *
import os
import math
import numpy as np
import nidaqmx
import csv
from keithley2400_I import Keithley2400
from keithley import Keithley
import time
import multiprocessing
import threading
from datetime import datetime
from scipy.optimize import curve_fit
from GMW import GMW

root = Tk()
root.title("Single Anglescan")
# import the database containing information about angle, magnitude and applied voltage

def main():

    global average, directory, dot_size, dot_edge, maxV, scantype

    directory = os.getcwd()


    #xchan=0 #Set a default iutput x channel for field measurement
    #ychan=1
    #zchan=2

    read_me = 'This program sweeps field with a fixed magnitude for 360 degrees. Currents are supplied by Keithley2400.\
    Voltage measurements are taken by Keithley2000.'

    print(read_me)

    dot_size=10 #Set a default data dot size
    dot_edge=0.5 #Set a default data dot edge width
    maxV = 0
    scantype='xy'

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

# Measures Voltage over series of rotating in-plane field
def measureMethod( _Hin, _average, _current, _sample, _number, _angle):
    global state

    # _current: current supplied by Keithley2400
    # _sample: sample name for save file
    average=int(_average) # number of measurements averaged by Keithley2000
    num = int(_number)
    [angi, angf] = Convert(_angle) 
    state = "measure"
    ix = 550

    Hlist = Convert(_Hin)
    Curlist = Convert(_current)

    def event():

        keith=Keithley2400() #Initiate K2400
        keith2000=Keithley() #Initiate K2000
        
        clear_plot()
        
        #Prepare data entries
        global values_x, values_py, canvas, scantype, ang, angmagV

        #For field scan
        for current in Curlist:
            for Hin in Hlist:

                gmw=GMW() #Initiate GMW magnet
                recipe_list=[30,50,70,100,200,500,800,1000,1300,1500,1700,1900]
                if Hin in recipe_list:
                    angmagV = np.loadtxt('C:/Users/doc/Desktop/GUI_Harmonic_Measurement/recipe/'+str(Hin)+'.csv',delimiter=',')
                    ang=np.arange(0,363,3)
                else:

                #Initialize for every loop
                    ang, angmagV = gmw.anglescan(Hin, num, angi, angf, scantype)
                    #np.savetxt(str(Hin)+".csv",angmagV, delimiter=",")
                    ang = ang*180/np.pi
                
              
                listbox_l.insert('end',"Now measuring with Idc = %f (mA)" %(current))
                listbox_l.insert('end',"Now measuring with Hin = %f (Oe)" %(Hin))
                listbox_l.see(END)


                #Start current measurement--------------------------------------------------------------------------------------
                values_py=np.zeros(num+1)
                values_x=np.zeros(num+1)
                #Setup K2400 for current output and resistance measurement
                keith.fourWireOff()
                keith.setCurrent(current)
                keith.outputOn()

                index=1
                data=[]

                while index<=15:
                    data=data+keith.measureOnce()
                    index+=1

                listbox_l.insert('end',"Measured current: %f mA" %(1000*data[2]))
                listbox_l.insert('end',"Measured voltage: %f V" %(data[1]))
                listbox_l.insert('end',"Measured resistance: %f Ohm" %(data[1]/data[2]))
                listbox_l.see(END)

                resistance = data[1]/data[2]

                #initial application of field to avoid outliers
                gmw.writetask.write([0,0,0])
                graph_name = str(scantype)+" anglescan "+str(round(Hin,2))+"Oe "+str(round(current,2))+"mA"

                ax.set_title(graph_name)

                #Setup GMW (Hx,Hy field) output and resistance measurement
                for g in range(num+1):
                    if state == "stop":

                        gmw.zero()
                        keith.resmode()
                        keith.local()
                        root.quit()
                    

                    if state == "measure":
                        gmw.writetask.write(angmagV[g])
            
                        #sleep at start to avoid outliers
                        if g == 1:
                            time.sleep(5)

                        data=keith2000.measureMulti(average)

                        tmp=double(1000*data/current) # Voltage from K2000 / Current from K2400
                        values_py[g]+=tmp
                        values_x[g]+=ang[g]

                        if g>0:
                            ax.plot(values_x[g-1:g+1], values_py[g-1:g+1],'b-o', ms=dot_size, mew=dot_edge, alpha=0.5)
                            canvas.draw()
                        #listbox_l.insert('end', "Resistance:" + str(round(tmp,4)) + "\t \t AppliedFieldAngle:" + str(round(ang[g],4))) 
                        #listbox_l.see(END)
                        print("AppliedFieldAngle: " + str(round(ang[g],4)),end='\r')

        
                #Save data---------------------------------------------------------------------------------------------------------------
                #Setup timestamp
                stamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
                listbox_l.insert('end', str(stamp))

                file = open(str(directory)+"/"+str(_sample)+"_"+str(scantype)+"scan_"+str(Hin)+"Oe_"+str(round(current,2))+"mA_"+str(round(resistance,2))+"Ohm_"+str(stamp)+".csv", "w")
                file.write("Sample name: "+str(_sample)+"\n")
                file.write("Scan type: "+str(scantype)+" scan\n")
                file.write("Applied current: "+str(current)+"(mA)\n")
                file.write("Applied field: "+str(Hin)+"(Oe)\n\n")
                file.write("Number"+","+"AppliedFieldAngle"+","+"Resistance(Ohm)"+"\n")

                cnt=1
                #output all data
                for a in range(len(values_x)):
                    file.write(str(cnt)+","+str(values_x[a])+","+str(values_py[a])+"\n")
                    cnt +=1

                file.close()

                listbox_l.insert('end', "The Measurement data is saved.")
                listbox_l.see(END)

                clear_plot()                
                gmw.zero()
                gmw.shutdown()

        keith.fourWireOff()

        listbox_l.insert('end',"Measurement finished")
        listbox_l.see(END)
        
        keith.resmode()
        keith.local()
    


    if (double(max(Hlist)/ix))< 11:

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
    t1=threading.Thread(target= lambda : measureMethod( _Hin, _average, _current, _sample, _number, _angle), daemon=True)
    t1.start()


def scantypeMethod(val):

    global scantype

    scantype = str(val)

    listbox_l.insert('end', "scan type is switched to : "+ str(scantype)+" scan")
    listbox_l.see(END)


def dirMethod():

    global directory

    directory = filedialog.askdirectory()

    listbox_l.insert('end', directory)
    listbox_l.see(END)

def clearMethod():

    ax.clear()
    ax.grid(True)
    ax.set_title("Realtime Resistance vs Theta Plot")
    ax.set_xlabel("Applied Field Angle (Theta)")
    ax.set_ylabel("Resistance (Ohm)")

    canvas.draw()
    listbox_l.delete(0, END)

    print("clear all")

def clear_plot():

    ax.clear()
    ax.grid(True)
    ax.set_title("Realtime Resistance vs Theta Plot")
    ax.set_xlabel("Applied Field Angle (Theta)")
    ax.set_ylabel("Resistance (Ohm)")

def quitMethod():

    gmw()
    writetask.write([0, 0, 0])
    
    fdata=[0,0,0] # origin measured field is in unit V, ifield is conversion value with unit Oe/V
    findex=1
    while findex<=5: #Average of five measurements
        fdata=[fdata[i]+readtask.read()[i] for i in range(0,3)]
        findex+=1
    fielddata=[x/5 for x in fdata]

    listbox_l.insert('end', "All fields set to zero.\nMeasured field is "+str([readtask.read()]))
    listbox_l.see(END)
    writetask.close()
    readtask.close()
    time.sleep(1)

    global root

    root.quit()

def createWidgit():

    global ax, axsec, canvas, listbox_l, listbox_2, func, frame, sense

    fig = pylab.figure(1, figsize=(5,5))

    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_title("Realtime Resistance vs Theta Plot")
    ax.set_xlabel("Applied Field Angle (Theta)")
    ax.set_ylabel("Resistance (Ohm)")

    fig.tight_layout()
    c_values = np.loadtxt("C:/Users/doc/Desktop/GUI_Harmonic_Measurement/Calibration/calibrate.txt", delimiter="," ,usecols=1)
    _cX = c_values[-2]
    _cY = c_values[-1]

    content = ttk.Frame(root, padding=(3,3,12,12))

    #plotting area
    frame = ttk.Frame(content, borderwidth=0, relief="sunken",padding=(3,3,12,12))
    frame_setting = ttk.Frame(content)
    frame_information = ttk.Frame(content, padding = (3,3,12,12))
    frame_buttomArea = ttk.Frame(content)

    #Save Variables
    entry_sample = ttk.Entry(frame_information); entry_sample.insert(0, "sample_name")

    #Function Variables
    entry_Hin = ttk.Entry(frame_setting); entry_Hin.insert(0,"1000") # Hin field
    entry_average = ttk.Entry(frame_setting); entry_average.insert(0,"1") # measure time for Keithley
    entry_current = ttk.Entry(frame_setting); entry_current.insert(0,"1.5") # applied current
    entry_number = ttk.Entry(frame_setting); entry_number.insert(0,"120") # points per scan
    entry_angle = ttk.Entry(frame_setting); entry_angle.insert(0,"0/360") # points per scan


    value3 = tkinter.StringVar()

    scantype = ['xy', 'xy', 'xz', 'yz']

    option_scantype = ttk.OptionMenu(frame_setting, value3, *scantype, command = scantypeMethod)


    listbox_l = Listbox(frame_information,height=5)
    scrollbar_s = ttk.Scrollbar(frame_information, orient=VERTICAL, command=listbox_l.yview)

    #Save Labels
    label_sample = ttk.Label(frame_information, text = "Sample Name")

    #Function Labels
    label_Hin = ttk.Label(frame_setting, text="Hin field (Oe):")
    label_average = ttk.Label(frame_setting, text="Averages:")
    label_scantype = ttk.Label(frame_setting, text="Scan type:")
    label_current = ttk.Label(frame_setting, text="Current (mA):")
    label_number = ttk.Label(frame_setting, text="Points per scan:")
    label_angle =  ttk.Label(frame_setting, text="Scan angle range (degree):")
    label_empty = ttk.Label(frame_setting, text="")



    button_measure = ttk.Button(frame_buttomArea, text ="Measure", \
        command = lambda : measurethread(entry_Hin.get(),entry_average.get(),entry_current.get(),\
            entry_sample.get(),entry_number.get(),entry_angle.get()))

    button_dir  = ttk.Button(frame_buttomArea, text="Change directory", command = dirMethod)
    button_quit = ttk.Button(frame_buttomArea, text="Quit", command = quitMethod)
    button_stop = ttk.Button(frame_buttomArea, text="Stop", \
        command = stopMethod)
    button_clear = ttk.Button(frame_buttomArea, text="Clear", command = clearMethod)

    #Attatch Plot
    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.get_tk_widget().grid(row=0, column =0, pady =0, padx =0,sticky='nsew')
    content.grid(column=0, row=0, sticky=(N, S, E, W))
    frame.grid(column=0, row=0, columnspan=6, rowspan=60, sticky=(N, S, E, W))


    frame_setting.grid(column=7, row=0, columnspan=2, rowspan=30, sticky=(N, S, E, W))

    #Frame setting grid
    label_Hin.grid(column=0, row=5, columnspan=2, sticky=(N, W), padx=5)
    entry_Hin.grid(column=0, row=6, columnspan=2, sticky=(N, W), padx=5)
    label_number.grid(column=0, row=7, columnspan=2, sticky=(N, W), padx=5)
    entry_number.grid(column=0, row=8, columnspan=2, sticky=(N, W), padx=5)
    label_average.grid(column=0, row=9, columnspan=2, sticky=(N, W), padx=5)
    entry_average.grid(column=0, row=10, columnspan=2, sticky=(N, W), padx=5)
    label_scantype.grid(column=0, row=11, columnspan=2, sticky=(N, W), padx=5)
    option_scantype.grid(column=0, row=12, columnspan=2, sticky=(N, W), padx=5)
    label_angle.grid(column=0, row=13, columnspan=2, sticky=(N, W), padx=5)
    entry_angle.grid(column=0, row=14, columnspan=2, sticky=(N, W), padx=5)
    label_current.grid(column=0, row=17, columnspan=2, sticky=(N, W), padx=5)
    entry_current.grid(column=0, row=18, columnspan=2, sticky=(N, W), padx=5)
    label_empty.grid(column=0, row=19, columnspan=2, sticky=(N, W), padx=5)


    frame_information.grid(column=0, row=71,columnspan=6,sticky=(N,E,W,S))
    listbox_l.grid(column=0, row=0,columnspan=6,sticky=(N, S, E, W))
    scrollbar_s.grid(column=2, row=0, sticky=(N,S))

    listbox_l['yscrollcommand'] = scrollbar_s.set

    label_sample.grid(column=0, row=2, columnspan=2, sticky=(N,W,E,S), padx=5)
    entry_sample.grid(column=0, row=3, columnspan=2, sticky=(N,W,E,S), padx=5)

    frame_information.grid_columnconfigure(0, weight=1)
    frame_information.grid_rowconfigure(0, weight=1)
    frame_buttomArea.grid(column =7, row=71,columnspan=2,sticky=(N, S, E, W))

    label_empty3 = ttk.Label(frame_buttomArea, text="")

    button_stop.grid(column=0, row=7,columnspan = 2,sticky=(N, S, E, W))
    button_measure.grid(column =0, row=2, columnspan = 2, sticky=(N, S, E, W))
    label_empty3.grid(column=0, row=3, columnspan=2, sticky=(N, S, E, W))
    button_clear.grid(column = 0, row = 6, columnspan = 1, sticky=(N, S, E, W))
    button_dir.grid(column=0, row=5,columnspan = 2,sticky=(N, S, E, W))
    button_quit.grid(column=1, row=6,columnspan = 1,sticky=(N, S, E, W))


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
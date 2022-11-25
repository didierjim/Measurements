
#********************** 2017/01/30 Version ********************#
# Note: Threading added in the measureMethod()
# Note: The listbox will now always show the latest measured data
# Note: Threading can avoid non-responsive problem, but will also cause
#       the intereference by clicking other buttons during measurement.
# Note: Keithley current option added.
# Note: All output will be shut down by clicking quit
# Note: Create the K2400 current stepping function

#********************** 2017/03/30 Version ********************#
# Note: Modification on data plots (dots and lines)
# Note: Saving files with date and time

#********************** 2017/06/15 Version ********************#
# Note: Saving files with measured channel resistance

#********************** 2018/01/11 Version ********************#
# Note: Added comments for clarity
# Note: Cleaned up code for easier reading
# Note: Unnecessary variables removed
# Note: Amplifier protect added.
# Note: Save function updated to include sample name
# Note: Read me added
# Note: Data value changed to match multimeasure for Keithley

#********************** 2018/01/26 Version ********************#
# Note: Loop made to run from low to high
# Note: Added delay to minimize initial noise

#********************** 2018/05/18 Version ********************#
# Note: Title added
# Note: Print statements made to display in Listbox
# Note: Save function variables rounded to 2 decimals, listbox variables to 4 decimals
# Note: Updated Hx loop to allow for a negative to positive Hx values

#********************** 2020/05/22 Version ********************#
# Note: GMW VectorMagnet replace the lock-in, remove all the lock-in amp terms
# Note: New function about measuring field has been added
#       including every method and write the data into csv
# Note: Further calibration of conversion constant is required
#       output and input calibration values have different unit
# Note: No yet tested

#********************** 2020/05/26 Version ********************#
# Note: New function about measuring field has been added
#       including every method and write the data into csv

#********************** 2020/05/26 Version ********************#
# Note: the magnitude of in plane field output is about 30 mT
#       in the angle_magnitude.csv

#********************** 2020/07/16 Version *******************#
# Note: AMR recipe "angle_magnitude3-1" is used
#       Code simplified and corrected 

#********************** 2020/07/20 Version *******************#
# Note: Corrected recipe "in_out_ang.csv" according to readings of tesla meter is used
#       Calibration of conversion constant is done for X and Y axis
#       X-writing (ix)      =  136.6 Oe per unit magnitude
#       X-reading (ifieldx) =  129.2 Oe per unit magnitude
#       Y-writing (iy)      =  227.2 Oe per unit magnitude
#       Y-reading (ifieldy) =  192.7 Oe per unit magnitude
#       AMR measurement with two-probe method tested

#********************** 2020/07/24 Version *******************#
# Note: New recipe "in_out_ang_noboard.csv" according to readings of tesla meter is used
#       Calibration of conversion constant is done without plastic board
#       X-writing (ix)      =  146.9 Oe per unit magnitude
#       X-reading (ifieldx) =   78.4 Oe per unit magnitude
#       Y-writing (iy)      =  158.7 Oe per unit magnitude
#       Y-reading (ifieldy) =   88.0 Oe per unit magnitude
#       AMR measurement with four-probe method tested

#********************** 2020/07/31 Version *******************#
# Note: New recipe "in_out_ang_noboard_standing.csv" according to readings of tesla meter and standing sensor is used
#       Calibration of conversion constant is done without plastic board
#       X-writing (ix)      =  549.4 Oe per unit magnitude
#       Y-writing (iy)      =  547.3 Oe per unit magnitude
#       AMR and PHE measurement with four-probe method tested
#       Slight asymmetry should be deducted when measuring PHE

#********************** 2020/09/24 Version *******************#
# Note: Field scan and current scan functions are added,
#       also the instananeous second harmonic signal is presented  

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
import time
import multiprocessing
import threading
from datetime import datetime
from scipy.optimize import curve_fit
from GMW import GMW

root = Tk()
root.title("Two-Point Fieldscan")
# import the database containing information about angle, magnitude and applied voltage

def main():

    global result, average, directory, dot_size, dot_edge, scantype

    directory = os.getcwd()

    read_me = 'This program sweeps field with a fixed magnitude for 360 degrees. \
    Current supply amd voltage measurements are both conducted by Keithley2400.'

    print(read_me)

    dot_size=10 #Set a default data dot size
    dot_edge=0.5 #Set a default data dot edge width

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
def measureMethod( _H, _phi, _theta, _average, _current, _sample, _number):

    global state, p, t

    # _current: current supplied by Keithley2400
    # _sample: sample name for save file
    average=int(_average) # number of measurements averaged by Keithley2400
    num = int(_number)
    #p = int(_phi)
    t = int(_theta)
    
    Philist = Convert(_phi)
    Hlist = Convert(_H)
    Curlist = Convert(_current)

    state = "measure"

    def event():

        keith=Keithley2400() #Initiate K2400
        
        clear_plot()
        
        #Prepare data entries
        global values_x, values_y, canvas, msg, msgV, p, t


        for p in Philist:
	        for current in Curlist:
	            for H in Hlist:
	                p = int(p)

	                gmw=GMW() #Initiate GMW magnet

	                graph_name = "Theta"+str(t)+"Phi"+str(p)+" fieldscan "+str(round(H,2))+"Oe "+str(round(current,2))+"mA"
	                    
	                ax.set_title(graph_name)
	                print(graph_name)
	                
	                #Initialize for every loop

	                msg, msgV = gmw.SolverFieldscan(H, num, p, t)
                    #msg, msgV = gmw.SolverFieldscan(H, num, p, t)

	                
	                listbox_l.insert('end',"Now measuring with Idc = %f (mA)" %(current))
	                listbox_l.insert('end',"Now measuring with H = %f (Oe), phi = %d, theta = %d" %(H,p,t))
	                listbox_l.see(END)


	                values_y=np.zeros(4*num+1)
	                values_x=np.zeros(4*num+1)
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

	                #Setup GMW (Hx,Hy field) output and resistance measurement
	                #Field stength of original recipe is 308 Oe
	                for g in range(np.shape(msgV)[0]):
	                    if state == "stop":

	                        gmw.zero()

	                        keith.resmode()
	                        keith.local()
	                        root.quit()
	                    

	                    if state == "measure":
	                        gmw.writetask.write(msgV[g])
	            
	                        #sleep at start to avoid outliers
	                        if g < 5:
	                            time.sleep(.5)

	                        data=keith.measureOnce()

	                        tmp=double(data[1]/data[2]) # Voltage from K2400 / Current from K2400
	                        values_y[g]+=tmp
	                        values_x[g]+=msg[g]

	                        if g>0:
	                            ax.plot(values_x[g-1:g+1], values_y[g-1:g+1],'r-o', ms=dot_size, mew=dot_edge, alpha=0.5)
	                            canvas.draw()
	                        listbox_l.insert('end', "Resistance:" + str(round(tmp,4)) + "\t AppliedField:" + str(round(msg[g],4))) 
	                        
	                        listbox_l.see(END)
	                        print("AppliedField: " + str(round(msg[g],4)),end='\r')
	                print('\n')

	                #Save data---------------------------------------------------------------------------------------------------------------
	                
	                #Setup timestamp
	                stamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
	                listbox_l.insert('end', str(stamp))

	                file = open(str(directory)+"/"+str(_sample)+"_TP"+str(p)+"fieldscan_"+str(H)+"Oe_"+str(round(current,2))+"mA_"+str(round(resistance,2))+"Ohm_"+str(stamp)+".csv", "w")
	                file.write("Sample name: "+str(_sample)+"\n")
	                file.write("Phi="+str(p)+"Theta="+str(t)+")\n")
	                file.write("Applied current: "+str(current)+"(mA)\n")
	                file.write("Applied field: "+str(H)+"(Oe)\n\n")
	                file.write("Number"+","+"AppliedField"+","+"Resistance(Ohm)"+"\n")

	                cnt=1
	                #output all data
	                for a in range(len(values_x)):
	                    file.write(str(cnt)+","+str(values_x[a])+","+str(values_y[a])+"\n")
	                    cnt +=1

	                file.close()

	                listbox_l.insert('end', "The Measurement data is saved.")
	                listbox_l.see(END)

	                clear_plot()
	                gmw.zero()
	                time.sleep(2)         

        keith.fourWireOff()

        listbox_l.insert('end',"Measurement finished")
        listbox_l.see(END)
        
        keith.resmode()
        keith.local()
    


    if (double(max(Hlist)))<= 2500:

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
    

def measurethread( _H, _phi, _theta, _average, _current, _sample, _number):
    t1=threading.Thread(target= lambda : measureMethod( _H, _phi, _theta, _average, _current, _sample, _number), daemon=True)
    
    t1.start()


def dirMethod():

    global directory

    directory = filedialog.askdirectory()

    listbox_l.insert('end', directory)
    listbox_l.see(END)

def clearMethod():

    ax.clear()
    ax.grid(True)
    ax.set_title("Realtime Resistance vs H Plot")
    ax.set_xlabel("Applied Field (Oe)")
    ax.set_ylabel("Resistance (Ohm)")

    canvas.draw()
    listbox_l.delete(0, END)

    print("clear all")

def clear_plot():

    ax.clear()
    ax.grid(True)
    ax.set_title("Realtime Resistance vs H Plot")
    ax.set_xlabel("Applied Field (Oe)")
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

    global ax, axsec, canvas, listbox_l, listbox_2, result, func, frame, sense, scantype

    fig = pylab.figure(1, figsize=(4.5,4.5))

    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_title("Realtime Resistance vs H Plot")
    ax.set_xlabel("Applied Field (Oe)")
    ax.set_ylabel("Resistance (Ohm)")

    fig.tight_layout()
    #c_values = np.loadtxt("C:/Users/doc/Desktop/GUI_Harmonic_Measurement/Calibration/calibrate.txt", delimiter="," ,usecols=1)
    #_cX = c_values[-2]
    #_cY = c_values[-1]

    content = ttk.Frame(root, padding=(3,3,12,12))

    #plotting area
    frame = ttk.Frame(content, borderwidth=0, relief="sunken",padding=(3,3,12,12))
    frame_setting = ttk.Frame(content)
    frame_information = ttk.Frame(content, padding = (3,3,12,12))
    frame_information2 = ttk.Frame(content, padding = (3,3,12,12))
    frame_buttomArea = ttk.Frame(content)

    #Save Variables
    entry_sample = ttk.Entry(frame_information); entry_sample.insert(0, "sample_name")

    #Function Variables
    entry_H = ttk.Entry(frame_setting); entry_H.insert(0,"1000") # H field
    entry_average = ttk.Entry(frame_setting); entry_average.insert(0,"1") # measure time for Keithley
    entry_current = ttk.Entry(frame_setting); entry_current.insert(0,"1") # applied current
    entry_number = ttk.Entry(frame_setting); entry_number.insert(0,"20") # points per scan
    entry_phi = ttk.Entry(frame_setting); entry_phi.insert(0,"0") # X Calibration factor
    entry_theta = ttk.Entry(frame_setting); entry_theta.insert(0,"90") # Y Calibration factor


    value3 = tkinter.StringVar()


    listbox_l = Listbox(frame_information,height=5)
    scrollbar_s = ttk.Scrollbar(frame_information, orient=VERTICAL, command=listbox_l.yview)

    #Save Labels
    label_sample = ttk.Label(frame_information, text = "Sample Name")

    #Function Labels
    #label_cX =ttk.Label(frame_setting, text="X Calibration factor:") 
    #label_cY =ttk.Label(frame_setting, text="Y Calibration factor:")
    label_H = ttk.Label(frame_setting, text="H field (Oe):")
    label_average = ttk.Label(frame_setting, text="Averages:")
    label_current = ttk.Label(frame_setting, text="Current (mA):")
    label_number = ttk.Label(frame_setting, text="Points per scan:")
    label_phi =ttk.Label(frame_setting, text="IP angle (degree):") 
    label_theta =ttk.Label(frame_setting, text="OOP angle (degree):")
    label_empty = ttk.Label(frame_setting, text="")
    label_empty1 = ttk.Label(frame_setting, text="")



    button_measure = ttk.Button(frame_buttomArea, text ="Measure", \
        command = lambda : measurethread(entry_H.get(),entry_phi.get(),entry_theta.get(),entry_average.get(),entry_current.get(),\
            entry_sample.get(),entry_number.get()))

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
    label_phi.grid(column=0, row=1, columnspan=2, sticky=(N, W), padx=5)
    entry_phi.grid(column=0, row=2, columnspan=2, sticky=(N, W), padx=5)
    label_theta.grid(column=0, row=3, columnspan=2, sticky=(N, W), padx=5)
    entry_theta.grid(column=0, row=4, columnspan=2, sticky=(N, W), padx=5)
    label_H.grid(column=0, row=5, columnspan=2, sticky=(N, W), padx=5)
    entry_H.grid(column=0, row=6, columnspan=2, sticky=(N, W), padx=5)

    
    label_current.grid(column=0, row=9, columnspan=2, sticky=(N, W), padx=5)
    entry_current.grid(column=0, row=10, columnspan=2, sticky=(N, W), padx=5)
    label_empty1.grid(column=0, row=11, columnspan=2, sticky=(N, W), padx=5)
    label_number.grid(column=0, row=12, columnspan=2, sticky=(N, W), padx=5)
    entry_number.grid(column=0, row=13, columnspan=2, sticky=(N, W), padx=5)
    #label_average.grid(column=0, row=14, columnspan=2, sticky=(N, W), padx=5)
    #entry_average.grid(column=0, row=15, columnspan=2, sticky=(N, W), padx=5)
    
    
    #label_cX.grid(column=0, row=16, columnspan=2, sticky=(N, W), padx=5)
    #entry_cX.grid(column=0, row=17, columnspan=2, sticky=(N, W), padx=5)
    #label_cY.grid(column=0, row=18, columnspan=2, sticky=(N, W), padx=5)
    #entry_cY.grid(column=0, row=19, columnspan=2, sticky=(N, W), padx=5)
    label_empty.grid(column=0, row=20, columnspan=2, sticky=(N, W), padx=5)


    frame_information.grid(column=0, row=71,columnspan=6,sticky=(N,E,W,S))

    listbox_l.grid(column=0, row=0,columnspan=6,sticky=(N, S, E, W))
    scrollbar_s.grid(column=2, row=0, sticky=(N,S))


    listbox_l['yscrollcommand'] = scrollbar_s.set

    label_sample.grid(column=0, row=2, columnspan=2, sticky=(N,W,E,S), padx=5)
    entry_sample.grid(column=0, row=3, columnspan=2, sticky=(N,W,E,S), padx=5)

    frame_information.grid_columnconfigure(0, weight=1)
    frame_information.grid_rowconfigure(0, weight=1)



    frame_buttomArea.grid(column =7, row=71,columnspan=2, rowspan =10,sticky=(N, S, E, W))
    label_empty3 = ttk.Label(frame_buttomArea, text="")

    button_stop.grid(column=0, row=6,columnspan = 2,sticky=(N, S, E, W))
    button_measure.grid(column =0, row=2, columnspan = 2, sticky=(N, S, E, W))
    label_empty3.grid(column=0, row=3, columnspan=2, sticky=(N, S, E, W))
    button_clear.grid(column = 0, row = 5, columnspan = 1, sticky=(N, S, E, W))
    button_dir.grid(column=0, row=4,columnspan = 2,sticky=(N, S, E, W))
    button_quit.grid(column=1, row=5,columnspan = 1,sticky=(N, S, E, W))


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
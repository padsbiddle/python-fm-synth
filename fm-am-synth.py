# Script Name: fm-am-synth.py
# Author: Padraig Daly
# Description: AM/FM Synthesizer with Visualization and Audio Output


import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import sounddevice as sd
from scipy import signal

# || --  wave generation global variables -- ||
sr = 44100 # setting the sample rate globally
a = 1  # amplitude
fs = sr  # sampling frequency
ts = 1 / fs
duration = 1.0  # time in seconds
n = np.arange(0, fs * duration)

# || --  GUI dimensions global variables -- ||
cb_width = 20 # combobox width
cb_height = 10 # combobox height
cb_pady = 5 # combobox pady
fs_length = 200 # slider length
btn_width = 10 # button width
btn_pady = 2 # button pady
fr_pad = 5 # frame padding (grey box)

def gen_wave(f,w):

# generates the basic waveforms
    if w =="Sine":
        waveform = a * np.sin(2 * np.pi * f * n * ts)
    elif w == "Square":
        waveform = a * signal.square(2 * np.pi * f * n * ts)
    elif w == "Sawtooth":
        waveform = a * signal.sawtooth(2 * np.pi * f * n * ts)
    else:
        waveform = np.zeros_like(n)

    return waveform

def gen_result(fc, wc, fm, wm, k, mode):

# uses the basic waveform generator function to first generate the basic waveforms
    c = gen_wave(fc,wc) # generating the carrier wave
    m = gen_wave(fm,wm) # generating the modulator wave

    # c = normalise(c) # normalising the carrier waveform
    # m = normalise(m) # normalising the modulator waveform

    if mode == "Superimpose":
        y = c + m # a superimpose of the carrier and modulator waveforms
    elif mode == "AM":
        y = c * (a + k * m) # amplitude modulation of the carrier wave using the modulator wave
    elif mode == "FM":
        ts = 1/sr
        n = np.arange(0, fs * duration)
        # y = a * np.sin((2 * np.pi * fs * n * ts) + (k * m)) # this is a direct translation of the brief equation - does not seem to produce FM synthesis
        y = a * np.sin((2 * np.pi * fc * n * ts) + (k * np.cumsum(m))) # frequency modulation of the carrier wave using the modulator wave - np.cumcum = cummulative sum of m
        # replacing (k * m) with (k * np.cumsum(m))
    else:
        y = c # if any errors then the carrier is returned as default

    return normalise(y) # outputs the modulated result after normalising


def create_gui():
    #Builds the base GUI
    root = tk.Tk() # base GUI from Tkinter
    root.title("AM/FM Synthesizer with Superimpose") # GUI title bar
    root.geometry("1400x620") # GUI box dimensions, adjusted to fit the controls and frame without needing to resize

    left_frame = ttk.Frame(root,padding=10) # places a frame in the left side of the GUI
    left_frame.grid(row=0,column=0) # puts that frame in the left column

    right_frame = ttk.Frame(root,padding=10) # places a frame in the right side of the GUI
    right_frame.grid(row=0,column=1) # puts that frame in the right column

    return root,left_frame,right_frame # returns the GUI for use by other parts of the program

def draw_plot(right_frame):
    # builds the static plot on the GUI
    fig,ax = plt.subplots(figsize=(11,6))
    canvas = FigureCanvasTkAgg(fig, master =right_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=0,column=0)
    ax.set_title("Waveform")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.grid(True)
    fig.tight_layout()
    canvas.draw()

    return fig,ax,canvas

def update_plot(carrier_freq_var,carrier_wave_type_var, mod_freq_var, mod_wave_type_var, ax,canvas):
# updates the already created plot GUI based on changing widgets
    cf = carrier_freq_var.get()  # get the value from the slider
    cw = carrier_wave_type_var.get()  # get the value from the combo box
    mf = mod_freq_var.get()  # get the value from the slider
    mw = mod_wave_type_var.get()  # get the value from the combo box
    k = mod_index_var.get()  # get the value from the slider
    mode = mod_type_var.get()  # get the value from the combo box

    y_c = gen_wave(cf,cw) # generating the carrier wave
    y_m = gen_wave(mf,mw) # generating the modulator wave
    y_r = gen_result(cf, cw, mf, mw, k, mode) # generating the result wave

    t= np.arange(0,0.02,1/sr) # t now contains 882 values

    y_c = y_c[:len(t)] # before this, y_c has 44100 samples. [:len(t)] cuts y_c to the length of t (882 samples)
    y_m = y_m[:len(t)] # it selects all values in y_c up to the length of t and overwrites y_c with those values
    y_r = y_r[:len(t)] # if the length is not cut there is a sample rate missmatch and the code breaks

    ax.clear()
    ax.plot(t,y_c,color="blue", label="Carrier") # plots the carrier wave on the graph
    ax.plot(t,y_m,color="green", label="Modulator") # plots the modulator wave on the graph
    ax.plot(t,y_r, color="red", label="Result") # plots the result wave on the graph
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title(f"Mode = {mode} || Carrier = {cw} Wave - {cf:.1f} Hz || Mod = {mw} Wave - {mf:.1f} Hz || Mod Index = {k:.1f}") # .1f restricts to 1 decimal place
    #ax.set_title(f"{mw} Wave - {mf:.1f} Hz") # an attempt to have the plot title update when the modulator signal is adjusted [not working]
    ax.grid(True)
    ax.figure.tight_layout()
    ax.legend(loc="upper right") # adds a legend and locks it in place in the upper right corner
    canvas.draw()


# || -- Playback -- ||

def normalise(y):
    return y * 0.5 # scales the signal down by half to prevent clipping

def play_carrier(carrier_freq_var, carrier_wave_type_var):
    cf = carrier_freq_var.get() # get the value from the carrier frequency slider
    cw = carrier_wave_type_var.get() # get the value from the carrier wavetype combo box

    y = gen_wave(cf,cw) # calls function and passes values, results wave stored in y
    y = normalise(y) # calls function and passes values, results wave overwrites y

    sd.play(y, sr) # calls sound device, produces audio

def play_modulator(mod_freq_var, mod_wave_type_var):
    mf = mod_freq_var.get()  # same processing as play_carrier
    mw = mod_wave_type_var.get()

    y = gen_wave(mf, mw)
    y = normalise(y)

    sd.play(y, sr)

def play_result(carrier_freq_var, carrier_wave_type_var, mod_freq_var, mod_wave_type_var, mod_index_var, mod_type_var):
    cf = carrier_freq_var.get() # get the value from the slider
    cw = carrier_wave_type_var.get() # get the value from the combo box
    mf = mod_freq_var.get()  # get the value from the slider
    mw = mod_wave_type_var.get()  # get the value from the combo box
    k = mod_index_var.get() # get the value from the slider
    mode = mod_type_var.get() # get the value from the combo box

    y = gen_result(cf, cw, mf, mw, k, mode) # same processing as play_carrier, calling a different function

    sd.play(y, sr)

def create_controls(left_frame, carrier_freq_var, carrier_wave_type_var, mod_freq_var, mod_wave_type_var, ax, canvas):


    # builds the user controls in the left panel - in the brackets above - this is what the function is receiving
    # left_frame → where the controls are placed
    # carrier_freq_var → stores the frequency value
    # carrier_wave_type_var → stores waveform type
    # mod_freq_var → stores the frequency value
    # mod_wave_type_var → stores waveform type
    # ax, canvas → used to update the plot


# || --------------------------------------------------||
# ||    Carrier signal: slider / combo box / button    ||
# || --------------------------------------------------||


# || -- Grey box with title for carrier signal section -- ||
    carrier_signal_frame = ttk.LabelFrame(
        left_frame,
        text="Carrier Signal",
        padding=fr_pad # global variable
    )
    carrier_signal_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    ttk.Label(
        carrier_signal_frame,
        textvariable=carrier_freq_label_var # takes it's text value from the tkinter variable being set in the carrier frequency slider command line
    ).grid(row=0,column=0,pady=(0,0)) # label for the slider
    # pady is padding on the y axis. Values are in pixels (above and below)
    # .grid() makes it visible, places it visually on the left frame

# || -- Carrier Frequency Slider -- ||

    carrier_freq_slider = ttk.Scale(  # creates the slider stored in a variable
        carrier_signal_frame, # places the slider in the left frame
        from_=50,
        to =2000, # slider range
        variable =carrier_freq_var, # links the slider to the carrier_freq_var variable,
        # moving the slider updates carrier_freq_var
        # reading carrier_freq_var.get() gives the current slider value
        orient ="horizontal",
        length =fs_length,
        command =lambda val: (carrier_freq_label_var.set(f"Frequency {float(val):.1f} Hz"),
                             update_plot(carrier_freq_var,carrier_wave_type_var, mod_freq_var, mod_wave_type_var, ax, canvas)) # Whenever the slider
        # moves Tkinter sets the label variable with the above text plus the slider value and also calls update_plot() to pass the slider value
    )
    carrier_freq_slider.grid(row=1,column=0) # Places the slider below the label. ROW 2


# || -- Carrier Frequency Combobox -- ||
    ttk.Label(carrier_signal_frame,text="Waveform").grid(row=2,column=0,pady=(0,0)) # label for the waveform selection

    combo = ttk.Combobox( # Creates a dropdown menu:
        carrier_signal_frame,
        textvariable=carrier_wave_type_var, # Value stored in carrier_wave_type_var - needed for update_plot and playback
        state="readonly", # readonly prevents free typing
        width=cb_width,
        height=cb_height,

    )
    combo['values'] = ("Sine","Square","Sawtooth") # adds values to the combo box
    combo.current(0) # sets sine as default when the program opens (position 0)
    combo.grid(row=3,column=0, pady=cb_pady)

    combo.bind("<<ComboboxSelected>>",lambda e: update_plot(carrier_freq_var,carrier_wave_type_var, mod_freq_var, mod_wave_type_var, ax, canvas)) # update_plot() is called
    # When the user selects a new waveform: The event triggers

    button = ttk.Button(
        carrier_signal_frame,
        text="Play Carrier",
        width=btn_width, # global variable
        command=lambda: play_carrier(carrier_freq_var,carrier_wave_type_var) # button command calls the play_carrier function
    )
    button.grid(row=4, column=0, pady=btn_pady)



# || -------------------------------------------------------------||
# ||    Modulator signal: slider / slider / combo box / button    ||
# || -------------------------------------------------------------||

# Grey box with title for modulator signal section
    modulator_signal_frame = ttk.LabelFrame(
        left_frame,
        text="Modulator Signal",
        padding=fr_pad
    ) # similar processes described already
    modulator_signal_frame.grid(row=1, column=0, padx=10, pady=10, sticky="w")

# || -- Modulator frequency slider -- ||

    ttk.Label(modulator_signal_frame,
              textvariable=mod_freq_label_var,
    ).grid(row=4,column=0,pady=(0,0)) # label for the slider ROW 1
    # pady is padding on the y axis. Values are in pixels (above and below)
    # .grid() makes it visible, places it visually on the left frame

    modulator_freq_slider = ttk.Scale(  # creates the slider stored in a variable
            modulator_signal_frame, # places the slider in the left frame
            from_=1,
            to =2000, # slider range
            variable=mod_freq_var,  # links the slider to the carrier_freq_var variable,
            # moving the slider updates carrier_freq_var
            # reading carrier_freq_var.get() gives the current slider value
            orient="horizontal",
            length=fs_length,
            command=lambda val: (mod_freq_label_var.set(f"Frequency {float(val):.1f} Hz"),
                                 update_plot(carrier_freq_var,carrier_wave_type_var, mod_freq_var, mod_wave_type_var, ax, canvas))
            ) # similar processes described already
    modulator_freq_slider.grid(row=5,column=0) # Places the slider below the label. ROW 2

# || -- Modulation Index slider -- ||

    ttk.Label(
        modulator_signal_frame,
        textvariable=mod_index_label_var
    ).grid(row=6,column=0,pady=(0,0)) # label for the slider
    # pady is padding on the y axis. Values are in pixels (above and below)
    # .grid() makes it visible, places it visually on the left frame

    modulator_index_slider = ttk.Scale(  # creates the slider stored in a variable
            modulator_signal_frame, # places the slider in the left frame
            from_=0,
            to=1, # slider range
            variable=mod_index_var,
            orient="horizontal",
            length=fs_length,
            command=lambda val: (mod_index_label_var.set(f"Modulation Index {float(val):.1f}"),
                             update_plot(carrier_freq_var, carrier_wave_type_var, mod_freq_var, mod_wave_type_var, ax,
                                         canvas))
    ) # similar processes described already
    modulator_index_slider.grid(row=7,column=0) # Places the slider below the label. ROW 2

# || -- Modulation Waveform Combobox -- ||

    ttk.Label(modulator_signal_frame,text="Waveform").grid(row=8,column=0,pady=(0,0)) # label for the mod waveform selection

    combo = ttk.Combobox(  # Creates a dropdown menu:
        modulator_signal_frame,
        textvariable=mod_wave_type_var,
        state="readonly",  # readonly prevents free typing
        width=cb_width,
        height=cb_height,
    )
    combo['values'] = ("Sine","Square","Sawtooth")  # adds values to the combo box
    combo.current(0)  # sets Sine as default when the program opens
    combo.grid(row=9, column=0, pady=cb_pady)

    combo.bind("<<ComboboxSelected>>",lambda e: update_plot(carrier_freq_var,carrier_wave_type_var, mod_freq_var,mod_wave_type_var, ax, canvas)) # update_plot() is called
    # When the user selects a new waveform from the dropdown menu, the event triggers - a similar process to the slider command line


# || -- Modulation Waveform play button -- ||

    button = ttk.Button(
        modulator_signal_frame,
        text="Play Modulator",
        width=btn_width,
        command=lambda: play_modulator(mod_freq_var,mod_wave_type_var)
    ) # similar processes described already
    button.grid(row=10, column=0, pady=btn_pady)



# || -------------------------------------------------------||
# ||           Result signal: combo box / button            ||
# || -------------------------------------------------------||


# Grey box with title for result signal section
    result_signal_frame = ttk.LabelFrame(
        left_frame,
        text="Modulated / Result Signal",
        padding=fr_pad,
    )
    result_signal_frame.grid(row=2, column=0, padx=10, pady=10, sticky="w")

# || -- Modulation Type Combobox -- ||

    ttk.Label(result_signal_frame,text="Modulation Type").grid(row=2,column=0,pady=(0,0)) # label for the mod type

    combo = ttk.Combobox(  # Creates a dropdown menu:
        result_signal_frame,
        textvariable=mod_type_var,
        state="readonly",  # readonly prevents free typing
        width=cb_width,
        height=cb_height,

    )
    combo['values'] = ("AM", "FM", "Superimpose")  # adds values to the combo box
    combo.set("AM")  # sets AM as default when the program opens - a different way to achieve the same thing as combo.current(0)
    combo.grid(row=10, column=0, pady=cb_pady)

    combo.bind("<<ComboboxSelected>>", lambda e: update_plot(carrier_freq_var,carrier_wave_type_var, mod_freq_var,mod_wave_type_var, ax, canvas))  # update_plot() is called
    # When the user selects a new waveform: The event triggers

    # || -- Modulation Waveform Combobox -- ||

    button = ttk.Button(
        result_signal_frame,
        text="Play Result",
        width=btn_width,
        command=lambda: play_result(carrier_freq_var, carrier_wave_type_var, mod_freq_var, mod_wave_type_var, mod_index_var, mod_type_var)
    ) # similar processes already described
    button.grid(row=11, column=0, pady=btn_pady)

# || -------------------------------------------------------||
# || ---------------------- Main ---------------------------||
# || -------------------------------------------------------||

if __name__ == "__main__":
    root,left_frame,right_frame = create_gui() # calls the create GUI function which returns 3 values and stores them in variables
    carrier_freq_label_var = tk.StringVar(value="Frequency 1700.0 Hz")  #
    carrier_freq_var = tk.DoubleVar(value=1700.0) # auto updating tkinter variable, stored in "carrier_freq_var" - updates everytime slider moves
    carrier_wave_type_var = tk.StringVar(value= "Sine") # same as above updates when the combobox is changed.
    mod_freq_label_var = tk.StringVar(value="Frequency 140.0 Hz")  #
    mod_freq_var = tk.DoubleVar(value=140.0) # tkinter var for modulator freq slider
    mod_index_label_var = tk.StringVar(value="Modulation Index 0.6")  #
    mod_index_var = tk.DoubleVar(value=0.6) # tkinter var for modulation index slider
    mod_wave_type_var = tk.StringVar(value= "Sine") # tkinter var for modulator waveform combobox
    mod_type_var = tk.StringVar(value="AM") # tkinter var for modulation type combobox

# || --  get value global variables -- ||

    # creates the basic plot
    fig,ax,canvas = draw_plot(right_frame)
    # calls update to populate the plot with the default values - without this step the plot is blank when the program opens
    update_plot(carrier_freq_var, carrier_wave_type_var, mod_freq_var, mod_wave_type_var, ax, canvas
    )
    #controls
    create_controls(left_frame,carrier_freq_var, carrier_wave_type_var, mod_freq_var, mod_wave_type_var, ax, canvas)
    root.mainloop()





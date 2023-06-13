'''
A GUI for controlling registers
'''
import readline
import sys
sys.path.insert(0, '../')
import version
__author__= "Pontus Brink"
__version__ = version.version_num

import sys
import os
sys.path.append('.')

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import tkinter.font as tkFont
except:
    import tkFont as tkfont

try:
    import tkinter.filedialog as tkFileDialog
except:
    import tkFileDialog

try:
    import tkinter.ttk as ttk
except:
    import ttk

from shutil import copyfile
from Chip import Chip
from threading import Thread
import controller
import terminalWindow
import FuncThread as FT
import graphplot
import ThreadHandler as TH
currentRxChip = 'RxChip.txt'
currentTxChip =  'TxChip.txt'
import time
import Variables as var
import RxTxView as rt
import Page as p
import GuiCmdHist
import RegisterWindow
import BeambookView
import datetime

import recovery_logger


serial_number = ''
board_type = ''
rfm_type = ''

INITIAL_POLL_DELAY  = 800
LONG_POLL_DELAY     = 1100 #1600
SHORT_POLL_DELAY    = 700 #1000
TERMINAL_POLL_DELAY = 200

# This class controls the entire program.
class MainView(tk.Frame):
    def __init__(self, root,RxChip, TxChip, fref, esd_recovery, *args, **kwargs):
        tk.Frame.__init__(self,*args,**kwargs)

        self.root = root
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.TH = TH.ThreadHandler()
        self.queueThread = FT.FuncThread(lambda:self.TH.start())
        self.queueThread.start()
        self.quit = False
        self.module_error = False

        # Add menubar, this is the controls of the top that are general for every chip. Controls which chip to use and so on.
        self.menubar = tk.Menu(root)

        config_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=config_menu)
        LoadFile = lambda: self.loadGainSettings()
        SaveFile = lambda: self.saveRegisterSettings()
        config_menu.add_command(label="Load TX and RX gain setting", command=LoadFile)
        config_menu.add_command(label="Save register setting", command=SaveFile)

        menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=menu)
        switcherRx = lambda: PictureShower(newWindow(self,"Block Diagram"),var._RXBLOCKDIAGRAM, background="orange")
        switcherTx = lambda: PictureShower(newWindow(self,"Block Diagram"),var._TXBLOCKDIAGRAM, background="orange")
        menu.add_command(label="Show Rx Block Diagram", command=switcherRx)
        menu.add_command(label="Show Tx Block Diagram", command=switcherTx)

        self.master.config(menu=self.menubar)

        self.root.title("TRX-BF01 EVK    ")

        global serial_number
        if serial_number == None:
            try:
                import mb1
                devlist = mb1.listdevs()
            except:
                devlist = None

            rfm_type_list = ['BFM06010', 'BFM06009', 'BFM06005', 'BFM06012', 'BFM06015', 'BFM06016']
            d = ConnectDialog(root, devlist, rfm_type_list)
            root.wait_window(d.top)
            if (serial_number == None) or (serial_number == ''):
                self.close()

        if serial_number != None:
            self.root.title("TRX-BF01 EVK    " + serial_number)
        else:
            self.root.title("TRX-BF01 EVK    ")

        self.rxController = controller.Controller(RxChip, TxChip, self, board_type, serial_number, "RX", rfm_type.upper(), fref, esd_recovery)
        self.chipsConnected = self.rxController.eder.check()

        # Tx Rx notebook
        self.nb = ttk.Notebook(root)
        RxPage = p.Page(self.nb)
        self.RxView = rt.RxTxView(RxPage, self.rxController, self.TH, "RX")

        self.nb.add(RxPage, text="RX")
        TxPage = p.Page(self.nb)
        self.TxView = rt.RxTxView(TxPage, self.rxController, self.TH, "TX")
        self.nb.add(TxPage, text="TX")

        self.TxView.setMainView(self)
        self.RxView.setMainView(self)

        BeambookPage = p.Page(self.nb)
        self.BeambookView = BeambookView.BeambookView(BeambookPage, self.rxController, self.TH)
        self.nb.add(BeambookPage, text="Beambook   ")

        self.cmdhist = GuiCmdHist.GuiCmdHist()
        #TerminalWindow
        terminalPage = p.Page(root)
        text = tk.Text(terminalPage)
        text.configure(height=50)
        self.terminal = terminalWindow.Std_redirector(text, self.TH)

        # Terminal input.
        self.ederInput = tk.StringVar()
        inputFrame = tk.Frame(terminalPage)
        self.CommandCombobox = ttk.Combobox(inputFrame, textvariable=self.ederInput)
        self.ederInput.set("eder.")
        self.CommandCombobox.configure(values=self.cmdhist.load_cmd_history())
        self.CommandCombobox.bind('<Return>', self.enterKeyPressed)
        self.CommandCombobox.bind('<Up>', self.upKeyPressed)

        regwinFrame = tk.Frame(terminalPage)
        self.regwin = RegisterWindow.RegisterWindow(regwinFrame, self.rxController.eder)

        sendCommandButton = tk.Button(inputFrame, text="Run", width=10, command=lambda :self.TH.put(lambda:self.runEder()))
        clearButton = tk.Button(inputFrame, text="Clear", width=10, command=lambda :self.TH.put(lambda:self.clearWindow()))

        self.CommandCombobox.pack(side="left", fill="both", expand="true")
        clearButton.pack(side="right")
        sendCommandButton.pack(side="right")
        inputFrame.pack(side="bottom", fill="x")
        regwinFrame.pack(side="right", fill="y")
        text.pack(side="bottom", fill="both", expand="true")

        self.rxController.eder.logger.log_info = lambda string, indent=0: self.terminal.log_info(string, indent)
        self.rxController.eder.logger.log_warning = lambda string, indent=0: self.terminal.log_info(string, indent)
        self.rxController.eder.logger.log_error = lambda string, indent=0: self.terminal.log_info(string, indent)

        sys.stderr = self.terminal
        sys.stdout = self.terminal

        # Siversima logo
        self.logoPage = p.Page(root, background=var._BACKGROUND)
        verLabel = tk.Label(self.logoPage, fg='white', text="v" + str(__version__), background=var._BACKGROUND)
        verLabel.pack(side="right", anchor="ne")
        logo = PictureShower(self.logoPage,"SiversLogo.gif")

        # Graph plotter.
        self.grapher = graphplot.PlotFrame(root, self.rxController, self.rxController, self.TH)

        # Pack it up.
        self.logoPage.pack(side="top", fill="x", anchor="n")
        self.grapher.pack(side="bottom", fill="both", expand=True)
        self.nb.pack(side="top",fill="both", expand=True)

        terminalPage.pack(side="top", fill="both", expand="true")

        self.grapher.startPlotThread()
        root.after(INITIAL_POLL_DELAY, self.PollStarter)
        root.after(INITIAL_POLL_DELAY + 100, self.guiUpdateTrigger)
        root.after(INITIAL_POLL_DELAY + 200, self.termUpdateTrigger)

    def guiUpdateTrigger(self):
        self.RxView.buttonBar.UpdateGuiTxRx()
        self.TxView.buttonBar.UpdateGuiTxRx()
        root.after(SHORT_POLL_DELAY, self.guiUpdateTrigger)

    def termUpdateTrigger(self):
        self.terminal.update()
        root.after(TERMINAL_POLL_DELAY, self.termUpdateTrigger)

    def poll(self):
        if self.RxView.isBusy():
            return
        if self.group == 'RX':
            if self.RxView.configPage.pollVar.get():
                self.RxView.controller.getRegisterValues(self.RxView)
        elif self.group == 'TX':
            if self.TxView.configPage.pollVar.get():
                self.TxView.controller.getRegisterValues(self.TxView)
        else:
            #print ('!!')
            #print (self.group)
            pass

        self.regwin.poll()
        if self.checkModuleError():
            self.module_error = True
            print ('Module Failure!')
            self.RxView.controller.eder.rpi.reset(2)
        else:
            if self.module_error:
                print ('Attempting failure recovery ...')
                print ('Please wait ...')
                self.module_error = False
                time.sleep(9)
                self.TxView.buttonBar.recover_state()

    def viewUpdater(self):
        try:
            group = self.nb.tab(self.nb.select(), "text")
        except:
            root.after(LONG_POLL_DELAY, self.PollStarter)
            return
        if group == 'RX':
            if self.RxView.configPage.pollVar.get():
                self.RxView.controller.updateRegisters(self.RxView)
        elif group == 'TX':
            if self.TxView.configPage.pollVar.get():
                self.TxView.controller.updateRegisters(self.TxView)

        self.regwin.updateView()

    def checkModuleError(self):
        if esd_recovery == 'disable':
            return False
        chip_id = self.RxView.controller.eder.regs.rd('chip_id')
        if (chip_id != 0x02741812) and (chip_id != 0x02731803):
            return True
        else:
            if self.module_error:
                return False
        current_state = self.RxView.controller.eder.status.get_mode_chip()
        if current_state == 0:
            with open(recovery_logger.recovery_file, 'r') as rec_log:
                log_text = rec_log.readlines()
            for line in log_text:
                if line.startswith('txSetup') or line.startswith('rxSetup') :
                    return True

        if ((current_state == 2) or (current_state == 3)) and (self.RxView.controller.eder.regs.rd('vco_en') == 0):
            return True

        return False


    def backupRegs(self):
        self.TH.put(lambda : self.saveRegisterSettings(recovery_backup=True))

    def run_func_in_thread(self, func):
        root.after(SHORT_POLL_DELAY, func)

    def PollStarter(self):
        if self.RxView.isBusy():
            root.after(LONG_POLL_DELAY, self.PollStarter)
            return
        try:
            self.group = self.nb.tab(self.nb.select(), "text")
        except:
            print ('*****!!!!!*****')
            root.after(LONG_POLL_DELAY, self.PollStarter)
            return
        if self.group == 'RX':
            if self.RxView.configPage.pollVar.get():
                self.RxView.controller.updateRegisters(self.RxView)
        elif self.group == 'TX':
            if self.TxView.configPage.pollVar.get():
                self.TxView.controller.updateRegisters(self.TxView)

        self.regwin.updateView()

        self.TH.put(lambda:self.poll())
        root.after(LONG_POLL_DELAY, self.PollStarter)

    def enterKeyPressed(self, event):
        self.TH.put(lambda:self.runEder())

    def upKeyPressed(self, event):
        try:
            self.CommandCombobox.current(self.CommandCombobox.current() + 1)
        except:
            pass

    def loadGainSettings(self):
        filename = tkFileDialog.askopenfilename(initialdir = "../config",title = "Select file",filetypes = (("json files","*.json"),("all files","*.*")))
        if filename != '':
            self.rxController.eder.loadGainSettings(filename)

    def saveRegisterSettings(self, recovery_backup=False):
        if not recovery_backup:
            filename = tkFileDialog.asksaveasfilename(initialdir = "../config",title = "Select file",defaultextension=".json",filetypes = (("json files","*.json"),("all files","*.*")))
            if filename != '':
                self.rxController.eder.saveRegisterSettings(filename)
        else:
            self.rxController.eder.saveRegisterSettings('recovery.json')

    def runEder(self):
        code = self.ederInput.get()
        sys.stdout = self.terminal
        #sys.stderr = self.terminal
        self.CommandCombobox.configure(values=self.cmdhist.add_to_cmd_history(code))
        self.rxController.runPythonCode(code)
        self.CommandCombobox.current(0)

    def clearWindow(self):
        self.terminal.clear()

    def close(self):
        readline.write_history_file('eder.cmd')
        try:
            self.cmdhist.save_cmd_history()
        except:
            pass

        try:
            self.grapher.close()
        except:
            pass
        try:
            self.nb.destroy()
        except:
            pass
        self.TH.stop()
        self.queueThread.join()
        #
        self.menubar.destroy()
        self.root.quit()
        self.master.destroy()
        exit(0)

    def setMainViewTitle(self, titleAddition=None):
        if serial_number != None:
            if titleAddition == None:
                self.root.title("TRX-BF01 EVK    " + serial_number)
            else:
                self.root.title("TRX-BF01 EVK    " + serial_number + titleAddition)
        else:
            if titleAddition == None:
                self.root.title("TRX-BF01 EVK    ")
            else:
                self.root.title("TRX-BF01 EVK    " + titleAddition)

def newWindow(parent, title):
    newWindow = tk.Toplevel(parent)
    newWindow.wm_title(title)
    return newWindow

class ConnectDialog:
    def __init__(self, parent, dev_list, rfm_type_list):
        self.ser_num = tk.StringVar()
        self.rfm_type = tk.StringVar()
        self.top = tk.Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.title('EVK Selector')
        try:
            self.top.iconbitmap('sivers.ico')
        except:
            pass
        window_width = parent.winfo_width()
        self.top.geometry('+%d+%d' % (window_width/2-70, 300))
        tk.Label(self.top, text='Device').pack()
        self.top.bind("<Return>", self.connect)

        self.SerNumCombobox = ttk.Combobox(self.top)
        self.SerNumCombobox.configure(values=dev_list)
        self.SerNumCombobox.configure(textvariable=self.ser_num)
        self.SerNumCombobox.configure(takefocus="")
        if dev_list != None:
            if len(dev_list) > 0:
                self.SerNumCombobox.current(0)
        self.SerNumCombobox.pack(padx=15)

        self.RfmTypeCombobox = ttk.Combobox(self.top)
        self.RfmTypeCombobox.configure(values=rfm_type_list)
        self.RfmTypeCombobox.configure(textvariable=self.rfm_type)
        self.RfmTypeCombobox.configure(takefocus="")
        if rfm_type_list != None:
            if len(rfm_type_list) > 0:
                self.RfmTypeCombobox.current(0)
        self.RfmTypeCombobox.pack(padx=15)

        b = tk.Button(self.top, text="Connect", command=self.connect)
        b.pack(pady=5)

    def connect(self, event=None):
        global serial_number
        serial_number = self.ser_num.get()
        if serial_number != None:
            recovery_logger.create_recovery_log(serial_number+'_recovery.log')
        global rfm_type
        rfm_type = self.rfm_type.get()
        self.top.destroy()

class PictureShower(p.Page):
    def __init__(self, parent, photoLocation, *args, **kwargs):
        p.Page.__init__(self,parent,*args,**kwargs)
        # Picture
        photo = tk.PhotoImage(file=photoLocation)
        self.label = tk.Label(parent, bd=0, image=photo, *args, **kwargs)
        self.label.photo=photo
        self.label.pack(side='left')


def getPrevChip():
    if os.path.isfile(currentRxChip):
        RxChip =  Chip(currentRxChip)
        if os.path.isfile(currentTxChip):
            TxChip = Chip(currentTxChip)
        else:
            raise Exception('Missing file TxChip.txt')
    else:
        raise Exception('Missing file RxChip.txt')
    return RxChip, TxChip

def startApp(root, RxChip, TxChip, fref, esd_recovery):
    app=MainView(root, RxChip, TxChip, fref, esd_recovery)
    app.pack(side="top", fill="both", expand=True)
    app.mainloop()

def get_args():
    import argparse
    parser = argparse.ArgumentParser(description='Command line options.')
    parser.add_argument('--board', '-b', dest='board_type', choices=['MB0', 'MB1'], default='MB1',
                         help='Specify type of motherboard')
    parser.add_argument('--unit', '-u', dest='unit_name', metavar='UNIT', default=None,
                         help='Specify unit name')
    parser.add_argument('-f', '--fref', dest='ref_freq', metavar='<freq>', default=None,
                         help='Specify reference clock frequency <freq>')
    parser.add_argument('-r', '--rfm', dest='rfm_type', choices=['BFM06005', 'BFM06009', 'BFM06010', 'BFM06012', 'BFM06015', 'BFM06016'], default='BFM06010',
                         help='Specify type of RFM')
    parser.add_argument('-e', '--esd', dest='esd_recovery', choices=['disable','enable'], default='disable',
                         help='enable to recover system state after system failure')

    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    try:
        fref = float(args.ref_freq)
    except:
        fref = None
    board_type = args.board_type
    serial_number = args.unit_name
    esd_recovery = args.esd_recovery

    if serial_number != None:
        recovery_logger.create_recovery_log(serial_number+'_recovery.log')
    rfm_type = args.rfm_type.upper()
    RxChip, TxChip = getPrevChip()
    root = tk.Tk()
    try:
        root.iconbitmap('sivers.ico')
    except:
        pass

    w = 1300 # width for the Tk root
    #w = 1050
    h = 1100 # height for the Tk root

    # get screen width and height
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen

    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)

    # set the dimensions of the screen 
    # and where it is placed
    #root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    root.geometry('%dx%d+%d+%d' % (w, hs*0.9, 0, 0))

    # Make the main window non-resizable
    #root.resizable(0,0)

    # Set main window minimum size
    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    startApp(root,RxChip, TxChip, fref, esd_recovery)




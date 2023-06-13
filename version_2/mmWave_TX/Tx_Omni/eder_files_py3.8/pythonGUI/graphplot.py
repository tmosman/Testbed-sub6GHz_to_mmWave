try:
    import tkinter as tk
except:
    import Tkinter as tk
import matplotlib
from matplotlib import pyplot as plt
from matplotlib import animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
from matplotlib import style
from random import randint
import sys
import FuncThread as FT
import time
import Variables as var
from threading import Lock


class PlotFrame(tk.Frame):
    def __init__(self,root, rxController, txController, TH, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.TH = TH
        self.rxController = rxController
        self.txEderTempData = [0]*var._LIST_LENGTH
        self.txPcbData = [0]*var._LIST_LENGTH
        txCol = "blue"
        self.xdata = range(var._LIST_LENGTH)
        #print style.available
        #style.use('fivethirtyeight')
        #style.use('seaborn')
        #style.use('classic')
        #style.use('bmh')
        style.use('ggplot')
        
        self.chipTemperature = 0
        self.pcbTemperature = 0
        self.lock = Lock()

        # Chip Temp
        self.chipFig = plt.figure()
        self.chipFig.set_size_inches(4,2)
        self.chipTempAx = self.chipFig.add_subplot(1,1,1)
        self.chipTempAx.set_ylabel('Chip Temp (deg. C)', fontsize=var._FONTSIZE, rotation='horizontal')
        self.chipTempAx.yaxis.set_label_coords(0,1.02)
        self.chipTempAx.set_xticklabels([])
        self.txTempLine, = self.chipTempAx.plot(self.xdata, self.txEderTempData, color=txCol, linewidth=2.0)
        #plt.legend(loc=2, fontsize=var._FONTSIZE)

        # Pcb Temp
        self.pcbFig = plt.figure()
        self.pcbFig.set_size_inches(4,2)
        self.pcbTempAx = self.pcbFig.add_subplot(1,1,1)
        self.pcbTempAx.set_ylabel('Pcb Temp (deg. C)', fontsize=var._FONTSIZE, rotation='horizontal')
        self.pcbTempAx.yaxis.set_label_coords(0,1.02)
        self.pcbTempAx.set_xticklabels([])
        self.txPcbLine, = self.pcbTempAx.plot(self.xdata, self.txPcbData, color=txCol, linewidth=2.0)

        for label in self.chipTempAx.get_yticklabels() + self.pcbTempAx.get_yticklabels():
            label.set_fontsize(var._FONTSIZE)

        self.canvas = FigureCanvasTkAgg(self.chipFig, master=self)
        self.canvas.get_tk_widget().pack(side="left",fill="x", expand=True)
        self.canvas = FigureCanvasTkAgg(self.pcbFig, master=self)
        self.canvas.get_tk_widget().pack(side="left",fill="x", expand=True)

        #plt.legend(loc=2, fontsize=var._FONTSIZE)

        self.ybottom = -1
        self.ytop = 30
        self.anims = []
        self.ymargin = 10

    def _readForPlotChip(self):
        if self.lock.acquire(False) == False:
            print ('** not free')
            return 0, self.chipTemperature 
        self.chipTemperature = self.rxController.getTemp()-273.13
        self.lock.release()
        return 0, self.chipTemperature

    def _readForPlotPcb(self):
        if self.lock.acquire(False) == False:
            print ('*** not free')
            return 0, self.pcbTemperature
        try:
            newPcbTemperature = self.rxController.getPcbTemp()
            if newPcbTemperature == -300:
                pass
            else:
                self.pcbTemperature = newPcbTemperature
        except:
            self.pcbTemperature = 0
        self.lock.release()
        return 0, self.pcbTemperature

    def _shiftListChip(self):
        self.txEderTempData = self.txEderTempData[-var._LIST_LENGTH+1:]

    def _shiftListPcb(self):
        self.txPcbData = self.txPcbData[-var._LIST_LENGTH+1:]

    def startPlotThread(self):
        self.anims.append(animation.FuncAnimation(self.chipFig, self.animateChip, interval=var._GRAPHUPDATEDELAY))
        self.anims.append(animation.FuncAnimation(self.pcbFig, self.animatePcb, interval=var._GRAPHUPDATEDELAY))

    def animateChip(self, i=0):
        if self.rxController.view.TxView.isBusy():
            return
        try:
            self._shiftListChip()
            txRead = self.chipTemperature
            self.txEderTempData.append(txRead)
            self.txTempLine.set_ydata(self.txEderTempData)

            if txRead > var._REDTEMPERATURE:
                self.font_color = 'red'
                self.txTempLine.set_color('red')
            else:
                self.font_color = 'black'
                self.txTempLine.set_color('blue')

            self.ytop = max(max(self.txPcbData), max(self.txEderTempData)) + self.ymargin
            self.ybottom = min(min(self.txPcbData), min(self.txEderTempData)) - self.ymargin

            self.chipTempAx.set_ylim(self.ybottom, self.ytop)
            self.chipTempAx.set_ylabel('Chip Temp ( {} deg. C )'.format(round(txRead)), color=self.font_color, fontsize=var._FONTSIZE, rotation='horizontal')
        except:
            print ('*')

        self.TH.put(lambda : self._readForPlotChip())


    def animatePcb(self, i=0):
        if self.rxController.view.TxView.isBusy():
            return
        try:
            self._shiftListPcb()
            txPcbRead = self.pcbTemperature
            self.txPcbData.append(txPcbRead)
            self.txPcbLine.set_ydata(self.txPcbData)

            self.pcbTempAx.set_ylim(self.ybottom, self.ytop)
            self.pcbTempAx.set_ylabel('Pcb Temp ( {} deg. C )'.format(txPcbRead), color='black', fontsize=var._FONTSIZE, rotation='horizontal')
        except:
            print ('**')

        self.TH.put(lambda : self._readForPlotPcb())

    def close(self):
        for anim in self.anims:
            anim.event_source.stop()
            anim = 0

        plt.close()

if __name__ == "__main__":
    root = tk.Tk()
    frame = PlotFrame(root)
    frame.ani = animation.FuncAnimation(fig=frame.chipFig, func=frame.animate, interval=100)
    root.mainloop()

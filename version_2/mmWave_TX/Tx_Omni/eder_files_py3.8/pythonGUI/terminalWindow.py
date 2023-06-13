try:
    import tkinter as tk
except:
    import Tkinter as tk

import sys
import threading
try:
    import queue as Q
except:
    import Queue as Q



class Std_redirector(object):
    def __init__(self,widget, TH):
        self.widget = widget
        self.TH = TH
        self.q = Q.Queue()

    def write(self,string):
        try:
            self.q.put(lambda:self.widget.insert(tk.END,string))
            self.q.put(lambda:self.widget.see(tk.END))
        except:
            pass

    def clear(self):
        try:
            self.q.put(lambda:self.widget.delete('1.0', tk.END))
        except:
            pass

    def log_info(self, string, indentation=0):
        try:
            self.q.put(lambda:self.widget.insert(tk.END,' '*indentation + string + '\n'))
            self.q.put(lambda:self.widget.see(tk.END))
        except:
            pass

    def update(self):
        max_prints = 100
        while not self.q.empty() and max_prints > 0:
            #print max_prints
        #if not self.q.empty():
            func = self.q.get()
            func()
            self.q.task_done()
            max_prints -= 1 
#

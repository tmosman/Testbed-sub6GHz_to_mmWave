import Page as p
try:
    import tkinter as tk
except:
    import Tkinter as tk

try:
    import tkinter.ttk as ttk
except:
    import ttk

from threading import Lock

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../')

import background
import ScrolledFrame

SelectedEntry = [None, None]


class RegisterWindow():

    def __init__(self, parent, chip, *args, **kwargs):
        self.chip = chip

        self.groups = ['tx', 'rx', 'trx', 'adc', 'agc', 'bias', 'pll',  'system', 'vco']
        self.group_tab = {}
        self.reg_tab_layout = {}
        self.regValueList = {}
        self.lock = Lock()

        self.nb = ttk.Notebook(parent)
        for group in self.groups:
            self.group_tab[group] = ScrolledFrame.ScrolledFrame(self.nb)
            self.reg_tab_layout[group] = RegisterTabLayout(self.group_tab[group].interior, chip, group, self)
            self.nb.add(self.group_tab[group], text=group)
             
        self.nb.pack(side="right", fill="both", expand=True)
        self.nb.bind("<<NotebookTabChanged>>", self.pollAndUpdateView)

    def pollAndUpdateView(self, event=None):
        self.poll()
        self.updateView()

    def poll(self):
        self.lock.acquire()
        try:
            for reg in self.reg_tab_layout[self.group].reg_frame:
                self.regValueList[reg] = self.chip.regs.rd(reg)
        except:
            pass
        self.lock.release()


    def updateView(self):
        try:
            self.group = self.nb.tab(self.nb.select(), "text")
            for reg in self.reg_tab_layout[self.group].reg_frame:
                self.reg_tab_layout[self.group].reg_frame[reg].register_value.set(hex(self.regValueList[reg]))
        except:
            pass

class RegisterTabLayout(p.Page):
    def __init__(self, parent, chip, group, regwin, *args, **kwargs):
        p.Page.__init__(self, parent, *args, **kwargs)
        self.reg_frame = {}
        self.chip = chip
        i = 0
        if group == 'awv':
            for reg in chip.mems.tbls_awv:
                self.reg_frame[reg] = RegFrame(parent, chip, reg, regwin)
                self.reg_frame[reg].grid(row=i, column=0, sticky="nsew")
                i = i+1
        else:
            for reg in chip.regs.selected_map:
                if chip.regs.selected_map[reg]['group'] == group:
                    self.reg_frame[reg] = RegFrame(parent, chip, reg, regwin)
                    self.reg_frame[reg].grid(row=i, column=0, sticky="nsew")
                    i = i+1


class RegFrame(p.Page):
    def __init__(self, parent, chip, register_name, regwin, *args, **kwargs):
        p.Page.__init__(self, parent, *args, **kwargs)
        self.chip = chip
        self.name = register_name
        self.regwin = regwin
        self.register_value = tk.StringVar()
        self.reg_name_label = tk.Label(self, text=register_name, anchor="w", width=20)
        self.reg_name_label.bind('<Button-1>', self.enterKeyPressedEditMode)
        self.value_label = tk.Label(self, textvariable=self.register_value, anchor="e", width=10)
        self.value_label.bind('<Button-1>', self.enterKeyPressedEditMode)
        self.hex_entry_value = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.hex_entry_value, width=10)
        self.entry.bind('<Return>', self.enterKeyPressed)
        self.entry.bind("<Enter>", self.entry_select_callback)
        self.reg_name_label.pack(side="left",  fill="both")
        self.value_label.pack(side="right")
        if register_name.startswith('bf_'):
            self.register_value.set(hex(chip.mems.awv.rd(register_name)))
        else:
            self.register_value.set(hex(chip.regs.rd(register_name)))
        # Create tooltip
        self.toolTip = ToolTip(self.reg_name_label, self.chip.regs.selected_map[self.name]['doc'])
        self.reg_name_label.bind('<Enter>', self.enter)
        self.reg_name_label.bind('<Leave>', self.leave)

    def enter(self, event):
        self.toolTip.showtip()
                
    def leave(self, event):
        self.toolTip.hidetip()


    def enterKeyPressedEditMode(self, event):
        global SelectedEntry
        if (SelectedEntry[0] != None) and (SelectedEntry[0] != self.entry):
            SelectedEntry[0].pack_forget()
            SelectedEntry[1].pack(side="right")
        
        SelectedEntry = [self.entry, self.value_label]
        self.value_label.pack_forget()
        self.entry.pack(side="right")
        self.hex_entry_value.set(self.register_value.get())

    def enterKeyPressed(self, event):
        self.updateValue()
        self.entry.pack_forget()
        self.value_label.pack(side="right")

    def updateValue(self):
        value_str = self.hex_entry_value.get()
        if ('0x' in value_str) or ('0X' in value_str):
            # Hex
            try:
                value = int(value_str, 16)
            except:
                return
        else:
            # Dec
            try:
                value = int(value_str, 10)
            except:
                return

        self.chip.regs.wr(self.name, value)
        self.regwin.regValueList[self.name] = value
        self.register_value.set(hex(value))

    def entry_select_callback(self, event):
        self.entry.icursor(tk.END)
        self.entry.focus()


class ToolTip(object):

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_pointerx() + 27
        y = y + cy + self.widget.winfo_pointery() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
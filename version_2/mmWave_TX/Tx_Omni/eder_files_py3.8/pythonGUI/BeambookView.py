import Page as p
try:
    import tkinter as tk
except:
    import Tkinter as tk

try:
    import tkinter.ttk as ttk
except:
    import ttk
try:
    from tkinter import *
except:
    from Tkinter import *

import Variables as var
import platform

class BeambookView(p.Page):
    def __init__(self, parent, controller, TH, *args, **kwargs):
        p.Page.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.lastPressed = None
        self.TH = TH
        self.controller = controller
        left_section = p.Page(parent)

        if platform.system().upper() == 'LINUX':
            file_name_length = 36
            description_length = 70
            supported_mod_length = 40
            version_length = 7
            selected_length = 8
        elif platform.system().upper() == 'WINDOWS':
            file_name_length = 43
            description_length = 100
            supported_mod_length = 45
            version_length = 7
            selected_length = 8
        else:
            file_name_length = 36
            description_length = 80
            supported_mod_length = 40
            version_length = 7
            selected_length = 8


        tk.Label(left_section, text='TX beambooks (Double-Click to select)').pack(side=TOP)
        self.mlb_tx = MultiListbox(left_section, 
                                   (('File name', file_name_length), ('Description', description_length), ('Supported modules', supported_mod_length), ('Version', version_length), ('Selected', selected_length)), 
                                   self.tx_beambook_selected)
        self.controller.eder.tx.bf.awv.bbp.subscribe(self.tx_beambook_selected)
        for index in range(0, len(self.controller.eder.tx.bf.awv.bbp.beambook_index)):
            if self.controller.eder.tx.bf.awv.bbp.beambook_index[index]['beambook_type'] == 'TX':
                self.mlb_tx.insert(END, (self.controller.eder.tx.bf.awv.bbp.beambook_index[index]['file_name'], \
                                self.controller.eder.tx.bf.awv.bbp.beambook_index[index]['desc'], \
                                self.controller.eder.tx.bf.awv.bbp.beambook_index[index]['module_types'], \
                                self.controller.eder.tx.bf.awv.bbp.beambook_index[index]['version'], \
                                self.controller.eder.tx.bf.awv.bbp.beambook_index[index]['selected']))
        self.mlb_tx.pack(side=TOP, expand=NO,fill=BOTH)
        left_section.pack(side=LEFT, fill=BOTH)

        tk.Label(left_section, text='\nRX beambooks (Double-Click to select)').pack(side=TOP)
        self.mlb_rx = MultiListbox(left_section, 
                                   (('File name', file_name_length), ('Description', description_length), ('Supported modules', supported_mod_length), ('Version', version_length), ('Selected', selected_length)), 
                                   self.rx_beambook_selected)
        self.controller.eder.rx.bf.awv.bbp.subscribe(self.rx_beambook_selected)
        for index in range(0, len(self.controller.eder.rx.bf.awv.bbp.beambook_index)):
            if self.controller.eder.rx.bf.awv.bbp.beambook_index[index]['beambook_type'] == 'RX':
                self.mlb_rx.insert(END, (self.controller.eder.rx.bf.awv.bbp.beambook_index[index]['file_name'], \
                                self.controller.eder.rx.bf.awv.bbp.beambook_index[index]['desc'], \
                                self.controller.eder.rx.bf.awv.bbp.beambook_index[index]['module_types'], \
                                self.controller.eder.rx.bf.awv.bbp.beambook_index[index]['version'], \
                                self.controller.eder.rx.bf.awv.bbp.beambook_index[index]['selected']))
        self.mlb_rx.pack(side=TOP, expand=NO,fill=BOTH)
        left_section.pack(side=LEFT, fill=BOTH)

    def tx_beambook_selected(self, set_index=True):
        selected_beambook_index = self.controller.eder.tx.bf.awv.bbp.get_selected_beambook()
        try:
            if selected_beambook_index == self.mlb_tx.curselection()[0]:
                return
        except:
            pass
        if selected_beambook_index != None:
            selected = self.mlb_tx.get(selected_beambook_index)
            selected[4] = ''
            self.mlb_tx.delete(selected_beambook_index)
            self.mlb_tx.insert(selected_beambook_index, selected)
        try:
            selected_beambook_index = self.mlb_tx.curselection()[0]
        except:
            pass
        if set_index:
            self.controller.eder.tx.bf.awv.bbp.set_selected_beambook(selected_beambook_index)
            self.controller.eder.tx.bf.awv.setup()
        selected = self.mlb_tx.get(selected_beambook_index)
        selected[4] = 'Yes'
        self.mlb_tx.delete(selected_beambook_index)
        self.mlb_tx.insert(selected_beambook_index, selected)
        self.mlb_tx.selection_set(selected_beambook_index)

    def rx_beambook_selected(self, set_index=True):
        selected_beambook_index = self.controller.eder.rx.bf.awv.bbp.get_selected_beambook()
        try:
            if selected_beambook_index == self.mlb_rx.curselection()[0]:
                return
        except:
            pass
        if selected_beambook_index != None:
            selected = self.mlb_rx.get(selected_beambook_index)
            selected[4] = ''
            self.mlb_rx.delete(selected_beambook_index)
            self.mlb_rx.insert(selected_beambook_index, selected)
        try:
            selected_beambook_index = self.mlb_rx.curselection()[0]
        except:
            pass
        if set_index:
            self.controller.eder.rx.bf.awv.bbp.set_selected_beambook(selected_beambook_index)
            self.controller.eder.rx.bf.awv.setup()
        selected = self.mlb_rx.get(selected_beambook_index)
        selected[4] = 'Yes'
        self.mlb_rx.delete(selected_beambook_index)
        self.mlb_rx.insert(selected_beambook_index, selected)
        self.mlb_rx.selection_set(selected_beambook_index)



class MultiListbox(Frame):
    def __init__(self, master, lists, cbselected):
        Frame.__init__(self, master)
        self.cbselected = cbselected
        self.lists = []
        for l,w in lists:
            frame = Frame(self); frame.pack(side=LEFT, expand=YES, fill=BOTH)
            Label(frame, text=l, borderwidth=1, relief=RAISED).pack(fill=X)
            lb = Listbox(frame, width=w, borderwidth=0, height=7, selectborderwidth=0, relief=FLAT, exportselection=FALSE)
            lb.pack(expand=YES, fill=BOTH)
            self.lists.append(lb)
            lb.bind('<B1-Motion>', lambda e, s=self: s._select(e.y))
            lb.bind('<Button-1>', lambda e, s=self: s._select(e.y))
            lb.bind('<Leave>', lambda e: 'break')
            lb.bind('<B2-Motion>', lambda e, s=self: s._b2motion(e.x, e.y))
            lb.bind('<Button-2>', lambda e, s=self: s._button2(e.x, e.y))
            lb.bind('<Double 1>', lambda e, s=self: s.__select(e.y))
        frame = Frame(self); frame.pack(side=LEFT, fill=Y)
        Label(frame, borderwidth=1, relief=RAISED).pack(fill=X)
        sb = Scrollbar(frame, orient=VERTICAL, command=self._scroll)
        sb.pack(expand=YES, fill=Y)
        self.lists[0]['yscrollcommand']=sb.set

    def __select(self, y):
        self.cbselected()

    def _select(self, y):
        row = self.lists[0].nearest(y)
        self.selection_clear(0, END)
        self.selection_set(row)
        return 'break'

    def _button2(self, x, y):
        for l in self.lists: l.scan_mark(x, y)
        return 'break'

    def _b2motion(self, x, y):
        for l in self.lists: l.scan_dragto(x, y)
        return 'break'

    def _scroll(self, *args):
        for l in self.lists:
            apply(l.yview, args)

    def curselection(self):
        return self.lists[0].curselection()

    def delete(self, first, last=None):
        for l in self.lists:
            l.delete(first, last)

    def get(self, first, last=None):
        result = []
        for l in self.lists:
            result.append(l.get(first,last))
        if last: return apply(map, [None] + result)
        return result
        
    def index(self, index):
        self.lists[0].index(index)

    def insert(self, index, *elements):
        for e in elements:
            i = 0
            for l in self.lists:
                l.insert(index, e[i])
                i = i + 1

    def size(self):
        return self.lists[0].size()

    def see(self, index):
        for l in self.lists:
            l.see(index)

    def selection_anchor(self, index):
        for l in self.lists:
            l.selection_anchor(index)

    def selection_clear(self, first, last=None):
        for l in self.lists:
            l.selection_clear(first, last)

    def selection_includes(self, index):
        return self.lists[0].selection_includes(index)

    def selection_set(self, first, last=None):
        for l in self.lists:
            l.selection_set(first, last)
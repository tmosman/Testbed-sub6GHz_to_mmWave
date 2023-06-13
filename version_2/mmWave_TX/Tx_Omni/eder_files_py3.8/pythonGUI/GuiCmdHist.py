class GuiCmdHist(object):

    def __init__(self):
        self.command_history = []

    def load_cmd_history(self):
        try:
            file =open('guicmd.hist', 'r')
            self.command_history = file.readlines()
            file.close()
            for index in range(0,len(self.command_history)):
                self.command_history[index] = self.command_history[index].replace('\n', '')
            #self.CommandCombobox.configure(values=self.command_history)
        except IOError:
            self.init_cmd_history()
        return self.command_history

    def save_cmd_history(self):
        try:
            file =open('guicmd.hist', 'w')
            for command in self.command_history:
                file.write(command+'\n')
        except:
            pass
        file.close()

    def init_cmd_history(self):
        self.command_history = []
        self.command_history.insert(0, 'eder.')

    def add_to_cmd_history(self, code):
        if len(self.command_history) > 1:
            if code == self.command_history[1]:
                return

        self.command_history.insert(1,code)
        if len(self.command_history) > 100:
            self.command_history.pop(100)
        #self.CommandCombobox.configure(values=self.command_history)
        return self.command_history


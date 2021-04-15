from dataclasses import dataclass
from datetime import *

@dataclass
class Session:
    Title:str = None
    QtdOptions:int = None
    Options:list = None
    Timeout:str = None
    VoteNumber:int = None
    VotePOption:dict = None
    Win_tie:list = None
    Result:list = None
    FlagFinished:bool = None

    def __init__(self,Title,QtdOptions,Options,Timeout):
        self.Title = Title
        self.QtdOptions = QtdOptions
        self.Options = Options
        self.Timeout = Timeout
        self.Win_tie = []
        self.init()

    def init(self):
        self.FlagFinished = False
        self.VoteNumber = 0
        self.VotePOption = dict.fromkeys(self.Options,0)
        
    def vote(self,option):
        print(str(self.VotePOption))
        print(option)
        if (self.VotePOption.get(option,-1)) != -1:
            self.VoteNumber += 1
            self.VotePOption[option] += 1
            return True
        else:
            return False
    
    def calc_result(self):
        if self.is_finished():
            result = []
            self.Win_tie = []
            vwin = 0
            for opt in self.Options:
                v_atual = self.VotePOption[opt]
                if v_atual == vwin :
                    self.Win_tie.append(opt)
                if(v_atual > vwin):
                    self.Win_tie = [opt]
                    vwin = v_atual
                perc = 0.0
                if(self.VoteNumber !=0):
                    perc = float(v_atual)/float(self.VoteNumber) * 100
                straux = opt + ' ' + str(perc) + '%'
                result.append(straux)
            return result
        else:
            return 'Not defined'

    def is_finished(self):
        now = datetime.today()
        closeDate = datetime.strptime(self.Timeout, '%Y/%m/%d %H:%M')
        print(closeDate)
        if(now.year > closeDate.year):
            self.FlagFinished = True
            return self.FlagFinished
        if(now.year < closeDate.year):
            self.FlagFinished = False
            return self.FlagFinished
        if(now.month > closeDate.month):
            self.FlagFinished = True
            return self.FlagFinished
        if(now.month < closeDate.month):
            self.FlagFinished = False
            return self.FlagFinished
        if(now.day > closeDate.day):
            self.FlagFinished = True
            return self.FlagFinished
        if(now.day < closeDate.day):
            self.FlagFinished = False
            return self.FlagFinished
        if(now.hour > closeDate.hour):
            self.FlagFinished = True
            return self.FlagFinished
        if(now.hour < closeDate.hour):
            self.FlagFinished = False
            return self.FlagFinished
        if(now.minute > closeDate.minute):
            self.FlagFinished = True
            return self.FlagFinished
        if(now.minute < closeDate.minute):
            self.FlagFinished = False
            return self.FlagFinished
        self.FlagFinished = True
        return self.FlagFinished
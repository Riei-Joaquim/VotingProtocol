from dataclasses import dataclass

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
            vwin = 0
            for opt in self.Options:
                v_atual = self.VotePOption[opt]
                if v_atual == vwin :
                    self.Win_tie.append(opt)
                if(v_atual > vwin):
                    self.Win_tie = [opt]
                    vwin = v_atual
                perc = float(v_atual)/float(self.VoteNumber)
                straux = opt + str(perc) + '%'
                result.append(straux)
            return result
        else:
            return 'Not defined'

    def is_finished(self):
        return self.FlagFinished
from VP.Entities import *
from VP.Communication.ProcessPacket import ProcessPacket

class VotingServer:
    """
    Voting Server
    """
    def __init__(self):
        self.processPacket = ProcessPacket()
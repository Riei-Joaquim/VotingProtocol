from VP.Entities import *
from VP.Communication.ProcessPacket import ProcessPacket

class VotingClient:
    """
    Voting Client
    """
    def __init__(self):
        self.processPacket = ProcessPacket()
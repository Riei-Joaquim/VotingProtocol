from VotingProtocol.Entities import *
from VotingProtocol.Communication.Communication import Communication
import time
import json
from threading import Thread

class VotingClient:
    """
    Voting Client
    """
    def __init__(self):
        self.Comm = Communication('CLIENT')
    
    def discoverServers(self):
        while True:
            msg = HelloServers()
            self.Comm.broadcastPacket(msg)
            ans = self.Comm.tryReadMessage(None)
            if ans["Packet"] == "Hello Client":
                p = HelloClient(**ans)
                print(p)
                self.Comm.setupRemoteServer(p.ServerAddress, p.PublicKey)
                break
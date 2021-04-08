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
            ans = self.Comm.tryReadMessage()
            jsonObj = json.loads(ans)

            if jsonObj["Packet"] == "Hello Client":
                print(ans)
                self.Comm.setupRemoteServer(jsonObj["ServerAddress"], jsonObj["PublicKey"])
                break
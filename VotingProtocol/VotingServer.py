from VotingProtocol.Entities import *
from VotingProtocol.Communication.Communication import Communication
from VotingProtocol.Communication.ProcessPacket import ProcessPacket
import json

class VotingServer:
    """
    Voting Server
    """
    def __init__(self):
        self.CommGeneral = Communication('SERVER')
        self.CommClients = []
        self.ProcessPacket = ProcessPacket()
    
    def run(self):
        print('server is running!')
        while True:
            data, addr = self.CommGeneral.readMessage()
            jsonObj = json.loads(data)
            if jsonObj["Packet"] == "Hello Servers":
                hello = HelloClient(ServerAddress=str(self.CommGeneral.getLocalIP()), PublicKey=str(self.ProcessPacket.getLocalPublicKey()))
                self.CommGeneral.sendPacketTo(hello, addr[0])
                print('from ', addr, 'receive', data)
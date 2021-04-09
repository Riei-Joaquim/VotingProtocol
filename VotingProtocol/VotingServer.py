from VotingProtocol.Entities import *
import VotingProtocol.Communication.Communication as Comm
from VotingProtocol.Communication.ProcessPacket import ProcessPacket
import json
from threading import Thread

def VotingServer():
    CommUDPSocket = Comm.startUDPSocket('SERVER')
    managerUDP = Thread(target=Comm.UDPServerRunner, args=(CommUDPSocket,))
    managerTCP = Thread(target=Comm.TCPServerRunner)
    managerUDP.start()
    managerTCP.start()
    managerUDP.join()
    managerTCP.join()

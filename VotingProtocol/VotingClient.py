from VotingProtocol.Entities import *
import VotingProtocol.Communication.Communication as Comm
import time
import json
from threading import Thread

def VotingClient():
    # Discover servers infos
    CommUDPSocket = Comm.startUDPSocket('CLIENT')
    hello = Comm.UDPDiscoverServers(CommUDPSocket)

    if hello is not None:
        print(hello)
        Comm.setupRemoteServer(hello.ServerAddress, hello.PublicKey)

    CommUDPSocket.close()

    # Conect in server
    Comm.TCPClientRunner()

    
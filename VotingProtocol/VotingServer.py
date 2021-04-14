from VotingProtocol.Entities import *
import VotingProtocol.Communication.Communication as Comm
from VotingProtocol.Communication.ProcessPacket import ProcessPacket
import json
from threading import Thread

def VotingServer(signaturePrivateKey:bytes, userAccounts:dict, udpPort:int, tcpPort:int, tcpCommCapabilities:int):
    """
    Metodo principal para a execução da rotina do sevidor, no protocolo de votação. 
    """
    # Setup de parametros da rede para a operação do protocolo pelo lado do servidor
    Comm.setupPorts(udpPort, tcpPort)
    Comm.setServerCapabilities(tcpCommCapabilities)
    Comm.setSignature(signaturePrivateKey, 'SIGNER')

    CommUDPSocket = Comm.startUDPSocket('SERVER')
    managerUDP = Thread(target=Comm.UDPServerRunner, args=(CommUDPSocket,))
    managerTCP = Thread(target=Comm.TCPServerRunner, args=(userAccounts,))
    managerUDP.start()
    managerTCP.start()
    managerUDP.join()
    managerTCP.join()

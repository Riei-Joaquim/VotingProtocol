from VotingProtocol.Entities import *
import VotingProtocol.Communication.Communication as Comm
from VotingProtocol.Communication.ProcessPacket import ProcessPacket
import json
from threading import Thread

def VotingServer():
    SIGNATURE_PRIVATE_BYTES = b'-----BEGIN RSA PRIVATE KEY-----\n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\n-----END RSA PRIVATE KEY-----\n'
    ACCOUNTS_USERS = {
        'riei@gmail.com':'12345',
        'joaquim@gmail.com':'12345',
        'matos@gmail.com':'12345',
        'rodrigues@gmail.com':'12345',
        'victor@gmail.com':'12345',
        'hugo@gmail.com':'12345',
        'meireles@gmail.com':'12345',
        'silva@gmail.com':'12345'
    }

    CommUDPSocket = Comm.startUDPSocket('SERVER')
    managerUDP = Thread(target=Comm.UDPServerRunner, args=(CommUDPSocket, SIGNATURE_PRIVATE_BYTES,))
    managerTCP = Thread(target=Comm.TCPServerRunner, args=(ACCOUNTS_USERS,))
    managerUDP.start()
    managerTCP.start()
    managerUDP.join()
    managerTCP.join()

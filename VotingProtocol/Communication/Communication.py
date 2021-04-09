from VotingProtocol.Communication.ProcessPacket import ProcessPacket
from VotingProtocol.Entities import *
from socket import *
from threading import Thread
import time
import os
import sys
import json

############################################# UTILS ##############################################
DEST_IP ='255.255.255.255'
UDP_PORT = 12000
TCP_PORT = 12001
TCP_SERVER_NAME = ''
CAPACITY_OF_USERS = 100
pPacket = ProcessPacket()

def getLocalIP():
    hostName = gethostname()
    hostIP = gethostbyname(hostName)
    return hostIP

def setupRemoteServer(serverIP, serverPublicKey):
    global DEST_IP
    DEST_IP = serverIP
    pPacket.setRemotePublicKey(serverPublicKey)

########################################## UDP PROTOCOL ##########################################
def startUDPSocket(typeSocket):
    UDPSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)        
    UDPSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    UDPSocket.setsockopt(IPPROTO_IP, IP_TTL, 128)
    if typeSocket == 'CLIENT':
        UDPSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        UDPSocket.settimeout(5000)
        UDPSocket.bind((str(getLocalIP()), UDP_PORT))
    else:
        UDPSocket.bind(('', UDP_PORT))

    return UDPSocket

def UDPReadMessage(comm, typeObject):
    data, addr = comm.recvfrom(4096)
    decode = pPacket.decode(data, typeObject)
    return decode, addr
    
def UDPBroadcastPacket(comm, packet):
    encoded = pPacket.encode(packet)
    comm.sendto(encoded, (DEST_IP, UDP_PORT))
    
def UDPSendPacketTo(comm, packet, IP):
    encoded = pPacket.encode(packet)
    comm.sendto(encoded, (IP, UDP_PORT))

def UDPServerRunner(comm):
    print('O servidor UDP está ligado e operante!')
    while True:
        data, addr = UDPReadMessage(comm, HelloServers)
            
        if data is not None:
            hello = HelloClient(ServerAddress=str(getLocalIP()), PublicKey=str(pPacket.getLocalPublicKey()))
            UDPSendPacketTo(comm,hello, addr[0]) 
            print('from ', addr, 'receive', data)

def UDPDiscoverServers(comm):
    hello = None
    while True:
        msg = HelloServers()
        UDPBroadcastPacket(comm, msg)
        ans = UDPTryReadMessage(comm, HelloClient)
        if ans is not None:
            hello = ans
            break
    
    return hello

def UDPTryReadMessage(comm, typeObject):
    try:
        encoded = comm.recv(4096)
        return pPacket.decode(encoded, typeObject)
    except timeout as e:
        return None

############################################ TCP PROTOCOL ############################################
def TCPClientReceive(comm, pPacketClient):
    while True:
        message = comm.recv(10240)
        decode = pPacketClient.decode(message, None)
        print(decode)

def TCPClientConnection(comm, addr, pPacketClient):
    while True:
        message = comm.recv(10240)
        decode = pPacketClient.decode(message, None)
        print(decode)

def TCPClientRunner():
    commTCPSocket = socket(AF_INET, SOCK_STREAM)
    commTCPSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    commTCPSocket.setsockopt(IPPROTO_IP, IP_TTL, 128)
    commTCPSocket.connect((DEST_IP, TCP_PORT))

    t = Thread(target=TCPClientReceive, args=(commTCPSocket, pPacket,))
    t.start()

    while True:
        #comando = ClientData(Email='meuNobre@', Password='torugo', PublicKey= pPacket.getLocalPublicKey())
        comando = HelloServers()
        commTCPSocket.send(pPacket.encode(comando))
        time.sleep(5)

def TCPServerRunner():
    commTCPSocket = socket(AF_INET, SOCK_STREAM)
    commTCPSocket.bind((TCP_SERVER_NAME, TCP_PORT))
    commTCPSocket.listen(CAPACITY_OF_USERS)

    print("O servidor TCP está ligado e operante!")
    while True:
        connectionSocket, addr = commTCPSocket.accept()
        pPacketClient = ProcessPacket('RSA', pPacket.RSALocalPrivateKey)
        t = Thread(target=TCPClientConnection, args=(connectionSocket, addr, pPacketClient)) 
        t.start()

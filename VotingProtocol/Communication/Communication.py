from VotingProtocol.Communication.ProcessPacket import ProcessPacket
from socket import *
from threading import Thread
import os
import sys
import json

class Communication:
    def __init__(self, Type, IP='255.255.255.255', Port=12000):
        self.IP = IP
        self.Port = Port
        self.Adress = (self.IP, self.Port)

        self.PPacket = ProcessPacket()
        # Stating in UDP Config
        self.CommSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)        
        self.CommSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.CommSocket.setsockopt(IPPROTO_IP, IP_TTL, 128)

        if Type == 'CLIENT':
            self.CommSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.CommSocket.settimeout(5000)
            self.CommSocket.bind((str(self.getLocalIP()),self.Port))
        elif Type == 'SERVER':
            self.CommSocket.bind(('', self.Port))
        else:
            self.CommSocket.bind(self.Adress)
        # Stating in TCP Config
        # self.CommSocket = socket(AF_INET, SOCK_DGRAM)
        # self.CommSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # self.CommSocket.setsockopt(IPPROTO_IP, IP_TTL, 128)
        # self.CommSocket.connect(('192.168.0.103', 12000))
        # self.ReadThread = Thread(target=self.readMessages, args=(self.CommSocket,))
        # self.ReadThread.start()
    
    def tryReadMessage(self, typeObject):
        try:
            encoded = self.CommSocket.recv(1024)
            return self.PPacket.decode(encoded, typeObject)
        except timeout as e:
            return None

    def setupRemoteServer(self, serverIP, serverPublicKey):
        self.IP = serverIP
        self.PPacket.setRemotePublicKey(serverPublicKey)

    def close(self):
        self.CommSocket.close()
    
    def readMessage(self, typeObject):
        data, addr = self.CommSocket.recvfrom(1024)
        decode = self.PPacket.decode(data, typeObject)
        return decode, addr
    
    def getLocalIP(self):
        hostName = gethostname()
        hostIP = gethostbyname(hostName)
        return hostIP

    def broadcastPacket(self, packet):
        encoded = self.PPacket.encode(packet)
        self.CommSocket.sendto(encoded, self.Adress)
    
    def sendPacketTo(self, packet, IP):
        encoded = self.PPacket.encode(packet)
        self.CommSocket.sendto(encoded, (IP,self.Port))
    
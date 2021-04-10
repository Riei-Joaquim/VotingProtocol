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
def TCPClientConnection(comm, addr, pPacketClient):
    while True:
        message = comm.recv(10240)
        decode = pPacketClient.decode(message, None)
        if decode is not None:
            if decode["Packet"] == "Client Data":
                clientInfos = ClientData(**decode)
                pPacketClient.setRemotePublicKey(clientInfos.PublicKey)
                ans = EvaluationData(Token='123geratoken12345',FlagAutentication=True)#funcao de autenticar no lugar do TRUE
                comm.send(pPacketClient.encode(ans))
            if decode["Packet"] == "Client Request":
                #Apos verificar se o Token é válido
                #
                clientReq = ClientRequest(**decode)
                ans = RequestResponse()
                if(clientReq.FlagAvailableSession):
                    ans.FlagAvailableSessions = True
                    ans.FlagCompletedSessions = False
                    #fazer um for pra pegar todas as sessões disponíveis
                    temp = ['Votacao 1','Melhor filme'] # temp sera substituido pelo vetor de sessions
                    ans.QtdSessions = len(temp) #valor temporario,vou ter que consultar o vetor
                    ans.Sessions = temp
                elif(clientReq.FlagCompletedSession):
                    ans.FlagAvailableSessions = False
                    ans.FlagCompletedSessions = True
                    #fazer um for pra pegar todas as sessões completas
                    temp = ['Votacao 0','Melhor serie'] # temp sera substituido pelo vetor de sessions
                    ans.QtdSessions = len(temp) #valor temporario,vou ter que consultar o vetor
                    ans.Sessions = temp
                comm.send(pPacketClient.encode(ans))
            if decode["Packet"] == "Client Request Create":
                #Apos verificar se o Token é válido
                #
                clientReq = ClientRequestCreate(**decode)
                ans = RequestResponse()
                ans.FlagAvailableSessions = True
                ans.FlagCompletedSessions = False
                #fazer um for pra pegar todas as sessões disponíveis
                temp = ['Votacao 1','Melhor filme'] # temp sera substituido pelo vetor de sessions
                temp.append(clientReq.Title)
                ans.QtdSessions = len(temp) #valor temporario,vou ter que consultar o vetor
                ans.Sessions = temp
                comm.send(pPacketClient.encode(ans))
            if decode["Packet"] == "Session Details":
                #Apos verificar o token de novo
                #
                ans = SessionDescription()
                clientReq = SessionDetails(**decode)
                ans.Title = clientReq.Title
                ans.FlagFinished = False #vai ter que avaliar
                temp = ["Meu Nobre", "Meu Riei"]
                ans.QtdOptions = len(temp)
                ans.Options = temp
                ans.Result = 'Not defined' #vai ter que avaliar
                comm.send(pPacketClient.encode(ans))
            if decode["Packet"] == "Vote":
                #Apos verificar o token de novo
                #
                clientVote = Vote(**decode)
                ans = VoteResponse()
                ##Consultar se a sessão existe
                ##Consultar se a opção existe
                ans.Title = clientVote.Title
                ans.Options = clientVote.Options
                ans.FlagComputed = True #se tiver dado certo
                ans.Description = 'Sucessfull'
                comm.send(pPacketClient.encode(ans))             
        else:
            print('DECODE ERA NONE')
            sys.exit(-1)
        print('decode = ',decode)

def TCPTryReadMessage(comm, typeObject):
    try:
        encoded = comm.recv(10240)
        return pPacket.decode(encoded, typeObject)
    except Exception as e:
        return None

def TCPClientRunner():
    commTCPSocket = socket(AF_INET, SOCK_STREAM)
    commTCPSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    commTCPSocket.setsockopt(IPPROTO_IP, IP_TTL, 128)
    commTCPSocket.connect((DEST_IP, TCP_PORT))
    commTCPSocket.settimeout(1)

    comando = ClientData(Email='meuNobre@', Password='torugo', PublicKey= pPacket.getLocalPublicKey())
    commTCPSocket.send(pPacket.encode(comando))
    serverAns = TCPTryReadMessage(commTCPSocket, EvaluationData)
    #verificar se foi autenticado, se n tenta de novo
    token = serverAns.Token
    time.sleep(5)
    state = "ClientRequest"
    while True:
        if(state == "ClientRequest"):
            comando = ClientRequest(Token=token,FlagAvailableSession=True)
            commTCPSocket.send(pPacket.encode(comando))
            serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
            print('Server ans CR = ',serverAns.Sessions)
            state = "Vote"
        if(state == "Vote"):
            comando = Vote(Title='Votacao 1', Options='Meu Riei')
            commTCPSocket.send(pPacket.encode(comando))
            serverAns = TCPTryReadMessage(commTCPSocket, VoteResponse)
            print('Server ans Vt = ',serverAns.Description,'\n',serverAns.Title,'\n',serverAns.Options)
            state = "question"
        if(state == "question"):
            x = input('vai pra onde?')
            state = "ClientRequest" if x == 0 else "Vote"

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
        print('oi')
        return

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
lSes = []

def getLocalIP():
    hostName = gethostname()
    hostIP = gethostbyname(hostName)
    return hostIP

def setupRemoteServer(serverIP, serverPublicKey):
    global DEST_IP
    DEST_IP = serverIP
    pPacket.setRemotePublicKey(serverPublicKey)

def getAvailableSessionsName():
    temp = []
    for s in lSes:
        if not s.is_finished():
            temp.append(s.Title)
    return temp

def getCompletedSessionsName():
    temp = []
    for s in lSes:
        if s.is_finished():
            temp.append(s.Title)
    return temp

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
                    temp = getAvailableSessionsName()
                    #temp = ['Votacao 1','Melhor filme'] # temp sera substituido pelo vetor de sessions
                    ans.QtdSessions = len(temp) #valor temporario,vou ter que consultar o vetor
                    ans.Sessions = temp
                elif(clientReq.FlagCompletedSession):
                    ans.FlagAvailableSessions = False
                    ans.FlagCompletedSessions = True
                    temp = getCompletedSessionsName()
                    #temp = ['Votacao 0','Melhor serie'] # temp sera substituido pelo vetor de sessions
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
                sessionAtual = Session(clientReq.Title,clientReq.QtdOptions,clientReq.Options,'data')
                lSes.append(sessionAtual)
                temp = getAvailableSessionsName()
                #temp = ['Votacao 1','Melhor filme'] # temp sera substituido pelo vetor de sessions
                ans.QtdSessions = len(temp) #valor temporario,vou ter que consultar o vetor
                ans.Sessions = temp
                comm.send(pPacketClient.encode(ans))
            if decode["Packet"] == "Session Details":
                #Apos verificar o token de novo
                #
                ans = SessionDescription()
                clientReq = SessionDetails(**decode)
                ans.Title = 'Not found'
                ans.FlagFinished = False #vai ter que avaliar
                ans.QtdOptions = 0
                ans.Options = []
                ans.Result = 'Not defined' #vai ter que avaliar

                for s in lSes:
                    if s.Title == clientReq.Title:
                        ans.Title = s.Title
                        ans.FlagFinished = s.is_finished()
                        ans.QtdOptions = s.QtdOptions
                        ans.Options = s.Options
                        ans.Result = s.calc_result() 
                        break

                comm.send(pPacketClient.encode(ans))
            if decode["Packet"] == "Vote":
                #Apos verificar o token de novo
                #
                clientVote = Vote(**decode)
                ans = VoteResponse()
                ##Consultar se a sessão existe
                ##Consultar se a opção existe
                ans.Title = clientVote.Title + ' Not found'
                ans.Option = clientVote.Option + ' Not found'
                ans.FlagComputed = False #se tiver dado errado
                ans.Description = 'Session not found'

                for s in lSes:
                    if s.Title == clientVote.Title:
                        ans.Title = s.Title
                        ans.FlagComputed = s.vote(clientVote.Option)
                        print(ans.FlagComputed)
                        if ans.FlagComputed == True :
                            ans.Option = clientVote.Option
                            ans.Description = 'Sucessfull Vote' 
                        else:
                            ans.Description = 'Option not found'
                        break

                comm.send(pPacketClient.encode(ans))             
        else:
            print('DECODE ERA NONE')
            return
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
    
    email = input('insira o email: ')
    senha = input('insira a senha: ')
    #'meuNobre@'
    #'meuNobre@'
    comando = ClientData(Email=email, Password=senha, PublicKey= pPacket.getLocalPublicKey())
    commTCPSocket.send(pPacket.encode(comando))
    serverAns = TCPTryReadMessage(commTCPSocket, EvaluationData)
    #verificar se foi autenticado, se n tenta de novo
    
    while serverAns.FlagAutentication != True :
        print('Dados invalidos, tente novamente!')
        email = input('insira o email: ')
        senha = input('insira a senha: ')
        #'meuNobre@'
        #'meuNobre@'
        comando = ClientData(Email=email, Password=senha, PublicKey= pPacket.getLocalPublicKey())
        commTCPSocket.send(pPacket.encode(comando))
        serverAns = TCPTryReadMessage(commTCPSocket, EvaluationData)
    
    token = serverAns.Token
    time.sleep(2)
    state = "ClientRequest"
    while True:
        if(state == "ClientRequest"):
            option = int(input('1(consultar sessoes abertas);\n2(consultar sessoes concluidas);\n3(criar sessao)\n'))
            if(option == 1):
                comando = ClientRequest(Token=token,FlagAvailableSession=True)
                commTCPSocket.send(pPacket.encode(comando))
                serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                print('Server ans CR = ',serverAns.Sessions)
                op2 = ''
                k = 0
                while(op2 != 'n' and op2 != 'N' and op2 != 'y' and op2 != 'Y'):
                    saux = 'Deseja obter mais detalhes sobre alguma sessão? Y(sim)/N(Nao)'
                    saux = 'Nao entendi. ' + saux if k == 1 else saux
                    k = 1
                    print(saux, end=' ')
                    op2 = input()
                    if(op2 == 'y' or op2 == 'Y'):
                        state = "SessionDetails"
                    if(op2 == 'n' or op2 == 'N'):
                        state = "ClientRequest"   
            
            if(option == 2):
                comando = ClientRequest(Token=token,FlagCompletedSession=True)
                commTCPSocket.send(pPacket.encode(comando))
                serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                print('Server ans CR = ',serverAns.Sessions)
                op2 = ''
                k = 0
                while(op2 != 'n' and op2 != 'N' and op2 != 'y' and op2 != 'Y'):
                    saux = 'Deseja obter mais detalhes sobre alguma sessão? Y(sim)/N(Nao)'
                    saux = 'Nao entendi. ' + saux if k == 1 else saux
                    k = 1
                    print(saux,end=' ')
                    op2 = input()
                    if(op2 == 'y' or op2 == 'Y'):
                        state = "SessionDetails"
                    if(op2 == 'n' or op2 == 'N'):
                        state = "ClientRequest"    
            
            if(option == 3):
                titulo = input("Insira o titulo da sessao: ")
                qtdOp = int(input("Quantas opcoes de votacao ela tem? "))
                opts = []
                for i in range(qtdOp):
                    print('Nome da opcao ', i+1, ': ', end='')
                    opt = input()
                    opts.append(opt)
                comando = ClientRequestCreate(Token=token,FlagCreateSession=True)
                comando.QtdOptions = qtdOp
                comando.Options = opts
                comando.Title = titulo
                commTCPSocket.send(pPacket.encode(comando))
                serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                print('Server ans CR = ',serverAns.Sessions)
                op2 = ''
                k = 0
                while(op2 != 'n' and op2 != 'N' and op2 != 'y' and op2 != 'Y'):
                    saux = 'Deseja obter mais detalhes sobre alguma sessão? Y(sim)/N(Nao)'
                    saux = 'Nao entendi. ' + saux if k == 1 else saux
                    k = 1
                    op2 = input(saux+' ')
                    if(op2 == 'y' or op2 == 'Y'):
                        state = "SessionDetails"
                    if(op2 == 'n' or op2 == 'N'):
                        state = "ClientRequest"  
            
        if(state == "SessionDetails"):
            titulo = input('Digite o titulo da sessao: ')
            comando = SessionDetails(Token=token,Title=titulo)
            commTCPSocket.send(pPacket.encode(comando))
            serverAns = TCPTryReadMessage(commTCPSocket, SessionDescription)
            if serverAns.FlagFinished :
                print(serverAns.Title)
                for i in range(serverAns.QtdOptions):
                    print(serverAns.Options[i])
                state = "ClientRequest"
            else:
                print(serverAns.Title)
                for i in range(serverAns.QtdOptions):
                    print(serverAns.Options[i])
                opt = input('Deseja votar? y/n ')
                if(opt == 'y'):
                    state = 'Vote'
                else:
                    state = 'ClientRequest'

        if(state == "Vote"):
            titulo = input('Qual o titulo da votacao?\n')
            option = input('Qual a opcao?\n')
            comando = Vote(Token=token,Title=titulo, Option=option)
            commTCPSocket.send(pPacket.encode(comando))
            serverAns = TCPTryReadMessage(commTCPSocket, VoteResponse)
            print('Server ans Vt = ',serverAns.Description,'\n',serverAns.Title,'\n',serverAns.Option, sep='')
            state = "question"
        if(state == "question"):
            x = input('Votar de novo? 1(votar de novo) ')
            state = "Vote" if x == '1' else "ClientRequest"

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

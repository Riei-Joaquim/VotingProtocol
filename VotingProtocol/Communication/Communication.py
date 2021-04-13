from VotingProtocol.Communication.ProcessPacket import ProcessPacket
from VotingProtocol.Entities import *
from socket import *
from datetime import datetime
from threading import Thread
import time
import os
import sys
import json
import secrets

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

def hasFields(objBytes, listFields):
    try:
        objDict = json.loads(objBytes.decode('utf-8'))
        for field in listFields:
            if field not in objDict:
                return False
        return True
    except Exception as e:
        print(e)
    return False

def userLogin(usersBase, user, password):
    if user in usersBase:
        if password == usersBase[user]:
            token = secrets.token_hex(512)
            return True, token
    return False, None

def getASession(obj):
    tmpSes = Session(
        Title= obj['Title'],
        QtdOptions= obj['QtdOptions'],
        Options= obj['Options'],
        Timeout= obj['Timeout'],
        )
    tmpSes.VoteNumber = obj['VoteNumber']
    tmpSes.VotePOption = obj['VotePOption']
    tmpSes.Win_tie = obj['Win_tie']
    tmpSes.Result = obj['Result']
    tmpSes.FlagFinished = obj['FlagFinished']
    print(tmpSes.VoteNumber,tmpSes.VotePOption,tmpSes.Win_tie,tmpSes.Result,tmpSes.FlagFinished)
    return tmpSes

def loadSessions():
    try:
        arqSessions = open('sessions.json','r')
        jsonSessions = json.load(arqSessions)
        tmpSessions = jsonSessions['Sessions']
        for ses in tmpSessions:
            lSes.append(getASession(ses))
        #lSes = [getASession(ses) for ses in tmpSessions]
        arqSessions.close()
    except Exception as erro:
        print('Nao consegui abrir o arquivo: erro {}'.format(erro))

def storeSessions():
    saveList = [
        dict(Title= obj.Title,
        QtdOptions= obj.QtdOptions,
        Options= obj.Options,
        Timeout= obj.Timeout,
        VoteNumber= obj.VoteNumber,
        VotePOption= obj.VotePOption,
        Win_tie= obj.Win_tie,
        Result= obj.Result,
        FlagFinished= obj.FlagFinished
        )
        for obj in lSes
    ]
    saveSes = dict(Sessions=saveList)
    saveSes = json.dumps(saveSes, indent=4, sort_keys=False)
    try:
        arqSessions = open('sessions.json','w')
        arqSessions.write(saveSes)
        
        arqSessions.close()
    except Exception as erro:
        print('Nao foi possivel salvar os dados: erro {}'.format(erro))

def alrdExist(name):
    for s in lSes:
        if s.Title == name:
            return True
    return False

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
    data, addr = comm.recvfrom(10240)
    if hasFields(data, ['0', '1', '2']):
        decode = pPacket.decode(data, typeObject)
    else:
        decode = None
    return decode, addr
    
def UDPBroadcastPacket(comm, packet):
    encoded = pPacket.encode(packet)
    comm.sendto(encoded, (DEST_IP, UDP_PORT))
    
def UDPSendSignedPacketTo(comm, packet, signatureKey, IP):
    encoded = pPacket.encode(packet)
    signEncoded = pPacket.signAESPacket(encoded, signatureKey)
    comm.sendto(signEncoded, (IP, UDP_PORT))

def UDPServerRunner(comm, signatureKey):
    print('O servidor UDP está ligado e operante!')
    while True:
        data, addr = UDPReadMessage(comm, HelloServers)
            
        if data is not None:
            hello = HelloClient(ServerAddress=str(getLocalIP()), PublicKey=str(pPacket.getLocalPublicKey()))
            UDPSendSignedPacketTo(comm, hello, signatureKey, addr[0]) 
            print('from ', addr, 'receive', data)

def UDPDiscoverValidsServers(comm, signatureKey):
    hello = None
    while True:
        msg = HelloServers()
        UDPBroadcastPacket(comm, msg)
        packetBytes = UDPTryReceiveMessage(comm)
        if packetBytes is not None and hasFields(packetBytes, ['payload', 'sign']):
            payload = pPacket.verifySignAESPacket(packetBytes, signatureKey)
            ans = pPacket.decode(payload, HelloClient)
            if ans is not None:
                hello = ans
                break
            
    return hello

def UDPTryReceiveMessage(comm):
    try:
        return comm.recv(10240)
    except timeout as e:
        return None

############################################ TCP PROTOCOL ############################################
def TCPClientConnection(comm, addr, pPacketClient, usersData):
    while True:
        message = comm.recv(10240)
        decode = pPacketClient.decode(message, None)
        userToken = None
        if decode is not None:
            if decode["Packet"] == "Client Data":
                clientInfos = ClientData(**decode)
                pPacketClient.setRemotePublicKey(clientInfos.PublicKey)
                isAuth, token = userLogin(usersData, clientInfos.Email, clientInfos.Password)
                ans = EvaluationData(Token=token, FlagAutentication=isAuth)#funcao de autenticar no lugar do TRUE
                comm.send(pPacketClient.encode(ans))
                
                if isAuth:
                    userToken = token

            if decode["Packet"] == "Client Request":
                clientReq = ClientRequest(**decode)

                if userToken != clientReq.Token:
                    continue

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
                clientReq = ClientRequestCreate(**decode)

                if userToken != clientReq.Token:
                    continue

                ans = RequestResponse()
                ans.FlagAvailableSessions = True
                ans.FlagCompletedSessions = False
                sessionAtual = Session(clientReq.Title,clientReq.QtdOptions,clientReq.Options,clientReq.Timeout)
                if(alrdExist(clientReq.Title) == False):
                    lSes.append(sessionAtual)
                    storeSessions()
                temp = getAvailableSessionsName()
                #temp = ['Votacao 1','Melhor filme'] # temp sera substituido pelo vetor de sessions
                ans.QtdSessions = len(temp) #valor temporario,vou ter que consultar o vetor
                ans.Sessions = temp
                comm.send(pPacketClient.encode(ans))
            if decode["Packet"] == "Session Details":

                if userToken != clientReq.Token:
                    continue

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
                        ans.Win_tie = s.Win_tie
                        break

                comm.send(pPacketClient.encode(ans))
            if decode["Packet"] == "Vote":
                clientVote = Vote(**decode)

                if userToken != clientReq.Token:
                    continue

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
            if decode["Packet"] == "Finish Connection":
                print('Fim da conexão')
                break
            print('decode = ',decode)
        else:
            print('DECODE ERA NONE')
            return
        

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
    print(datetime.today())
    #'meuNobre@'
    #'meuNobre@'
    comando = ClientData(Email=email, Password=senha, PublicKey= pPacket.getLocalPublicKey())
    commTCPSocket.send(pPacket.encode(comando))
    serverAns = TCPTryReadMessage(commTCPSocket, EvaluationData)
    #verificar se foi autenticado, se n tenta de novo
    while serverAns is None:
        serverAns = TCPTryReadMessage(commTCPSocket, EvaluationData)
    
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
            print('\n\n#---# Selecione a Requisicao #---#')
            option = int(input('\n\t1(consultar sessoes abertas);\n\t2(consultar sessoes concluidas);\n\t3(criar sessao);\n\t4(sair)\n\nSua escolha: '))
            if(option == 1):
                comando = ClientRequest(Token=token,FlagAvailableSession=True)
                commTCPSocket.send(pPacket.encode(comando))
                serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                while serverAns is None:
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
                while serverAns is None:
                    serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                print('Server ans CR = ',serverAns.Sessions)
                op2 = ''
                k = 0
                while(op2 != 'n' and op2 != 'N' and op2 != 'y' and op2 != 'Y'):
                    saux = 'Deseja obter mais detalhes sobre alguma sessão? Y(sim)/N(Nao)'
                    saux = 'Nao entendi. ' + saux if k == 1 else saux
                    k = 1
                    print(saux,end=' ')
                    op2 = input().lower()
                    #testeboy = op2.lower()
                    print(op2)
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
                #tmOut = input('quando encerra? AAAA/MM/DD H:M\n')
                while True :
                    try:
                        tmOut = input('quando encerra a sessao? AAAA/MM/DD H:M\n')
                        closeDate = datetime.strptime(tmOut, '%Y/%m/%d %H:%M')
                        break
                    except (RuntimeError, TypeError, NameError, ValueError):
                        print('Ocorreu um erro na escolha da data! Tente novamente:\n')

                comando = ClientRequestCreate(Token=token,FlagCreateSession=True)
                comando.QtdOptions = qtdOp
                comando.Options = opts
                comando.Title = titulo
                comando.Timeout = tmOut
                
                print(closeDate)
                commTCPSocket.send(pPacket.encode(comando))
                serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                while serverAns is None:
                    serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                print('Server ans CR = ',serverAns.Sessions)
                op2 = ''
                k = 0
                while(op2 != 'n' and op2 != 'N' and op2 != 'y' and op2 != 'Y'):
                    saux = '\nDeseja obter mais detalhes sobre alguma sessão? Y(sim)/N(Nao)'
                    saux = 'Nao entendi. ' + saux if k == 1 else saux
                    k = 1
                    op2 = input(saux+' ')
                    op2.lower()
                    print(op2)
                    if(op2 == 'y' or op2 == 'Y'):
                        state = "SessionDetails"
                    if(op2 == 'n' or op2 == 'N'):
                        state = "ClientRequest"  
            if(option == 4):
                comando = FinishConnection(Token=token)
                commTCPSocket.send(pPacket.encode(comando))
                commTCPSocket.close()
                break
                
        if(state == "SessionDetails"):
            titulo = input('Digite o titulo da sessao: ')
            comando = SessionDetails(Token=token,Title=titulo)
            commTCPSocket.send(pPacket.encode(comando))
            serverAns = TCPTryReadMessage(commTCPSocket, SessionDescription)
            while serverAns is None:
                    serverAns = TCPTryReadMessage(commTCPSocket, SessionDescription)
            if serverAns.FlagFinished :
                print('\n#---#',serverAns.Title,'#---#')
                
                print('\nResult:')
                for st in serverAns.Result:
                    print('\t',st, sep='')
                
                if len(serverAns.Win_tie) <= 1:
                    print('\nWinner:')
                else:
                    print('\nTie:')

                for st in serverAns.Win_tie:
                    print('\t',st, sep='')

                state = "ClientRequest"
            else:
                print('\n#---#',serverAns.Title,'#---#\n')
                for i in range(serverAns.QtdOptions):
                    print('\t',serverAns.Options[i],sep='')
                print('')
                opt = input('Deseja votar? y/n ').lower()
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
            while serverAns is None:
                    serverAns = TCPTryReadMessage(commTCPSocket, VoteResponse)
            print('Server ans Vt = ',serverAns.Description,'\n',serverAns.Title,'\n',serverAns.Option, sep='')
            state = "question"
        if(state == "question"):
            x = input('Votar de novo? 1(votar de novo) ')
            state = "Vote" if x == '1' else "ClientRequest"

def TCPServerRunner(usersData):
    commTCPSocket = socket(AF_INET, SOCK_STREAM)
    commTCPSocket.bind((TCP_SERVER_NAME, TCP_PORT))
    commTCPSocket.listen(CAPACITY_OF_USERS)

    print("O servidor TCP está ligado e operante!")
    print(lSes)
    loadSessions()
    print(lSes)    
    while True:
        connectionSocket, addr = commTCPSocket.accept()
        pPacketClient = ProcessPacket('RSA', pPacket.RSALocalPrivateKey)
        t = Thread(target=TCPClientConnection, args=(connectionSocket, addr, pPacketClient, usersData)) 
        t.start()

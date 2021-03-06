from VotingProtocol.Communication.ProcessPacket import ProcessPacket
from VotingProtocol.Entities import *
from socket import *
from datetime import datetime
from threading import Thread
import time
import json
import secrets

############################################# UTILS ##############################################
DEST_IP ='255.255.255.255'
UDP_PORT = -1
TCP_PORT = -1
TCP_SERVER_NAME = ''
CAPACITY_OF_USERS = -1
pPacket = ProcessPacket()
lSes = []

def setupPorts(udpPort, tcpPort):
    global TCP_PORT, UDP_PORT
    UDP_PORT = udpPort
    TCP_PORT = tcpPort

def setServerCapabilities(capabilities):
    global CAPACITY_OF_USERS
    CAPACITY_OF_USERS = capabilities

def setSignature(signature, op):
    """
    Setup dos bytes de assinatura no objeto que gerencia a criptografia, que com base na operacao desejada
    sabe que tipo de chave foi passada. 
    """
    pPacket.setSignatureKey(signature, op)

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
        arqSessions = open('VotingProtocol\\data\\sessions.json','r')
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
        arqSessions = open('VotingProtocol\\data\\sessions.json','w')
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
    """
    inicializa e retorna um socket UDP configurado para executar as funcoes do protocolo em sua fase UDP
    tanto da parte do client quanto do servidor.
    """
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
    
def UDPSendSignedPacketTo(comm, packet, IP):
    encoded = pPacket.encode(packet)
    signEncoded = pPacket.signPacket(encoded)
    comm.sendto(signEncoded, (IP, UDP_PORT))

def UDPServerRunner(comm):
    """
    Metodo do servidor, com a rotina de receber pacotes broadcast com 'Hello Servers' criptogrados com uma chave AES e respodem ao remetente
    com um pacote 'Hello Client' assinado com uma chave previamente definida.
    """
    print('O servidor UDP est?? ligado e operante!')
    while True:
        data, addr = UDPReadMessage(comm, HelloServers)
            
        if data is not None:
            hello = HelloClient(ServerAddress=str(getLocalIP()), PublicKey=str(pPacket.getLocalPublicKey()))
            UDPSendSignedPacketTo(comm, hello, addr[0]) 
            print('from ', addr, 'receive', data)

def UDPDiscoverValidsServers(comm):
    """
    Metodo do cliente, utilizando UDP envia broadcasts com 'Hello Servers' periodicamente na rede e recebe pacotes
    'Hello Client' assinados em uma porta previamente definida.
     Essa loop se mantem ate que seja recebido um pacote com assinatura valida, sendo retornado o objeto no payload.
    """
    hello = None
    while True:
        msg = HelloServers()
        UDPBroadcastPacket(comm, msg)
        packetBytes = UDPTryReceiveMessage(comm)
        if packetBytes is not None and hasFields(packetBytes, ['payload', 'sign']):
            payload = pPacket.verifySignPacket(packetBytes)
            if payload is not None:
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
    """
    Metodo do servidor, que representa a conexao de um cliente, recebendo dele requisicoes e dados que seram processados,
    tanto para login do usuario quanto para armazenar votos depositados, sendo respondidos seguindo o fluxo de estados 
    da documentacao, comunicacao utilizando criptografia RSA.
    """
    userToken = None
    while True:
        message = comm.recv(10240)
        decode = pPacketClient.decode(message, None)
        
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
                    ans.QtdSessions = len(temp) 
                    ans.Sessions = temp
                elif(clientReq.FlagCompletedSession):
                    ans.FlagAvailableSessions = False
                    ans.FlagCompletedSessions = True
                    temp = getCompletedSessionsName()
                    ans.QtdSessions = len(temp)
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
                    ans.FlagCreatedSessions = True
                    storeSessions()
                else:
                    ans.FlagCreatedSessions = False
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
                ans.Title = clientVote.Title + ' Not found'
                ans.Option = clientVote.Option + ' Not found'
                ans.FlagComputed = False
                ans.Description = 'Session not found'

                for s in lSes:
                    if s.Title == clientVote.Title:
                        ans.Title = s.Title
                        ans.FlagComputed = s.vote(clientVote.Option)
                        print(ans.FlagComputed)
                        if ans.FlagComputed == True :
                            ans.Option = clientVote.Option
                            ans.Description = 'Sucessfull Vote' 
                        elif (s.FlagFinished):
                            ans.Description = 'Session Closed' 
                        else:
                            ans.Description = 'Option not found'
                        break
                storeSessions()
                comm.send(pPacketClient.encode(ans))     
            if decode["Packet"] == "Finish Connection":
                print('Fim de conexao')
                comm.close()
                break
            print('decode = ',decode)
            #print('to vivo')
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
    """
    Metodo do client, que executa a rotina de votacao, lendo os comandos do usuario no terminal, enviando as requisicoes
    para o servidor via TCP, comunicacao criptograda baseado em RSA. Recebendo as respostas, as processando e exibindo 
    as informacoes correspondentes seguindo o fluxo de estados definidos na documentacao. 
    """
    commTCPSocket = socket(AF_INET, SOCK_STREAM)
    commTCPSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    commTCPSocket.setsockopt(IPPROTO_IP, IP_TTL, 128)
    commTCPSocket.connect((DEST_IP, TCP_PORT))
    commTCPSocket.settimeout(1)
    
    email = input('insira o email: ')
    senha = input('insira a senha: ')
    #print(datetime.today())
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
        comando = ClientData(Email=email, Password=senha, PublicKey= pPacket.getLocalPublicKey())
        commTCPSocket.send(pPacket.encode(comando))
        serverAns = TCPTryReadMessage(commTCPSocket, EvaluationData)
        while serverAns is None:
            serverAns = TCPTryReadMessage(commTCPSocket, EvaluationData)
    
    sessionChosen = ''
    token = serverAns.Token
    time.sleep(2)
    state = "ClientRequest"
    while True:
        if(state == "ClientRequest"):
            print('\n\n#---# Selecione a Requisicao #---#')
            option = input('\n\t1(consultar sessoes abertas);\n\t2(consultar sessoes concluidas);\n\t3(criar sessao);\n\t4(sair)\n\nSua escolha: ')
            while (option != '1' and option != '2' and option != '3' and option != '4'):
                print('Nao entendi a escolha')
                option = input('\n\t1(consultar sessoes abertas);\n\t2(consultar sessoes concluidas);\n\t3(criar sessao);\n\t4(sair)\n\nSua escolha: ')
            if(option == '1'):
                comando = ClientRequest(Token=token,FlagAvailableSession=True)
                commTCPSocket.send(pPacket.encode(comando))
                #print('Eviei')
                serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                while serverAns is None:
                    serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                print('Sessoes disponiveis para votacao = ',serverAns.Sessions)
                op2 = ''
                k = 0
                while(op2 != 'n' and op2 != 'N' and op2 != 'y' and op2 != 'Y'):
                    saux = 'Deseja obter mais detalhes sobre alguma sess??o? Y(sim)/N(Nao)'
                    saux = 'Nao entendi. ' + saux if k == 1 else saux
                    k = 1
                    print(saux, end=' ')
                    op2 = input()
                    if(op2 == 'y' or op2 == 'Y'):
                        state = "SessionDetails"
                    if(op2 == 'n' or op2 == 'N'):
                        state = "ClientRequest"   
            
            if(option == '2'):
                comando = ClientRequest(Token=token,FlagCompletedSession=True)
                commTCPSocket.send(pPacket.encode(comando))
                serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                while serverAns is None:
                    serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                print('Sessoes concluidas = ',serverAns.Sessions)
                op2 = ''
                k = 0
                while(op2 != 'n' and op2 != 'N' and op2 != 'y' and op2 != 'Y'):
                    saux = 'Deseja obter mais detalhes sobre alguma sess??o? Y(sim)/N(Nao)'
                    saux = 'Nao entendi. ' + saux if k == 1 else saux
                    k = 1
                    print(saux,end=' ')
                    op2 = input().lower()
                    #testeboy = op2.lower()
                    #print(op2)
                    if(op2 == 'y' or op2 == 'Y'):
                        state = "SessionDetails"
                    if(op2 == 'n' or op2 == 'N'):
                        state = "ClientRequest"    
            
            if(option == '3'):
                titulo = input("Insira o titulo da sessao: ")
                while True:
                    try:
                        qtdOp = int(input("Quantas opcoes de votacao ela tem? "))
                        break
                    except Exception as erro:
                        print('Digite um numero valido')
                opts = []
                for i in range(qtdOp):
                    print('Nome da opcao ', i+1, ': ', end='')
                    opt = input()
                    opts.append(opt)
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
                
                #print(closeDate)
                commTCPSocket.send(pPacket.encode(comando))
                serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                while serverAns is None:
                    serverAns = TCPTryReadMessage(commTCPSocket, RequestResponse)
                #print('Server ans: \n',serverAns,end='\n\n')
                if(serverAns.FlagCreatedSessions == False):
                    print('\tNao foi possivel criar a sessao. Ja existe uma sessao cadastrada com esse nome\n')
                print('Sessoes disponiveis para votacao = ',serverAns.Sessions)
                op2 = ''
                k = 0
                while(op2 != 'n' and op2 != 'N' and op2 != 'y' and op2 != 'Y'):
                    saux = '\nDeseja obter mais detalhes sobre alguma sess??o? Y(sim)/N(Nao)'
                    saux = 'Nao entendi. ' + saux if k == 1 else saux
                    k = 1
                    op2 = input(saux+' ')
                    op2.lower()
                    #print(op2)
                    if(op2 == 'y' or op2 == 'Y'):
                        state = "SessionDetails"
                    if(op2 == 'n' or op2 == 'N'):
                        state = "ClientRequest"  
            if(option == '4'):
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

                if(serverAns.Title != 'Not found'):
                    sessionChosen = serverAns.Title
                    opt = input('Deseja votar? y/n ').lower()
                    while (opt != 'n' and opt != 'y'):
                        opt = input('Nao entendi! Deseja votar? y/n ').lower()
                    
                    state = 'Vote' if (opt == 'y') else 'ClientRequest'

                else: 
                    state = 'ClientRequest'

        if(state == "Vote"):
            titulo = sessionChosen
            option = input('Qual a opcao?\n')
            comando = Vote(Token=token,Title=titulo, Option=option)
            commTCPSocket.send(pPacket.encode(comando))
            serverAns = TCPTryReadMessage(commTCPSocket, VoteResponse)
            while serverAns is None:
                    serverAns = TCPTryReadMessage(commTCPSocket, VoteResponse)
            print('Server ans Vt = ',serverAns.Description,'\n',serverAns.Title,'\n',serverAns.Option, sep='')
            state = "question"
        if(state == "question"):
            opt = input('Votar de novo? y/n ').lower()
            while (opt != 'n' and opt != 'y'):
                opt = input('Nao entendi! Deseja votar de novo? y/n ').lower()
            state = "Vote" if (opt == 'y') else "ClientRequest"

def TCPServerRunner(usersData):
    """
    Metodo do servidor, estabelece as conexoes TCPs com os clientes, quando um cliente se conectar destina uma thread
    de execucao para processar e responder as requisicoes, comunicacao baseada na chaves RSA trocadas na fase UDP do
    protocolo 
    """
    commTCPSocket = socket(AF_INET, SOCK_STREAM)
    commTCPSocket.bind((TCP_SERVER_NAME, TCP_PORT))
    commTCPSocket.listen(CAPACITY_OF_USERS)

    print("O servidor TCP est?? ligado e operante!")
    print(lSes)
    loadSessions()
    print(lSes)    
    while True:
        connectionSocket, addr = commTCPSocket.accept()
        pPacketClient = ProcessPacket('RSA', pPacket.RSALocalPrivateKey)
        t = Thread(target=TCPClientConnection, args=(connectionSocket, addr, pPacketClient, usersData)) 
        t.start()

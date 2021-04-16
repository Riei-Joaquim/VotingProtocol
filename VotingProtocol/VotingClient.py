from VotingProtocol.Entities import *
import VotingProtocol.Communication.Communication as Comm

def VotingClient(signaturePublicKey:bytes, udpPort:int, TcpPort:int):
    """
    Metodo principal para a execução da rotina de um cliente, no protocolo de votação. 
    """
    # Setup de parametros da rede para a operação do protocolo pelo lado do cliente
    Comm.setupPorts(udpPort, TcpPort) # setup de portas
    Comm.setSignature(signaturePublicKey, 'VERIFY') # setup da public key para verificar a autenticidade e a origem dos pacotes

    CommUDPSocket = Comm.startUDPSocket('CLIENT')
    # Descoberta e validação do servidor
    hello = Comm.UDPDiscoverValidsServers(CommUDPSocket)
    
    #configuracao da conexao com o servidor e definindo a chave publica do servidor para criptografar as mensagens seguintes com RSA
    if hello is not None:
        #print(hello)
        Comm.setupRemoteServer(hello.ServerAddress, hello.PublicKey)
    
    #finalizacao da parte UDP da comunicacao
    CommUDPSocket.close()

    # comunicacao concreta com o servidor, fazendo login, requisicoes de dados e votando, na rotina de cliente
    Comm.TCPClientRunner()

    
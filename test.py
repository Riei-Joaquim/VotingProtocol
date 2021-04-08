
import VotingProtocol

client = VotingProtocol.VotingClient()

client.discoverServers()

"""
from socket import *
from threading import Thread

privatePostalBox = []
publicPostalBox = []

def readMessages(clientSocket): # Essa função funciona dentro de uma thread e permite que um usuário possa enviar mensagens ao servidor e receber as mensagens dele simultaneamente.
    while True:
        message = clientSocket.recv(1024).decode('utf-8')
        print(message)
        #print(message) ##################### TEM QUE PRINTAR A FUNÇÂO DE CORES DIFERENTES #########################
    return


def main():
    serverName = '192.168.0.103'
    serverPort = 12000

    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    clientSocket.setsockopt(IPPROTO_IP, IP_TTL, 128)
    clientSocket.connect((serverName, serverPort))

    t = Thread(target=readMessages, args=(clientSocket,)) # É iniciada uma thread para que um usuário possa, simultaneamente, enviar e receber mensagens.
    t.start()

    while True:
        comando = 'teste'
        clientSocket.send(bytes(comando, "utf-8"))
    return



if __name__ == "__main__":
    main()
"""
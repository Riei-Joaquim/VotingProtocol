from Entities import *
import socket

def waitHServer(my_packet):
    if(my_packet.Packet != 'Evaluation Data'):
        return 'Evaluation Data'
    #checar se foi autenticado
    if(my_packet.FlagAutentication):
        return 'Client Request'
    return 'Client Data'

def main():
    HOST = '127.0.0.1'     # Endereco IP do Servidor, vamos ter que setar ele dependendo do broadcast
    PORT = 5000            # Porta que o Servidor esta
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest = (HOST, PORT)
    tcp.connect(dest)
    msg = input()
    state = 'Client Data'
    Token = None
    while msg != '\x18': #trocar para while True e dar break no fim da conexão
        #aqui vai receber a msg do server
        #my_packet = tcp.recv(1024)
        #tcp.send (bytes(msg,"utf-8"))
        
        if state == 'Client Data':
            my_packet = ClientData()
            email = input('Digite o email')
            password = input('Digite a senha')
            my_packet.Email = email
            my_packet.Password = password
            tcp.send(my_packet)
            state = 'Evaluation Data'
            continue

        if state == 'Evaluation Data':
            my_packet = tcp.recv(1024)
            state = waitHServer(my_packet)
            if state == 'Client Request':
                Token = my_packet.Token
            
        if state == 'Client Request':
            comand = input('Criar sessão: 0\nConsultar sessões abertas: 1\nConsultar sessões fechadas: 1\n')
            if(comand == 0):
                my_packet = ClientRequestCreate()
                my_packet.Token = Token
                my_packet.FlagCreateSession = True
                my_packet.FlagAvailableSession = False
                my_packet.FlagCompletedSession = False
                my_packet.Title = input('Titulo da sessão: ')
                my_packet.Timeout = input('Até quando deve durar a sessão?')
                my_packet.QtdOptions = int (input('Quantidade de opções'))
                my_packet.Options = []
                for i in range(1,my_packet.QtdOptions):
                    my_packet.Options.append(input('nome da opção ',i))


            if(comand == 1):
                my_packet = ClientRequest()
                my_packet.Token = Token
                my_packet.FlagCreateSession = False
                my_packet.FlagAvailableSession = True
                my_packet.FlagCompletedSession = False

            if(comand == 2):
                my_packet = ClientRequest()
                my_packet.Token = Token
                my_packet.FlagCreateSession = False
                my_packet.FlagAvailableSession = False
                my_packet.FlagCompletedSession = True

        msg = input()
    tcp.close()

if __name__ == '__main__':
    main()
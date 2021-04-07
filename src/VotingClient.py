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
    title = None
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
            comand = input('Criar sessão: 0\nConsultar sessões abertas: 1\nConsultar sessões fechadas: 2\nVer detalhes de uma sessão: 3\nEncerrar conexão: 4')
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
                for i in range(my_packet.QtdOptions):
                    my_packet.Options.append(input('nome da opção ',i))
                state = 'Request Response'

            if(comand == 1):
                my_packet = ClientRequest()
                my_packet.Token = Token
                my_packet.FlagCreateSession = False
                my_packet.FlagAvailableSession = True
                my_packet.FlagCompletedSession = False
                state = 'Request Response'

            if(comand == 2):
                my_packet = ClientRequest()
                my_packet.Token = Token
                my_packet.FlagCreateSession = False
                my_packet.FlagAvailableSession = False
                my_packet.FlagCompletedSession = True
                state = 'Request Response'

            if(comand == 3):
                title = input('Titulo da sessão: ')
                my_packet = SessionDetails()
                my_packet.Token = Token
                my_packet.Title = title
                state = 'Session Description'

            if(comand == 4):
                #exit
                print('Até um outro dia!!')
                break

        if state == 'Request Response':
            #recive msg
            my_packet = SessionDescription()
            print(my_packet.Title)
            #verificar se nao deu erro, se der muda o estado
            
            if(my_packet.FlagFinished):
                best = 0.0
                winer = None
                for i in my_packet.Options:
                    g = i.split('=')
                    s = ''
                    for c in g[1]:
                        if c != ' ' || c != '%':
                            s += c
                    s = float(s)
                    winer = i if s > best else winer
                    best = s if s > best else best
                    print(i)
                    wi = winer.split(' = ')
                print('O vencedor foi: ',wi[0])
                state = 'Client Request'
            else:
                for i in my_packet.Options:
                    print(i)
                print('Votação em andamento')
                s = input('Deseja votar? Y/N')
                s = s.lower()
                if(s == 'y'):
                    state = 'Vote'
                else:
                    state = 'Client Request'

            if state == 'Vote':
                title = input('Digite a sessão.')
                option = input('Digite a opção')
                my_packet = Vote()
                my_packet.Token = Token
                my_packet.Title = title
                my_packet.Options = option
                #envia
                #tratar a resposta do voto
                s = input('Deseja votar novamente? Y/N')
                s = s.lower()
                if(s == 'y'):
                    state = 'Vote'
                else:
                    state = 'Client Request'

                

        msg = input()
    tcp.close()

if __name__ == '__main__':
    main()
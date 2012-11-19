#!/usr/bin/python
#coding: utf-8

'''
    Autora: Francielle Costa Salvador
    Data: 16/10/2012
    Trabalho final do curso de "Python para Administradores de Redes Linux".

    Um Programa para execução de comandos remotos em diversos hosts
    simultaneamente. Útil para atualizações e instalação de pacotes nas várias
    máquinas de um laboratório. A comunicação com os hosts remotos (IPs
    definidos no arquivo de configuração - "settings.py") é realizada através
    de uma conexão SSL criptografada com autenticação. Deve ser enviado um
    comando individual via linha de comando ou ser informado um arquivo com
    uma série de comandos. O retorno dos comandos de cada host serão
    armazenados num arquivo a medida que forem executados.
'''

import socket
import ssl
import settings
import subprocess
from datetime import datetime
from time import sleep
import sys
import os


def ssh():
    '''
        Esta função aceita uma conexão onde serão passados os comandos a serem
        executados. Após executar os comandos localmente, outra função será
        chamada para que os resultados sejam retornados.
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.bind(('', settings.PORTACLIENTE))

        print 'Aguardando conexão do "servidor" ... \n\n'

        s.listen(1)
        novo_sock, info_ser = s.accept()
        con_ssl = ssl.wrap_socket(
            novo_sock, server_side=True, certfile="cert.pem",
            keyfile="cert.pem", ssl_version=ssl.PROTOCOL_TLSv1)

        cmd = []
        while True:
            dados = con_ssl.recv(1024)
            if not dados:
                break
            cmd.append(dados)

        #Pega o endereço do "servidor"
        ip_servidor = info_ser[0]

        con_ssl.shutdown(socket.SHUT_RDWR)
        con_ssl.close()

        #Transforma a lista recebida em string
        cmd = ''.join(cmd)
        #Separa a lista a cada quebra de linha
        lst = cmd.split('\n')

        #Forexaomatado o nome do arquivo que irá armazenar os resultados
        #IP DD-MM-YY_H-M-S.log
        arqlog = 'SSH {0}.log'.format(datetime.now().strftime(
            '%d-%m-%Y_%H-%M-%S'))
        arq = open(arqlog, 'wb')

        #Executar os comandos e escrever o resultado num arquivo de Log local
        print 'Executando comandos recebidos ... \n\n'
        saida = ''
        for i in lst:
            if len(i.strip()) != 0:
                p = subprocess.Popen(
                    i, shell=True, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    close_fds=True)
                resultado = p.stdout.read()
                saida = '''Comando: {0}\nResultado: {1}
                    \n\n'''.format(i, resultado)
                arq.write(saida)

        arq.close()

        #Tempo para o servidor abrir a conexão
        sleep(1)

        #Função que vai abrir uma conexão com o "servidor"
        print 'Enviando resultados ... \n\n'
        ssh_resultado(ip_servidor, arqlog)

    except Exception as e:
        sys.stderr.write('Erro: {0}\n'.format(e))


def ssh_resultado(ip, arqlog):
    '''
       Esta função solicita uma conexão com o "servidor" para enviar o(s)
       resultado(s) do(s) comando(s) executado(s) no "cliente". Ela recebe
       como argumentos o IP (para o qual deve retornar os resultados) e o nome
       do arquivo de Log.
    '''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = ssl.wrap_socket(
            s, ca_certs='cert.pem', cert_reqs=ssl.CERT_REQUIRED)
        ssl_sock.connect((ip, settings.PORTASERVIDOR))

        with open(arqlog, 'rb') as a:
            arquivo = a.read(1024)
            while arquivo:
                ssl_sock.send(arquivo)
                arquivo = a.read(1024)

        ssl_sock.close()

    except Exception as e:
        sys.stderr.write('Erro: {0}\n'.format(e))


if __name__ == '__main__':
    euid = os.geteuid()

    if euid != 0:
        print 'Programa não foi chamado como root ...\n\n'
        args = ['sudo', sys.executable] + sys.argv + [os.environ]
        os.execlpe('sudo', *args)

    ssh()

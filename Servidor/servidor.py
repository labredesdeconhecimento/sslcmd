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

import settings
import argparse
import socket
import ssl
from datetime import datetime
from threading import Thread
from Queue import Queue
import sys
import re
import os
from time import sleep


#Número máximo de Threads
MAX = 50


def valida_ip(ip):
    ipRegex = re.compile(
        r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
    if ipRegex.match(ip):
        return True
    else:
        return False


def ssh(cmd, f1, f2, diretorio):
    '''
        Esta função recebe um IP, uma lista de comandos e duas filas. A
        função envia todos os comandos para o IP desejado e retorna os
        resultados.
    '''
    while True:
        ip = f1.get()

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssl_sock = ssl.wrap_socket(
                s, ca_certs='cert.pem', cert_reqs=ssl.CERT_REQUIRED)
            ssl_sock.settimeout(2)
            ssl_sock.connect((ip, settings.PORTACLIENTE))
            ssl_sock.settimeout(None)

            #Transformar a lista de comandos em string para ser enviada
            cmd = ''.join(cmd)

            #Enviando os comandos
            cont = 0
            while cont < len(cmd):
                ssl_sock.send(cmd[cont:cont + 1024])
                cont += 1024

            ssl_sock.close()
            s.close()

            #Se foi estabelecida a conexão e os comandos foram enviados
            #Coloca o IP na fila dos que terão que retornar os resultados
            f2.put(ip)

        except Exception as e:
            try:
                arqlog = '{0} {1}.log'.format(ip, datetime.now().strftime(
                    '%d-%m-%Y_%H-%M-%S'))
                with open('{0}/{1}'.format(diretorio, arqlog), 'wb') as arq:
                    arq.write('''**** Cliente {0} ****\n
                    Não foi possível estabelecer conexão!
                    \nErro : {1}'''.format(ip, e))

            except IOError:
                sys.stderr.write('Houve um erro ao criar arquivo de Log!\n')

        finally:
            f1.task_done()


def ssh_resultado(f2, diretorio):
    '''
        Esta função abre uma conexão para receber os resultados dos comandos
        executados nos "clientes".
    '''
    print 'Aguardando respostas dos "clientes" ... \n\n'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.bind(('', settings.PORTASERVIDOR))

        while True:
            s.listen(1)
            novo_sock, info_cli = s.accept()
            con_ssl = ssl.wrap_socket(
                novo_sock, server_side=True, certfile="cert.pem",
                keyfile="cert.pem", ssl_version=ssl.PROTOCOL_TLSv1)

            ip_cliente = info_cli[0]

            arqlog = '{0} {1}.log'.format(ip_cliente, datetime.now().strftime(
                '%d-%m-%Y_%H-%M-%S'))
            arq = open('{0}/{1}'.format(diretorio, arqlog), 'wb')

            while True:
                dados = con_ssl.recv(1024)
                if not dados:
                    break
                arq.write(dados)

            arq.close()

            f2.get()
            f2.task_done()

        con_ssl.shutdown(socket.SHUT_RDWR)
        con_ssl.close()

    except Exception as e:
            sys.stderr.write('Erro: {0}\n'.format(e))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-c', help='Enviar um único comando via linha de comando', dest='cmd')
    group.add_argument(
        '-a', help='Enviar um arquivo com uma série de comandos', dest='arq')
    args = parser.parse_args()

    #Cria a fila que vai receber todos os IPs válidos e tentar conectar
    #Se conectar vai enviar os comandos para o IP e adicionar o IP na fila2
    fila1 = Queue()

    #Cria a fila que vai receber os IPs dos quais o "servidor" espera a
    #resposta para saber os resultados dos comandos
    fila2 = Queue()

    cmd = []
    #Verifica se o usuário passou um arquivo ou um único comando
    if args.arq:
        try:
            #Ler o arquivo com os comandos e os passa para uma lista
            with open(args.arq, 'rb') as arq:
                for i in arq.readlines():
                    if len(i.strip()) != 0:
                        cmd.append(i)

        except IOError:
            sys.stderr.write('Houve um erro ao abrir o arquivo desejado!\n')
            sys.exit()
    else:
        #Adiciona o único comando numa lista
        cmd.append(args.cmd)

    try:
        #Crie a pasta onde ficarão os Logs recebidos
        caminho = 'LogSSH {0}'.format(datetime.now().strftime(
            '%d-%m-%Y_%H-%M-%S'))
        os.mkdir(caminho)

    except OSError:
        sys.stderr.write('Houve um erro ao criar pasta de Logs!\n')
        sys.exit()

    #Coloca os IPs válidos dentro da fila1
    for i in settings.IP:
        if valida_ip(i):
            fila1.put(i)
        else:
            try:
                arqlog = '{0} {1}.log'.format(i, datetime.now().strftime(
                    '%d-%m-%Y_%H-%M-%S'))
                with open('{0}/{1}'.format(caminho, arqlog), 'wb') as arq:
                    arq.write('IP inválido : {0} !!!'.format(i))

            except IOError:
                sys.stderr.write('Houve um erro ao criar arquivo de Log!\n')

    #Executa as threads para enviar os comandos
    print 'Tentativa de conexão nos "clientes" ...\n\n'
    for i in xrange(MAX):
        worker = Thread(target=ssh, args=(cmd, fila1, fila2, caminho))
        worker.setDaemon(True)
        worker.start()

    #Executa uma thread para chamar a função que pega o resultado retornado
    worker = Thread(target=ssh_resultado, args=(fila2, caminho))
    worker.setDaemon(True)
    worker.start()

    fila1.join()
    fila2.join()

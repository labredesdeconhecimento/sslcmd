Envio de Comandos Remotos com SSL

Autor: Francielle Costa Salvador
Data: 16/10/2012

Descrição:
    Um Programa para execução de comandos remotos em diversos hosts
    simultaneamente. Útil para atualizações e instalação de pacotes nas várias
    máquinas de um laboratório. A comunicação com os hosts remotos é realizada
    através de uma conexão SSL criptografada com autenticação. Poderá ser
    enviado um comando individual via linha de comando ou ser informado um
    arquivo com uma série de comandos. O retorno dos comandos de cada host
    serão armazenados num arquivo a medida que forem executados.
    
Como Usar:
    1 - Configurar o arquivo settings.py do Servidor e do Cliente com as 
    informações corretas. A porta passada para "PORTASERVIDOR" deve ser a
    mesma no settings.py do Cliente e no do Servidor. O mesmo é válido
    para a "PORTACLIENTE".
    
    2 - Caso seja usado um arquivo com a listagem de comandos, este deve 
    seguir o seguinte formato:
    
        comando1
        comando2
        [...]
        comandoN
        
    3 - Execute o cliente.py nos hosts onde se deseja executar os comandos. O
    cliente.py deve ser executado dentro da pasta corrente da aplicação que 
    contém o certificado entre outros arquivos utilizados na execução.
        
        Ex:
            $chmod +x cliente.py
            $./cliente.py
    
    4 - Execute o servidor.py no host de onde se deseja enviar os comandos.
    O servidor.py deve receber o argumento "-c 'comando'" ou o argumento 
    "-a arquivo.txt". O servidor.py deve ser executado dentro da pasta 
    corrente da aplicação que contém o certificado entre outros arquivos 
    utilizados na execução.
        
        Ex:
            $chmod +x servidor.py
            $./servidor.py -c 'comando'
                    ou
            $./servidor.py -a arquivo.txt

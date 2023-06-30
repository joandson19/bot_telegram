import logging
import subprocess
import paramiko
from telegram.ext import Updater, CommandHandler

# Configuração do registro de log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Variaveis

bot_telegram = 'SEU_BOT'

# Variáveis de conexão SSH para olt
olt_host = 'host'
olt_username = 'user'
olt_password = 'pass'

# Variaveis para conexão SSH para o MikroTik
mikrotik_host = 'host'
mikrotik_username = 'user'
mikrotik_password = 'pass'

# Função para tratar o comando /start
def start(update, context):
    message = "Olá! Eu sou um bot da AlagoinhasTelecom.\n\n" \
              "Você pode usar os seguintes comandos:\n" \
              "/ping [host] - Executa um ping para o host especificado.\n" \
              "/mtr [host] - Executa um MTR (traceroute) para o host especificado.\n" \
              "/sinalonu [interface]-[ONU] - Obtém informações ópticas da ONU em uma interface específica."

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# Função para tratar o comando /ping
def ping(update, context):
    # Obtém o endereço IP ou nome do host a partir do comando
    host = context.args[0]

    # Executa o comando de ping no host
    process = subprocess.Popen(['ping', '-c', '5', host], stdout=subprocess.PIPE)
    output, _ = process.communicate()

    # Envia a saída do comando de ping como mensagem de resposta
    context.bot.send_message(chat_id=update.effective_chat.id, text=output.decode('utf-8'))

# Função para tratar o comando /mtr
def mtr(update, context):
    # Obtém o endereço IP ou nome do host a partir do comando
    host = context.args[0]

    # Executa o comando MTR no host
    process = subprocess.Popen(['mtr', '-r', '-c', '5', host], stdout=subprocess.PIPE)
    output, _ = process.communicate()

    # Envia a saída do comando MTR como mensagem de resposta
    context.bot.send_message(chat_id=update.effective_chat.id, text=output.decode('utf-8'))

# Função para tratar o comando /sinalonu
def sinalonu(update, context):
    # Obtém a interface-onu a partir do comando
    interface_onu = context.args[0]
    
    # Verifica se a string contém o caractere '-' e faz o split se for o caso
    if '-' in interface_onu:
        interface, onu = interface_onu.split('-')
        # Remove o traço e adiciona um espaço entre "onu" e o número
        onu = 'onu ' + onu.strip('-')
    else:
        # Se não houver '-', assume que o valor representa apenas a interface e define o número da ONU como 0
        interface = interface_onu
        onu = None

    if onu is None:
        # Retorna uma mensagem informando que o número da ONU precisa ser definido
        message = "Falta definir o número da ONU.\n" \
                  "Favor note que esse comando tem que conter ex: \n" \
                  "1/1/2 exemplo de interface!\n" \
                  "-0 exemplo de onu, sempre separar usando o traço!"
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return

    # Cria uma conexão SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conecta à OLT via SSH
        client.connect(hostname=olt_host, username=olt_username, password=olt_password)

        # Executa o comando na OLT
        command = f'show interface gpon {interface} {onu} optical-info'
        stdin, stdout, stderr = client.exec_command(command)

        # Lê a saída do comando
        output = stdout.read().decode('utf-8')

        # Envia a saída do comando como mensagem de resposta
        context.bot.send_message(chat_id=update.effective_chat.id, text=output)

    except paramiko.AuthenticationException:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Falha na autenticação SSH.')
    except paramiko.SSHException:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Erro na conexão SSH.')
    finally:
        # Fecha a conexão SSH
        client.close()
        
# Função para tratar o comando /pingpppoe
def ping_cliente(update, context):
    # Obtém o nome do cliente a partir do comando
    cliente = context.args[0]

    # Cria uma conexão SSH para o MikroTik
    mikrotik_client = paramiko.SSHClient()
    mikrotik_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conecta ao MikroTik via SSH
        mikrotik_client.connect(hostname=mikrotik_host, username=mikrotik_username, password=mikrotik_password)

        # Executa o comando no MikroTik
        command = f'ping [ppp active get [find name="{cliente}"] address] count=5'
        stdin, stdout, stderr = mikrotik_client.exec_command(command)

        # Lê a saída do comando
        output = stdout.read().decode('utf-8')

        # Envia a saída do comando como mensagem de resposta
        context.bot.send_message(chat_id=update.effective_chat.id, text=output)

    except paramiko.AuthenticationException:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Falha na autenticação SSH (MikroTik).')
    except paramiko.SSHException:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Erro na conexão SSH (MikroTik).')
    finally:
        # Fecha a conexão SSH do MikroTik
        mikrotik_client.close()
        
# Função para tratar o comando /offpppoe
def offpppoe(update, context):
    # Obtém o nome do cliente a partir do comando
    cliente = context.args[0]

    # Configurações de conexão SSH para o MikroTik
    mikrotik_client = paramiko.SSHClient()
    mikrotik_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conecta ao MikroTik via SSH
        mikrotik_client.connect(hostname=mikrotik_host, username=mikrotik_username, password=mikrotik_password)

        # Executa o comando no MikroTik
        command = f'/ppp active remove [find name="{cliente}"]'
        stdin, stdout, stderr = mikrotik_client.exec_command(command)

        # Verifica se a desconexão foi bem-sucedida
        if "error" in stderr.read().decode('utf-8'):
            message = f'Erro ao desconectar o cliente {cliente}.'
        else:
            message = f'O cliente {cliente} foi desconectado com sucesso.'

        # Envia a mensagem de resposta
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    except paramiko.AuthenticationException:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Falha na autenticação SSH (MikroTik).')
    except paramiko.SSHException:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Erro na conexão SSH (MikroTik).')
    finally:
        # Fecha a conexão SSH
        mikrotik_client.close()        
        
def main():
    # Configuração do bot
    updater = Updater(token='bot_telegram', use_context=True)
    dispatcher = updater.dispatcher

    # Registro do handler para o comando /start
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # Registro do handler para o comando /ping
    ping_handler = CommandHandler('ping', ping)
    dispatcher.add_handler(ping_handler)

    # Registro do handler para o comando /mtr
    mtr_handler = CommandHandler('mtr', mtr)
    dispatcher.add_handler(mtr_handler)

    # Registro do handler para o comando /sinalonu
    sinalonu_handler = CommandHandler('sinalonu', sinalonu)
    dispatcher.add_handler(sinalonu_handler)
    
    # Registro do handler para o comando /pingpppoe
    ping_cliente_handler = CommandHandler('pingpppoe', ping_cliente)
    dispatcher.add_handler(ping_cliente_handler)
    
    # Registro do handler para o comando /offpppoe
    offpppoe_handler = CommandHandler('offpppoe', offpppoe)
    dispatcher.add_handler(offpppoe_handler)

    # Iniciar o bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

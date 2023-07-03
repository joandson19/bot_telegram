import logging
import subprocess
import paramiko
import re
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
              "/sinalonu [interface]-[ONU] - Obtém informações ópticas da ONU em uma interface específica. \n" \
              "/pingpppoe [login do pppoe] - Faz um ping no IP do login pppoe e retorna o resultado.\n" \
              "/dig [domínio] - Executa uma consulta DNS para o domínio especificado.\n" \
              "/whois [domínio] - Executa uma consulta WHOIS para o domínio especificado."

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
    # Obtém a interface e número da ONU a partir do comando
    interface_onu = context.args[0]

    # Conecta-se à OLT via SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(olt_host, username=olt_username, password=olt_password)

    # Executa o comando para obter informações ópticas da ONU
    command = f'show interface gpon {interface_onu} onu optical-info'
    _, stdout, _ = ssh_client.exec_command(command)

    # Obtém a saída do comando
    output = stdout.read().decode('utf-8')

    # Fecha a conexão SSH
    ssh_client.close()

    # Envia a saída do comando como mensagem de resposta
    context.bot.send_message(chat_id=update.effective_chat.id, text=output)

# Função para tratar o comando /pingpppoe
def pingpppoe(update, context):
    # Obtém o login do PPPoE a partir do comando
    pppoe_login = context.args[0]

    # Executa o comando de ping no IP do login PPPoE
    process = subprocess.Popen(['ping', '-c', '5', '-I', pppoe_login], stdout=subprocess.PIPE)
    output, _ = process.communicate()

    # Envia a saída do comando de ping como mensagem de resposta
    context.bot.send_message(chat_id=update.effective_chat.id, text=output.decode('utf-8'))

# Função para tratar o comando /dig
def dig_cmd(update, context):
    # Obtém o domínio a partir do comando
    domain = context.args[0]

    # Executa o comando dig para consultar o domínio
    process = subprocess.Popen(['dig', domain], stdout=subprocess.PIPE)
    output, _ = process.communicate()

    # Envia a saída do comando dig como mensagem de resposta
    context.bot.send_message(chat_id=update.effective_chat.id, text=output.decode('utf-8'))

# Função para tratar o comando /whois
def whois_cmd(update, context):
    # Obtém o domínio a partir do comando
    domain = context.args[0]

    # Executa o comando whois para consultar o domínio
    process = subprocess.Popen(['whois', domain], stdout=subprocess.PIPE)
    output, _ = process.communicate()

    # Divide a resposta em partes menores, se necessário
    MAX_MESSAGE_LENGTH = 4096  # Limite de tamanho de mensagem do Telegram
    response_parts = [output[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(output), MAX_MESSAGE_LENGTH)]

    # Envia cada parte da resposta como uma mensagem separada
    for part in response_parts:
        context.bot.send_message(chat_id=update.effective_chat.id, text=part.decode('utf-8'))

# Configuração do bot Telegram
updater = Updater(token=bot_telegram, use_context=True)
dispatcher = updater.dispatcher

# Define os tratadores de comandos
start_handler = CommandHandler('start', start)
ping_handler = CommandHandler('ping', ping)
mtr_handler = CommandHandler('mtr', mtr)
sinalonu_handler = CommandHandler('sinalonu', sinalonu)
pingpppoe_handler = CommandHandler('pingpppoe', pingpppoe)
dig_handler = CommandHandler('dig', dig_cmd)
whois_handler = CommandHandler('whois', whois_cmd)

# Adiciona os tratadores de comandos ao despachante
dispatcher.add_handler(start_handler)
dispatcher.add_handler(ping_handler)
dispatcher.add_handler(mtr_handler)
dispatcher.add_handler(sinalonu_handler)
dispatcher.add_handler(pingpppoe_handler)
dispatcher.add_handler(dig_handler)
dispatcher.add_handler(whois_handler)

# Inicia o bot
updater.start_polling()
updater.idle()

if __name__ == '__main__':
    main()

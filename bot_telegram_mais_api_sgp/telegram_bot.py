import logging
import subprocess
import paramiko
import re
import dns.resolver
import requests
from telegram import ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

# Configuração do registro de log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

ids_autorizados = [id1, id2] # se for liberar apenas 1 id basta deixar [id1] 

# Variaveis
TOKEN = 'token_bot'

# Configurações da API do SGP
URL_CONSULTA_CLIENTE = 'link'
URL_VERIFICA_ACESSO = 'link'
TOKEN_SGP = 'token'
APP_SGP = 'api'

# Variáveis de conexão SSH para olt
olt_host = 'hot'
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
              "/onu [nome da onu] - Obtém informações ópticas da ONU pelo nome. \n" \
              "/pingpppoe [login do pppoe] - Faz um ping no IP do login pppoe e retorna o resultado.\n" \
              "/dig [domínio] - Executa uma consulta DNS para o domínio especificado.\n" \
              "/whois [domínio] - Executa uma consulta WHOIS para o domínio especificado.\n" \
              "/cpf NUMERO - Executa uma consulta basica no contrato do cliente."

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# Função para tratar o comando /dig
def dig(update, context):
    # Obtém o domínio a partir do comando
    domain = context.args[0]

    try:
        # Realiza a consulta DNS do tipo A para o domínio
        records = dns.resolver.resolve(domain, 'A')

        # Obtém os registros de IP encontrados
        ips = [str(record) for record in records]

        # Envia a resposta com os registros de IP
        message = f'Registros de IP para o domínio {domain}:\n' + '\n'.join(ips)
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    except dns.resolver.NXDOMAIN:
        # Envia uma mensagem de erro se o domínio não for encontrado
        message = f'O domínio {domain} não foi encontrado.'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    except dns.resolver.NoAnswer:
        # Envia uma mensagem de erro se não houver resposta para a consulta
        message = f'Não há resposta para a consulta do domínio {domain}.'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    except dns.exception.DNSException:
        # Envia uma mensagem de erro genérico se ocorrer uma exceção na consulta DNS
        message = 'Ocorreu um erro ao processar a consulta DNS.'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# Função para tratar a consulta WHOIS
def whois(update, context):
    # Obtém o domínio a partir do comando
    domain = context.args[0]

    try:
        # Executa a consulta WHOIS
        whois_result = subprocess.check_output(['whois', domain]).decode('utf-8')

        # Define um limite máximo de caracteres para cada mensagem (por exemplo, 4000 caracteres)
        max_characters = 4000

        if len(whois_result) > max_characters:
            # Se o texto exceder o limite, divide-o em várias mensagens
            messages = [whois_result[i:i+max_characters] for i in range(0, len(whois_result), max_characters)]

            # Envia a mensagem inicial informando que o resultado será enviado em partes
            context.bot.send_message(chat_id=update.effective_chat.id, text='O resultado do WHOIS é muito grande. Será enviado em partes.')

            # Envia as mensagens subsequentes com o resultado do WHOIS
            for message in messages:
                context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        else:
            # Se o texto não exceder o limite, envia-o como uma única mensagem
            context.bot.send_message(chat_id=update.effective_chat.id, text=whois_result)

    except subprocess.CalledProcessError:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Ocorreu um erro ao processar a consulta WHOIS.')

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
        
def onu(update, context):
    # Verifica se o argumento do comando foi fornecido
    if len(context.args) == 0:
        message = "Você precisa fornecer o LOGIN do cliente após o comando /onu."
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return
        
    # Obtém o nome do cliente a partir do comando
    cliente = context.args[0]

    # Cria uma conexão SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conecta à OLT via SSH
        client.connect(hostname=olt_host, username=olt_username, password=olt_password)

        # Executa o comando para obter a interface e número da ONU do cliente
        command = 'show interface gpon onu | include ' + cliente
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8')

        # Verifica se o comando retornou algum resultado
        if output:
            # Extrai a interface e número da ONU do resultado
            match = re.search(r'(\d+/\d+/\d+)\s+(\d+)\s+\S+\s+Up', output)
            if match:
                interface = match.group(1)
                onu = match.group(2)

                # Executa o comando para obter o sinal da ONU do cliente
                command = f'show interface gpon {interface} onu {onu} optical-info'
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode('utf-8')

                # Envia a saída do comando como mensagem de resposta
                context.bot.send_message(chat_id=update.effective_chat.id, text=output)
            else:
                message = f'Cliente {cliente} não encontrado.'
                context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        else:
            message = f'Cliente {cliente} não encontrado.'
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    except paramiko.AuthenticationException:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Falha na autenticação SSH.')
    except paramiko.SSHException:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Erro na conexão SSH.')
    finally:
        # Fecha a conexão SSH
        client.close()

## Daqui em diante faz uso da API do SGP
def consultar_cliente_cpf(cpf):
    # Parâmetros para a chamada da API do SGP
    payload = {
        'token': TOKEN_SGP,
        'app': APP_SGP,
        'cpfcnpj': cpf
    }

    try:
        response = requests.post(URL_CONSULTA_CLIENTE, data=payload)
        data = response.json()

        if response.status_code == 200 and 'contratos' in data:
            contratos = data['contratos']
            razao_social = data.get('razaoSocial')
            return contratos, razao_social
        else:
            return None, None

    except requests.exceptions.RequestException as e:
        print('Erro na consulta da API do SGP:', e)
        return None, None

def verificar_acesso(contrato_id):
    # Parâmetros para a chamada da API do SGP
    payload = {
        'token': TOKEN_SGP,
        'app': APP_SGP,
        'contrato': contrato_id
    }

    try:
        response = requests.post(URL_VERIFICA_ACESSO, data=payload)
        data = response.json()

        if response.status_code == 200 and 'status' in data:
            return data
        else:
            return None

    except requests.exceptions.RequestException as e:
        print('Erro na verificação de acesso:', e)
        return None

def consultar_cpf(update, context):
    message = update.message
    command_args = context.args
    chat_id = message.chat.id  # Obtém o ID do usuário

    # Verifica se o ID do usuário está na lista de IDs autorizados
    if chat_id not in ids_autorizados:
        # Usuário não autorizado
        message.reply_text('Você não está autorizado a executar esta função. Entre em contato com o administrador.')
        message.reply_text(f'Seu ID: {chat_id}')
        update.message.delete()
        return
        
    if len(command_args) != 1:
        message.reply_text('Por favor, use o comando no formato /cpf <número do CPF>')
        return

    cpf = command_args[0]
    contratos, razao_social = consultar_cliente_cpf(cpf)

    if contratos is None:
        response = 'Não foi possível consultar os contratos do cliente.'
    else:
        response = 'Contratos do cliente:\n\n'

        for contrato in contratos:
            contrato_id = contrato['contratoId']
            response += f"Razão Social: {contrato['razaoSocial']}\n"
            response += f"Contrato ID: {contrato_id}\n"
            response += f"Plano de serviço: {contrato['servico_plano']}\n"
            response += f"Status: {contrato['contratoStatusDisplay']}\n"

            # Verificar o acesso para o contrato atual
            resultado_acesso = verificar_acesso(contrato_id)
            if resultado_acesso is not None:
                status_acesso = resultado_acesso['msg']

                if status_acesso == 'Serviço Online':
                    response += 'Status de acesso: <b>🟢 Online</b>\n'
                elif status_acesso == 'Serviço Offline':
                    response += 'Status de acesso: <b>🔴 Offline</b>\n'
                else:
                    response += 'Status de acesso: Desconhecido\n'

            response += '\n'

    # Remover a mensagem do CPF do chat se possível
    try:
        context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
    except BadRequest as e:
        print('Erro ao excluir mensagem:', e)

    # Enviar a resposta em uma nova mensagem
    context.bot.send_message(chat_id=message.chat_id, text=response, parse_mode=ParseMode.HTML)

## Aqui finaliza o uso da API do SGP

def main():
    # Configuração do bot
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Registra o handler para o comando /cpf
    cpf_handler = CommandHandler('cpf', consultar_cpf)
    dispatcher.add_handler(cpf_handler)
    
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
    
    # Registro do handler para o comando /onu
    onu_handler = CommandHandler('onu', onu)
    dispatcher.add_handler(onu_handler)
    
    # Registro do handler para o comando /dig
    dig_handler = CommandHandler('dig', dig)
    dispatcher.add_handler(dig_handler)

    # Registro do handler para o comando /whois
    whois_handler = CommandHandler('whois', whois)
    dispatcher.add_handler(whois_handler)


    # Iniciar o bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

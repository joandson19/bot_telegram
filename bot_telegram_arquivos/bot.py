import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Defina a chave de autenticação do bot
AUTH_KEY = "crie_uma_senha"

# Defina o caminho da pasta que você deseja acessar
FOLDER_PATH = "/caminho/da/pasta/"

# Crie uma instância do bot com seu token
bot = telebot.TeleBot('token_bot')

# Variável global para armazenar o arquivo enviado
file_to_confirm = {}

# Lista de IDs de chat dos usuários autorizados
authorized_users = set()

# Handler para o comando /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text="Olá! Bem-vindo ao bot de acesso a arquivos. Use o comando /listar para ver a lista de arquivos.")

# Handler para o comando /listar
@bot.message_handler(commands=['listar'])
def list_files(message):
    if is_user_authorized(message.chat.id):
        files = os.listdir(FOLDER_PATH)
        if files:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for file_name in files:
                button = InlineKeyboardButton(text=file_name, callback_data=f"baixar:{file_name}")
                keyboard.add(button)
            bot.send_message(chat_id=message.chat.id, text="Lista de arquivos:", reply_markup=keyboard)
        else:
            bot.send_message(chat_id=message.chat.id, text="A pasta está vazia.")
    else:
        bot.send_message(chat_id=message.chat.id, text="Você não está autorizado a realizar esta ação.")

# Handler para o comando /baixar
@bot.callback_query_handler(func=lambda call: call.data.startswith('baixar:'))
def download_file(call):
    if is_user_authorized(call.message.chat.id):
        file_name = call.data.split(':')[1]
        file_path = os.path.join(FOLDER_PATH, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                bot.send_document(call.message.chat.id, file)
        else:
            bot.send_message(chat_id=call.message.chat.id, text="Arquivo não encontrado.")
    else:
        bot.send_message(chat_id=call.message.chat.id, text="Você não está autorizado a realizar esta ação.")        

# Handler para receber um arquivo
@bot.message_handler(content_types=['document'])
def receive_file(message):
    if is_user_authorized(message.chat.id):
        file_info = bot.get_file(message.document.file_id)

        # Armazena o arquivo na variável global para confirmação
        file_to_confirm[message.chat.id] = file_info

        # Cria os botõesde confirmação
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_yes = InlineKeyboardButton(text="Sim", callback_data="confirmar")
        button_no = InlineKeyboardButton(text="Não", callback_data="cancelar")
        keyboard.add(button_yes, button_no)

        # Envia a mensagem de confirmação com os botões
        bot.send_message(chat_id=message.chat.id, text="Deseja confirmar o envio do arquivo?", reply_markup=keyboard)
    else:
        bot.send_message(chat_id=message.chat.id, text="Você não está autorizado a realizar esta ação.")

# Handler para processar o callback de confirmação
@bot.callback_query_handler(func=lambda call: call.data in ["confirmar", "cancelar"])
def process_confirmation(call):
    chat_id = call.message.chat.id

    if is_user_authorized(chat_id):
        if chat_id in file_to_confirm:
            file_info = file_to_confirm.pop(chat_id)

            if call.data == "confirmar":
                # Baixa o arquivo
                downloaded_file = bot.download_file(file_info.file_path)

                # Recupera o nome do arquivo
                file_name = file_info.file_path.split('/')[-1]

                # Salva o arquivo na pasta
                file_path = os.path.join(FOLDER_PATH, file_name)
                with open(file_path, 'wb') as file:
                    file.write(downloaded_file)

                bot.send_message(chat_id=chat_id, text="Arquivo salvo com sucesso.")
            else:
                bot.send_message(chat_id=chat_id, text="Envio do arquivo cancelado.")
        else:
            bot.send_message(chat_id=chat_id, text="Não há arquivos para confirmar.")
    else:
        bot.send_message(chat_id=chat_id, text="Você não está autorizado a realizar esta ação.")

# Handler para o comando /autenticar
@bot.message_handler(commands=['autenticar'])
def authenticate(message):
    try:
        argument = message.text.split()[1]  # Obtém o argumento do comando
        if argument == AUTH_KEY:
            # Autenticação bem-sucedida
            authorized_users.add(message.chat.id)
            bot.send_message(chat_id=message.chat.id, text="Autenticação bem-sucedida. Agora você pode enviar arquivos.")
        else:
            # Autenticação falhou
            bot.send_message(chat_id=message.chat.id, text="Autenticação falhou. Tente novamente.")
    except IndexError:
        # Não há argumento no comando
        bot.send_message(chat_id=message.chat.id, text="O comando /autenticar requer um argumento. Por favor, tente novamente.")
        

# Função para verificar se um usuário está autorizado
def is_user_authorized(chat_id):
    return chat_id in authorized_users

# Inicia o bot
bot.polling()
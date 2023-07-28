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


# New global variable to keep track of user's current path
current_path = {}

# Handler for the command /listar
@bot.message_handler(commands=['listar'])
def list_files(message):
    if is_user_authorized(message.chat.id):
        # Get the current path for the user
        path = current_path.get(message.chat.id, FOLDER_PATH)
        files = os.listdir(path)

        if files:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for file_name in files:
                button = InlineKeyboardButton(text=file_name, callback_data=f"baixar:{file_name}")
                keyboard.add(button)
            
            # Add a button for navigating back if the current path is not the root folder
            if path != FOLDER_PATH:
                back_button = InlineKeyboardButton(text="↩️ Voltar", callback_data="voltar")
                keyboard.add(back_button)

            bot.send_message(chat_id=message.chat.id, text="Lista de arquivos:", reply_markup=keyboard)
        else:
            # Folder is empty, show "↩️ Voltar" button to navigate back
            keyboard = InlineKeyboardMarkup(row_width=1)
            back_button = InlineKeyboardButton(text="↩️ Voltar", callback_data="voltar")
            keyboard.add(back_button)
            bot.send_message(chat_id=message.chat.id, text="A pasta está vazia.", reply_markup=keyboard)
    else:
        bot.send_message(chat_id=message.chat.id, text="Você não está autorizado a realizar esta ação.")


# Handler for the command /voltar (to navigate back to the parent folder)
@bot.callback_query_handler(func=lambda call: call.data == "voltar")
def navigate_back_button(call):
    if is_user_authorized(call.message.chat.id):
        user_id = call.message.chat.id
        if user_id in current_path and current_path[user_id] != FOLDER_PATH:
            current_path[user_id] = os.path.dirname(current_path[user_id])  # Go up one level
        list_files(call.message)  # Show the contents of the parent directory
    else:
        bot.send_message(chat_id=call.message.chat.id, text="Você não está autorizado a realizar esta ação.")


# Handler for the command /baixar and navigating into folders
@bot.callback_query_handler(func=lambda call: call.data.startswith('baixar:'))
def download_file_or_navigate(call):
    if is_user_authorized(call.message.chat.id):
        user_id = call.message.chat.id
        data = call.data.split(':')
        action = data[0]
        target = data[1]

        # Handle navigation into folders
        if os.path.isdir(os.path.join(current_path.get(user_id, FOLDER_PATH), target)):
            # Update the current path for the user
            if user_id not in current_path:
                current_path[user_id] = FOLDER_PATH
            current_path[user_id] = os.path.join(current_path[user_id], target)
            list_files(call.message)  # Show the contents of the new directory
            return

        # Handle file download
        if action == 'baixar':
            file_path = os.path.join(current_path.get(user_id, FOLDER_PATH), target)
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
        # Obtém o nome original do arquivo enviado
        file_name = message.document.file_name

        # Armazena o arquivo na variável global para confirmação
        file_to_confirm[message.chat.id] = (file_name, message.document.file_id)

        # Cria os botões de confirmação
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_yes = InlineKeyboardButton(text="Sim", callback_data="confirmar")
        button_no = InlineKeyboardButton(text="Não", callback_data="cancelar")
        keyboard.add(button_yes, button_no)

        # Envia a mensagem de confirmação com os botões
        bot.send_message(chat_id=message.chat.id, text=f"Deseja confirmar o envio do arquivo '{file_name}'?", reply_markup=keyboard)
    else:
        bot.send_message(chat_id=message.chat.id, text="Você não está autorizado a realizar esta ação.")


# Handler para processar o callback de confirmação
@bot.callback_query_handler(func=lambda call: call.data in ["confirmar", "cancelar"])
def process_confirmation(call):
    chat_id = call.message.chat.id

    if is_user_authorized(chat_id):
        if chat_id in file_to_confirm:
            file_name, file_id = file_to_confirm.pop(chat_id)

            if call.data == "confirmar":
                # Baixa o arquivo
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                # Obtém o caminho da pasta onde o arquivo deve ser salvo (usando o current_path)
                current_folder_path = current_path.get(chat_id, FOLDER_PATH)

                # Salva o arquivo na pasta correta com o nome original
                file_path = os.path.join(current_folder_path, file_name)
                with open(file_path, 'wb') as file:
                    file.write(downloaded_file)

                bot.send_message(chat_id=chat_id, text="Arquivo salvo com sucesso.")
            else:
                bot.send_message(chat_id=chat_id, text="Envio do arquivo cancelado.")
        else:
            bot.send_message(chat_id=chat_id, text="Não há arquivos para confirmar.")
    else:
        bot.send_message(chat_id=chat_id, text="Você não está autorizado a realizar esta ação.")

# Handler for the command /autenticar
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

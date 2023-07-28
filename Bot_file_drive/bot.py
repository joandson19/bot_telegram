import os # útil demais, não toque nele
import emoji # útil para adicionar emoji nas pastas
import shutil # Util para apagar diretórios
import telebot # útil demais, não toque nele
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton # útil demais, não toque nele

# Defina a chave de autenticação do bot
AUTH_KEY = "UMA SENHA QUALQUER"

# Pasta raiz onde os usuários terão suas pastas pessoais
ROOT_FOLDER = "SUA PASTA ESCOLHIDA"

# Crie uma instância do bot com seu token
bot = telebot.TeleBot('TOKEN DO BOT')

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

# Função para criar a pasta do usuário
def create_user_folder(user_id):
    user_folder = os.path.join(ROOT_FOLDER, str(user_id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    return user_folder

# Handler para o comando /criarpasta
@bot.message_handler(commands=['criarpasta'])
def create_folder(message):
    if is_user_authorized(message.chat.id):
        try:
            folder_name = message.text.split()[1]  # Obtém o nome da pasta do argumento do comando
            
            # Obtém a pasta atual do usuário
            user_folder = create_user_folder(message.chat.id)
            current_user_folder = current_path.get(message.chat.id, user_folder)

            folder_path = os.path.join(current_user_folder, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                bot.send_message(chat_id=message.chat.id, text=f"Pasta '{folder_name}' criada com sucesso.")
            else:
                bot.send_message(chat_id=message.chat.id, text=f"A pasta '{folder_name}' já existe.")
        except IndexError:
            bot.send_message(chat_id=message.chat.id, text="O comando /criarpasta requer um nome de pasta. Por favor, tente novamente.")
    else:
        bot.send_message(chat_id=message.chat.id, text="Você não está autorizado a realizar esta ação.")

# Handler para o comando /apagar
@bot.message_handler(commands=['apagar'])
def delete_file_or_folder(message):
    if is_user_authorized(message.chat.id):
        # Obtém a pasta atual do usuário
        user_folder = create_user_folder(message.chat.id)
        current_user_folder = current_path.get(message.chat.id, user_folder)

        files = os.listdir(current_user_folder)
        if files:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for item_name in files:
                is_directory = os.path.isdir(os.path.join(current_user_folder, item_name))
                if is_directory:
                    # If it's a directory, add 📁 emoji before the name
                    item_name_with_emoji = f"{emoji.emojize(':file_folder:')} {item_name}"
                else:
                    item_name_with_emoji = item_name

                button = InlineKeyboardButton(text=item_name_with_emoji, callback_data=f"apagar:{item_name}")
                keyboard.add(button)

            bot.send_message(chat_id=message.chat.id, text="Selecione o arquivo ou pasta para apagar:", reply_markup=keyboard)
        else:
            bot.send_message(chat_id=message.chat.id, text="A pasta está vazia. Nada para apagar.")
    else:
        bot.send_message(chat_id=message.chat.id, text="Você não está autorizado a realizar esta ação.")

# Handler para o callback de confirmação de exclusão
@bot.callback_query_handler(func=lambda call: call.data.startswith('apagar:'))
def confirm_delete(call):
    if is_user_authorized(call.message.chat.id):
        user_id = call.message.chat.id
        item_name = call.data.split(':')[1]

        # Obtém a pasta atual do usuário
        user_folder = create_user_folder(user_id)
        current_user_folder = current_path.get(user_id, user_folder)

        item_path = os.path.join(current_user_folder, item_name)
        is_directory = os.path.isdir(item_path)
        confirmation_text = f"Tem certeza que deseja apagar {'a pasta' if is_directory else 'o arquivo'} '{item_name}'?"

        # Cria os botões de confirmação
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_yes = InlineKeyboardButton(text="Sim", callback_data=f"confirmar_apagar:{item_name}")
        button_no = InlineKeyboardButton(text="Não", callback_data="cancelar_apagar")
        keyboard.add(button_yes, button_no)

        bot.send_message(chat_id=call.message.chat.id, text=confirmation_text, reply_markup=keyboard)
    else:
        bot.send_message(chat_id=call.message.chat.id, text="Você não está autorizado a realizar esta ação.")

# Handler para o callback de confirmação final de exclusão
@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_apagar:'))
def process_delete_confirmation(call):
    chat_id = call.message.chat.id

    if is_user_authorized(chat_id):
        item_name = call.data.split(':')[1]

        # Obtém a pasta atual do usuário
        user_folder = create_user_folder(chat_id)
        current_user_folder = current_path.get(chat_id, user_folder)

        item_path = os.path.join(current_user_folder, item_name)
        is_directory = os.path.isdir(item_path)

        if os.path.exists(item_path):
            if is_directory:
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
            bot.send_message(chat_id=chat_id, text=f"{'Pasta' if is_directory else 'Arquivo'} '{item_name}' apagado com sucesso.")
        else:
            bot.send_message(chat_id=chat_id, text=f"{'' if is_directory else 'Arquivo ou'} Pasta '{item_name}' não encontrado.")
    else:
        bot.send_message(chat_id=chat_id, text="Você não está autorizado a realizar esta ação.")

# Handler for the command /listar
@bot.message_handler(commands=['listar'])
def list_files(message):
    if is_user_authorized(message.chat.id):
        # Cria a pasta do usuário se ainda não existir
        user_folder = create_user_folder(message.chat.id)

        # Get the current path for the user
        path = current_path.get(message.chat.id, user_folder)
        files = os.listdir(path)

        if files:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for file_name in files:
                is_directory = os.path.isdir(os.path.join(path, file_name))
                if is_directory:
                    # If it's a directory, add 📁 emoji before the name
                    file_name_with_emoji = f"{emoji.emojize(':file_folder:')} {file_name}"
                else:
                    file_name_with_emoji = file_name

                button = InlineKeyboardButton(text=file_name_with_emoji, callback_data=f"baixar:{file_name}")
                keyboard.add(button)
            
            # Add a button for navigating back if the current path is not the user's folder
            if path != user_folder:
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
        
        # Obtém a pasta do usuário
        user_folder = create_user_folder(user_id)
        
        if user_id in current_path and current_path[user_id] != user_folder:
            current_path[user_id] = os.path.dirname(current_path[user_id])  # Go up one level
        list_files(call.message)  # Show the contents of the parent directory
    else:
        bot.send_message(chat_id=call.message.chat.id, text="Você não está autorizado a realizar esta ação.")


# Handler for the command /baixar and navigating into folders
@bot.callback_query_handler(func=lambda call: call.data.startswith('baixar:'))
def download_file_or_navigate(call):
    if is_user_authorized(call.message.chat.id):
        user_id = call.message.chat.id
        
        # Obtém a pasta do usuário
        user_folder = create_user_folder(user_id)
        
        data = call.data.split(':')
        action = data[0]
        target = data[1]

        # Handle navigation into folders
        if os.path.isdir(os.path.join(current_path.get(user_id, user_folder), target)):
            # Update the current path for the user
            if user_id not in current_path:
                current_path[user_id] = user_folder
            current_path[user_id] = os.path.join(current_path[user_id], target)
            list_files(call.message)  # Show the contents of the new directory
            return

        # Handle file download
        if action == 'baixar':
            file_path = os.path.join(current_path.get(user_id, user_folder), target)
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
            
            # Obtém a pasta do usuário
            user_folder = create_user_folder(chat_id)

            if call.data == "confirmar":
                # Baixa o arquivo
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                # Obtém o caminho da pasta onde o arquivo deve ser salvo (usando o current_path)
                current_user_folder = current_path.get(chat_id, user_folder)

                # Salva o arquivo na pasta correta com o nome original
                file_path = os.path.join(current_user_folder, file_name)
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
            user_id = message.chat.id

            # Cria a pasta do usuário, se ainda não existir
            user_folder = create_user_folder(user_id)

            # Adiciona o usuário à lista de usuários autorizados
            authorized_users.add(user_id)

            # Usuario autorizado
            
            bot.send_message(chat_id=message.chat.id, text="Autenticação bem-sucedida. Agora você pode enviar arquivos.")
            
            # Chama a função para listar os arquivos do usuário
            
            list_files(message)
                        
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
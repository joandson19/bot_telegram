import os
import emoji # útil para adicionar emoji nas pastas
import shutil # Util para apagar diretórios
import telebot
import zipfile
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Defina a chave de autenticação do bot
AUTH_KEY = "SENHA ESCOLHIDA"

# Pasta raiz onde os usuários terão suas pastas pessoais
ROOT_FOLDER = "PASTA ESCOLHIDA"

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

# Handler for the command /baixarpasta
@bot.message_handler(commands=['baixarpasta'])
def list_folders_to_download(message):
    if is_user_authorized(message.chat.id):
        # Cria a pasta do usuário se ainda não existir
        user_folder = create_user_folder(message.chat.id)

        # Get the current path for the user
        path = current_path.get(message.chat.id, user_folder)

        folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]

        if folders:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for folder_name in folders:
                folder_with_emoji = f"{emoji.emojize(':file_folder:')} {folder_name}"
                button = InlineKeyboardButton(text=folder_with_emoji, callback_data=f"baixar_pasta:{folder_name}")
                keyboard.add(button)

            # Add a button for navigating back if the current path is not the user's folder
            if path != user_folder:
                back_button = InlineKeyboardButton(text="↩️ Voltar", callback_data="voltar")
                keyboard.add(back_button)

            bot.send_message(chat_id=message.chat.id, text="Escolha a pasta que deseja baixar:", reply_markup=keyboard)
        else:
            # Folder is empty, show "↩️ Voltar" button to navigate back
            keyboard = InlineKeyboardMarkup(row_width=1)
            back_button = InlineKeyboardButton(text="↩️ Voltar", callback_data="voltar")
            keyboard.add(back_button)
            bot.send_message(chat_id=message.chat.id, text="Não há pastas disponíveis para baixar.", reply_markup=keyboard)
    else:
        bot.send_message(chat_id=message.chat.id, text="Você não está autorizado a realizar esta ação.")


# Handler para processar o callback de escolha de pasta para baixar
@bot.callback_query_handler(func=lambda call: call.data.startswith('baixar_pasta:'))
def download_selected_folder(call):
    if is_user_authorized(call.message.chat.id):
        user_id = call.message.chat.id
        
        # Obtém a pasta do usuário
        user_folder = create_user_folder(user_id)

        folder_name = call.data.split(':')[1]
        folder_path = os.path.join(current_path.get(user_id, user_folder), folder_name)

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Compacta a pasta em um arquivo zip temporário
            temp_zip_path = os.path.join(user_folder, folder_name + ".zip")
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)

            # Envia o arquivo zip para o usuário
            with open(temp_zip_path, 'rb') as zip_file:
                bot.send_document(call.message.chat.id, zip_file)

            # Remove o arquivo zip temporário
            os.remove(temp_zip_path)

            bot.send_message(chat_id=user_id, text=f"Pasta '{folder_name}' baixada com sucesso.")
        else:
            bot.send_message(chat_id=user_id, text=f"A pasta '{folder_name}' não existe ou não é uma pasta.")
    else:
        bot.send_message(chat_id=call.message.chat.id, text="Você não está autorizado a realizar esta ação.")
        
# Dicionário para armazenar temporariamente os itens disponíveis para renomear
items_to_rename = {}

# Handler para o comando /renomear
@bot.message_handler(commands=['renomear'])
def list_items_to_rename(message):
    if is_user_authorized(message.chat.id):
        # Obtém a pasta atual do usuário
        user_folder = create_user_folder(message.chat.id)
        current_user_folder = current_path.get(message.chat.id, user_folder)

        files = os.listdir(current_user_folder)
        items_to_rename[message.chat.id] = {}  # Armazena os itens disponíveis no dicionário

        if files:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for item_name in files:
                is_directory = os.path.isdir(os.path.join(current_user_folder, item_name))
                item_name_with_emoji = f"{emoji.emojize(':file_folder:')} {item_name}" if is_directory else item_name

                # Adjust the file name if it's too long
                MAX_CHARACTERS = 15
                if len(item_name) > MAX_CHARACTERS:
                    truncated_name = item_name[:MAX_CHARACTERS] + "..." + item_name[-4:]
                    items_to_rename[message.chat.id][truncated_name] = item_name  # Armazena a correspondência de nomes
                    item_name_with_emoji = truncated_name

                # Add buttons for renaming each item
                button = InlineKeyboardButton(text=item_name_with_emoji, callback_data=f"escolher_renomear:{item_name_with_emoji}")
                keyboard.add(button)

            bot.send_message(chat_id=message.chat.id, text="Escolha o item que deseja renomear:", reply_markup=keyboard)
        else:
            bot.send_message(chat_id=message.chat.id, text="A pasta está vazia. Nada para renomear.")
    else:
        bot.send_message(chat_id=message.chat.id, text="Você não está autorizado a realizar esta ação.")


# Handler para o callback de escolha do item para renomear
@bot.callback_query_handler(func=lambda call: call.data.startswith('escolher_renomear:'))
def choose_item_to_rename(call):
    if is_user_authorized(call.message.chat.id):
        user_id = call.message.chat.id
        item_name = call.data.split(':')[1]

        # Obtém o nome real do arquivo a partir do dicionário
        real_name = items_to_rename.get(user_id, {}).get(item_name)

        if real_name:
            items_to_rename[user_id] = real_name
            bot.send_message(chat_id=user_id, text=f"Digite o novo nome para '{real_name}':")
        else:
            bot.send_message(chat_id=user_id, text=f"Item '{item_name}' não encontrado para renomear.")
    else:
        bot.send_message(chat_id=call.message.chat.id, text="Você não está autorizado a realizar esta ação.")


# Handler para receber o novo nome do item para renomear
@bot.message_handler(func=lambda message: message.chat.id in items_to_rename and message.text)
def receive_new_name(message):
    if is_user_authorized(message.chat.id):
        user_id = message.chat.id
        new_name = message.text.strip()

        if len(new_name) == 0:
            bot.send_message(chat_id=user_id, text="O novo nome não pode estar vazio.")
            return

        # Obtém o nome real do arquivo a partir do dicionário
        item_name = items_to_rename.get(user_id)

        # Obtém a pasta atual do usuário
        user_folder = create_user_folder(user_id)
        current_user_folder = current_path.get(user_id, user_folder)

        current_path_to_item = os.path.join(current_user_folder, item_name)
        new_path_to_item = os.path.join(current_user_folder, new_name)

        if os.path.exists(current_path_to_item):
            os.rename(current_path_to_item, new_path_to_item)
            bot.send_message(chat_id=user_id, text=f"Item '{item_name}' renomeado para '{new_name}'.")
        else:
            bot.send_message(chat_id=user_id, text=f"Item '{item_name}' não encontrado.")

        # Remove o item da lista de itens para renomear no dicionário
        del items_to_rename[user_id]
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
                    # Adjust the file name if it's too long
                    MAX_CHARACTERS = 15
                    if len(file_name) > MAX_CHARACTERS:
                        file_name = file_name[:MAX_CHARACTERS] + "..." + file_name[-4:]
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

# Handler para receber qualquer tipo de arquivo
@bot.message_handler(content_types=['document', 'photo', 'audio'])
def receive_file(message):
    if is_user_authorized(message.chat.id):
        # Obtém o arquivo enviado
        file_id = None
        file_name = None

        if message.content_type == 'document':
            file_id = message.document.file_id
            file_name = message.document.file_name
        elif message.content_type == 'photo':
            # Para fotos, usa o file_id como nome do arquivo
            file_id = message.photo[-1].file_id
            file_name = file_id + '.jpg'
        elif message.content_type == 'audio':
            # Para áudios, usa o file_id como nome do arquivo
            file_id = message.audio.file_id
            file_name = file_id + '.mp3'

        # Armazena o arquivo na variável global para confirmação
        file_to_confirm[message.chat.id] = (file_name, file_id)

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

Este codigo python permite que você tenha um bot de armazenamento de arquivos que permite você enviar arquivos para uma pasta no seu SO ou baixar dessa mesma pasta para o seu chat.
Nesse bot tem um metodo de autenticação basica com palavra passe.

# Requisitos python3
* pip3 install telebot

Abra o  arquivo bot.py e altere as variaveis .

# Defina a chave de autenticação do bot
* AUTH_KEY = "crie_uma_senha"

# Defina o caminho da pasta que você deseja acessar
* FOLDER_PATH = "/caminho/da/pasta/"

# Crie uma instância do bot com seu token
* bot = telebot.TeleBot('token_bot')

  

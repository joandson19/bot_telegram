# Bot file drive
O Bot_file_drive
é um bot do Telegram que permite aos usuários acessar, gerenciar e compartilhar arquivos de forma simples e conveniente. Com este bot, você pode criar pastas pessoais, enviar e baixar arquivos, bem como navegar entre as pastas para organizar seus dados. Cada usuario deste bot tem sua propria pasta que ao ser criar leva no nome dela o ID do usúario que está usando o bot.

# Funcionalidades Principais
* Autenticação: Antes de começar a usar o bot, é necessário se autenticar com uma chave de acesso para garantir a segurança dos arquivos.
* Listar Arquivos e Pastas: O comando /listar exibirá a lista de arquivos e pastas na pasta pessoal do usuário, permitindo a navegação entre subpastas e retornar à pasta anterior.
* Criar Pastas: Use o comando /criarpasta seguido do nome da pasta para criar uma nova pasta na pasta atual. A pasta será criada dentro da pasta em que você estiver navegando.
* Enviar Arquivos: Basta enviar um arquivo para o bot e ele será salvo na pasta atual do usuário.
* Apagar Arquivos e Pastas: O comando /apagar permite listar os arquivos e pastas na pasta atual e escolher qual deles deseja apagar. O bot solicitará uma confirmação antes de executar a exclusão.

# Requisitos
* Python 3.x
* Bibliotecas Python: os, emoji, shutil, telebot
* Token do Bot Telegram

# Instalação
"Crie uma instância do bot com seu token"
* bot = telebot.TeleBot('SEU_TOKEN_AQUI')
  
# Defina a chave de autenticação do bot:
* AUTH_KEY = "UMA SENHA QUALQUER"

  # Por fim, execute o bot
* python3 bot.py

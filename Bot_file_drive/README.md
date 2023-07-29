# Telegram File Manager Bot
Este repositório contém o código-fonte de um bot do Telegram desenvolvido em Python que funciona como um gerenciador de arquivos simples. O bot permite que os usuários criem pastas, listem arquivos e pastas, baixem arquivos e pastas, apaguem arquivos e pastas, renomeiem arquivos e pastas e enviem arquivos para armazenamento..

# Funcionalidades Principais
* Criação de pastas pessoais para cada usuário
* Listagem de arquivos e pastas em uma pasta específica
* Download de arquivos e pastas em formato zip
* Exclusão de arquivos e pastas
* Renomeação de arquivos e pastas
* Upload de arquivos para armazenamento

# Requisitos
* Python 3.x
* Bibliotecas Python: os, emoji, shutil, telebot
* Token do Bot Telegram

# Instalação
* pip3 install telebot emoji

"Crie uma instância do bot com seu token"
* bot = telebot.TeleBot('SEU_TOKEN_AQUI')
  
# Defina a chave de autenticação do bot:
* AUTH_KEY = "UMA SENHA QUALQUER"

  # Por fim, execute o bot
* python3 bot.py

# Observações:

* O bot requer autenticação para ser utilizado. O comando "/autenticar" seguido da chave de autenticação permitirá o acesso aos recursos do bot.
* Cada usuário terá acesso apenas à sua própria pasta pessoal.
* Arquivos enviados pelos usuários serão salvos na pasta atual do usuário.
* Certifique-se de conceder as permissões necessárias ao bot no grupo ou canal em que ele será utilizado.

# Aviso:
Este bot foi desenvolvido com fins de uso próprio para estudos e de conceitos de programação com a API do Telegram e manipulação de arquivos em Python. Não garantimos a segurança ou escalabilidade completa deste código para uso em produção. Use-o por sua conta e risco.

# Contribuições:
Contribuições são bem-vindas! Se você identificar bugs, melhorias ou novos recursos a serem adicionados, fique à vontade para abrir problemas (issues) ou enviar um pull request.

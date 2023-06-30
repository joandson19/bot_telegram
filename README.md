# bot_telegram

Esse é um script python de bot para o telegram que pode ser usado tanto usando o comando "pip3 telegram_bot" como rodando em container o qual eu considero melhor por ser um container isolado somente para tal função.

Se você já tem o docker instalado e funcional então é só clonar o repositório na pasta desejada, aqui vou usar a /opt 

* cd /opt
* git clone https://github.com/joandson19/bot_telegram.git

Após acesse a parta 

* cd bot_telegram

configure o arquivo telegram_bot.py com os dados necessários nas variáveis e após use os comandos abaixo.

* docker build -t telegram-bot .
* docker run -itd --name telegram-bot telegram-bot

Se você não tem o docker instalado siga o manual de instalação do Docker de acordo ao seu distema operacional.

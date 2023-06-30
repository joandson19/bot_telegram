# bot_telegram

Esse é um script python de bot para o telegram que pode ser usado tanto usando o comando "pip3 telegram_bot" como rodando em container o qual eu considero melhor por ser um container isolado somente para tal função.

Se você já tem o docker instalado e funcional então é só configurar o arquivo telegram_bot.py com os dados necessários na variáveis e após usar os comandos abaixo.

* docker build -t telegram-bot .
* docker run -itd --name telegram-bot telegram-bot

FROM python:3.9-slim

# Instala as dependências do sistema
RUN apt-get update && apt-get install -y \
	ntpdate \
	dnsutils \
	whois \
    iputils-ping \
    mtr \
    openssh-client 
	
# Copia o arquivo do bot Telegram para o diretório /app
COPY telegram_bot.py /app/telegram_bot.py

# Instala as dependências Python especificadas no requirements.txt
RUN pip3 install python-telegram-bot==12.0.0
RUN pip3 install paramiko
RUN pip3 install dnspython
RUN pip3 install requests

# Define o comando padrão para iniciar o bot Telegram
CMD [ "python3", "/app/telegram_bot.py" ]

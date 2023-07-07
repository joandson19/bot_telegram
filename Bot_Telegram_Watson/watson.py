import telebot
import requests

# Importe as bibliotecas necessárias do Watson
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# Configuração do bot do Telegram
bot_token = 'Token do telegram bot'
bot = telebot.TeleBot(bot_token)

# Configuração da API do Watson Text to Speech
apikey = 'chave api'
url = 'a url gerada no ibm watson'

authenticator = IAMAuthenticator(apikey)
text_to_speech = TextToSpeechV1(authenticator=authenticator)
text_to_speech.set_service_url(url)

# Função para converter texto em voz usando a API do Watson
def convert_text_to_speech(text):
    response = text_to_speech.synthesize(text, voice='pt-BR_IsabelaV3Voice', accept='audio/wav')
    audio_file = response.get_result().content

    return audio_file

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Olá! Envie-me um texto e eu vou convertê-lo em voz.')

# Receber mensagens de texto
@bot.message_handler(func=lambda message: True)
def convert_message_to_speech(message):
    text = message.text

    # Converter texto em voz
    audio_file = convert_text_to_speech(text)

    # Enviar o arquivo de áudio ao usuário
    bot.send_audio(message.chat.id, audio_file)

# Iniciar o bot
bot.polling()

import asyncio
from dotenv import load_dotenv
import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

token = os.getenv('YOUR_BOT_TOKEN')


# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем папку для сохранения резюме, если её еще нет
if not os.path.exists("telegram_files"):
    os.makedirs("telegram_files")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Пожалуйста, отправьте ваше резюме в формате PDF или DOC, и мы его получим.")

# Обработчик получения резюме
async def handle_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    chat_id = update.message.chat_id  # Получаем chat_id отправителя
    
    if document and document.mime_type in ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        file_id = document.file_id
        file = await context.bot.get_file(file_id)
        
        # Определяем расширение файла
        file_extension = document.file_name.split('.')[-1]
        
        # Сохраняем файл с именем, соответствующим chat_id
        file_path = os.path.join("telegram_files", f"{chat_id}.{file_extension}")
        
        await file.download_to_drive(file_path)
        
        # Подтверждаем получение резюме и просим дождаться ответа
        await update.message.reply_text(
            "Ваше резюме успешно получено! Пожалуйста, дождитесь ответа. Мы свяжемся с вами через этот чат."
        )
        print('File successefully saved', file_path)
    else:
        await update.message.reply_text("Пожалуйста, отправьте файл в формате PDF или DOC.")

# Асинхронная функция для отправки сообщения пользователю по chat_id
async def send_message_async(chat_id: int, message: str):
    bot = Bot(token=token)
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Сообщение отправлено пользователю {chat_id}: {message}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")


# Синхронная обертка для вызова send_message_async из обычного кода
def send_message(chat_id: int, message: str):
    asyncio.run(send_message_async(chat_id, message))

# Основная функция запуска бота
def main():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    application = Application.builder().token(token).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик для сообщений с документами (резюме)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_resume))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()

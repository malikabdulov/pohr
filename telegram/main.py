from dotenv import load_dotenv
import os
import logging
from telegram import Update
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

# Функция отправки сообщения пользователю по chat_id
async def send_message_to_user(chat_id: int, message: str, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Сообщение отправлено пользователю {chat_id}: {message}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")

# Функция для администраторов, которая вызывается через интерфейс админки
async def admin_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Использование: /send <chat_id> <сообщение>")
        return
    
    # Извлекаем chat_id и сообщение из аргументов команды
    chat_id = int(context.args[0])
    message = " ".join(context.args[1:])
    
    # Отправляем сообщение пользователю
    await send_message_to_user(chat_id, message, context)
    await update.message.reply_text(f"Сообщение отправлено пользователю с chat_id {chat_id}")

# Основная функция запуска бота
def main():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    application = Application.builder().token(token).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик для сообщений с документами (резюме)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_resume))
    
    # Обработчик для команды /send, которую администратор будет использовать для отправки сообщений
    application.add_handler(CommandHandler("send", admin_send_message))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import uuid

TOKEN = "8532102228:AAFZji9fDEgiiSTcQJh485DKhXhEDYVhnz0"
WEB_APP_URL = "https://your-domain.com/web_app.html"  # Замени на свой URL после деплоя

# Хранилище для временных файлов (в продакшене использовать Redis/БД)
user_files = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение с кнопкой Web App"""
    keyboard = [
        [InlineKeyboardButton(
            "🎛️ Открыть аудиоредактор", 
            web_app=WebAppInfo(url=WEB_APP_URL)
        )],
        [InlineKeyboardButton("📖 Инструкция", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎵 *Добро пожаловать в Audio Editor Bot!*\n\n"
        "Я помогу тебе редактировать аудиофайлы прямо в Telegram.\n"
        "Нажми кнопку ниже, чтобы открыть редактор.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет полученный аудиофайл и отправляет ссылку на редактор"""
    file = update.message.audio or update.message.voice or update.message.document
    
    if not file:
        await update.message.reply_text("Пожалуйста, отправь аудиофайл.")
        return
    
    # Создаем уникальный ID для пользователя
    user_id = str(update.effective_user.id)
    file_id = str(uuid.uuid4())
    
    # Скачиваем файл
    file_path = await file.get_file()
    local_path = f"temp_{file_id}.ogg"
    await file_path.download_to_drive(local_path)
    
    # Сохраняем информацию о файле
    if user_id not in user_files:
        user_files[user_id] = {}
    user_files[user_id][file_id] = {
        'path': local_path,
        'name': file.file_name if hasattr(file, 'file_name') else 'audio.ogg'
    }
    
    # Создаем клавиатуру с кнопкой открытия редактора
    editor_url = f"{WEB_APP_URL}?file_id={file_id}&user_id={user_id}"
    keyboard = [[
        InlineKeyboardButton(
            "🎚️ Редактировать аудио",
            web_app=WebAppInfo(url=editor_url)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ Аудиофайл получен!\n"
        "Нажми кнопку ниже, чтобы открыть редактор:",
        reply_markup=reply_markup
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает данные из Web App"""
    data = update.effective_message.web_app_data.data
    import json
    
    try:
        result = json.loads(data)
        
        if result.get('action') == 'processed':
            # Здесь можно сохранить обработанный файл
            await update.message.reply_text(
                "✅ Аудио успешно обработано!\n"
                "Скачать результат можно в редакторе."
            )
        elif result.get('action') == 'error':
            await update.message.reply_text(
                f"❌ Ошибка обработки: {result.get('message', 'Неизвестная ошибка')}"
            )
            
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
*🎵 Audio Editor Bot - Помощь*

*Что можно делать:*
• Изменять скорость воспроизведения
• Менять высоту тона (pitch)
• Обрезать аудио
• Регулировать громкость
• Конвертировать форматы
• Применять эффекты

*Как использовать:*
1. Отправь боту аудиофайл
2. Нажми "Открыть аудиоредактор"
3. Редактируй в визуальном интерфейсе
4. Скачай результат

*Поддерживаемые форматы:* MP3, WAV, OGG, M4A
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def cleanup():
    """Очистка временных файлов (запускать по расписанию)"""
    for user_id in user_files:
        for file_id, file_info in user_files[user_id].items():
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
    user_files.clear()

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.AUDIO, handle_audio))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    print("🤖 Бот запущен...")
    app.run_polling()
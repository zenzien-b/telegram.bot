import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import yt_dlp

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(f"مرحبًا {user.first_name}! أرسل لي رابط أي فيديو أو أغنية وسأحاول تنزيله لك.")
    
def handle_url(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    try:
        ydl = yt_dlp.YoutubeDL({'quiet': True})
        info = ydl.extract_info(url, download=False)
        
        keyboard = [
            [InlineKeyboardButton("جودة عالية", callback_data="1080")],
            [InlineKeyboardButton("جودة متوسطة", callback_data="720")],
            [InlineKeyboardButton("جودة منخفضة", callback_data="480")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text("اختر جودة التنزيل:", reply_markup=reply_markup)
        context.user_data['url'] = url
        
    except Exception as e:
        update.message.reply_text("❌ حدث خطأ، تأكد من الرابط أو حاول لاحقًا.")

def download_video(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    quality = query.data
    url = context.user_data['url']
    
    try:
        query.edit_message_text(text=f"⏳ جاري التنزيل بجودة {quality}p...")
        
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            'outtmpl': 'video.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
        with open(file_path, 'rb') as video_file:
            context.bot.send_video(
                chat_id=query.message.chat_id,
                video=video_file,
                caption=f"✅ تم التنزيل بنجاح بجودة {quality}p"
            )
        
        os.remove(file_path)
        
    except Exception as e:
        query.edit_message_text(text="❌ فشل التنزيل، حاول برابط آخر.")

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_url))
    dp.add_handler(CallbackQueryHandler(download_video))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

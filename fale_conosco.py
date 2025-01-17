from telegram.ext import ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

async def fale_conosco(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe informações de contato e navegação."""
    keyboard = [
        [InlineKeyboardButton("Enviar Mensagem", url="https://wa.me/5511912345678")],
        [InlineKeyboardButton("Voltar ao Menu", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "📞 **Fale Conosco**\n\n"
        "Entre em contato com nosso suporte para tirar dúvidas ou resolver problemas.\n\n"
        "📧 **E-mail:** suporte@strikerbot.com\n"
        "📱 **WhatsApp:** +55 11 91234-5678\n\n"
        "Clique no botão abaixo para nos enviar uma mensagem.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

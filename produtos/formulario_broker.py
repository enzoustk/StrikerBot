from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from constants import CHAT_FORMULARIO
from common import escape_markdown

# Estados do formulário
NOME, BANCA, UNIDADE, USUARIO, SENHA = range(5)

# Inicia o formulário
async def fazer_parte_broker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de cadastro do Broker."""
    if update.callback_query:  # Se for um evento de botão
        await update.callback_query.answer()

    await update.callback_query.message.reply_text(
        "Entre no Broker\n\nSe estiver pronto para começar, envie o seu nome:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_inicio")]])
    )
    return NOME

# Coleta o nome
async def obter_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Coleta o nome do usuário."""
    if update.callback_query:  # Se for um botão "Voltar"
        await update.callback_query.answer()
        context.user_data.pop("nome", None)
        await fazer_parte_broker(update, context)
        return NOME

    if update.message:  # Se for uma mensagem de texto
        context.user_data["nome"] = update.message.text.strip()
        await update.message.reply_text(
            "Digite o valor total de banca que será usado:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_nome")]])
        )
        return BANCA

# Coleta a banca
async def obter_banca(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Coleta o valor da banca."""
    if update.callback_query:  # Se for um botão "Voltar"
        await update.callback_query.answer()
        context.user_data.pop("banca", None)
        await obter_nome(update, context)
        return NOME

    if update.message:  # Se for uma mensagem de texto
        context.user_data["banca"] = update.message.text.strip()
        await update.message.reply_text(
            "Digite agora sua unidade desejada:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_banca")]])
        )
        return UNIDADE

# Coleta a unidade
async def obter_unidade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Coleta a unidade desejada."""
    if update.callback_query:  # Se for um botão "Voltar"
        await update.callback_query.answer()
        context.user_data.pop("unidade", None)
        await obter_banca(update, context)
        return BANCA

    if update.message:  # Se for uma mensagem de texto
        context.user_data["unidade"] = update.message.text.strip()
        await update.message.reply_text(
            "Insira o nome de usuário da conta que usaremos para as operações:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_unidade")]])
        )
        return USUARIO

# Coleta o usuário
async def obter_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Coleta o nome de usuário."""
    if update.callback_query:  # Se for um botão "Voltar"
        await update.callback_query.answer()
        context.user_data.pop("usuario", None)
        await obter_unidade(update, context)
        return UNIDADE

    if update.message:  # Se for uma mensagem de texto
        context.user_data["usuario"] = update.message.text.strip()
        await update.message.reply_text(
            "Insira a senha da conta:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_usuario")]])
        )
        return SENHA

# Coleta a senha e finaliza o cadastro
async def obter_senha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Coleta a senha da conta e finaliza o cadastro."""
    if update.callback_query:  # Se for um botão "Voltar"
        await update.callback_query.answer()
        context.user_data.pop("senha", None)
        await obter_usuario(update, context)
        return USUARIO

    if update.message:  # Se for uma mensagem de texto
        context.user_data["senha"] = update.message.text.strip()

        username_telegram = f"@{update.effective_user.username}" if update.effective_user.username else "Sem username configurado"

        dados = (
            f"📄 *Novo Cadastro Broker:*\n\n"
            f"👤 *Contato (Telegram):* {escape_markdown(username_telegram)}\n"
            f"👤 *Nome:* {escape_markdown(context.user_data['nome'])}\n"
            f"💰 *Banca:* {escape_markdown(context.user_data['banca'])}\n"
            f"🎯 *Unidade:* {escape_markdown(context.user_data['unidade'])}\n"
            f"🔑 *Usuário:* {escape_markdown(context.user_data['usuario'])}\n"
            f"🔒 *Senha:* {escape_markdown(context.user_data['senha'])}"
        )

        await context.bot.send_message(chat_id=CHAT_FORMULARIO, text=dados, parse_mode="Markdown")
        await update.message.reply_text("Obrigado pelo cadastro! Entraremos em contato em breve.")
        return ConversationHandler.END

# Cancela o fluxo
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela o processo de cadastro."""
    await update.message.reply_text("Cadastro cancelado.")
    return ConversationHandler.END

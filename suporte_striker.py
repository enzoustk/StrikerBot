# Bibliotecas Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)

# Imports de módulos do seu projeto
from constants import BOT_TOKEN_PARCIAL, FILE_PATH_DADOS
from produtos.produtos import produtos, produtos_detalhe, produtos_opcao
from produtos.formulario_broker import (
    fazer_parte_broker, cancelar, 
    obter_nome, obter_banca, obter_senha, obter_unidade, obter_usuario
)
from parcial import (
    parcial, 
    processar_botao_parcial, 
    processar_datas_intervalo
)
from grafico import (
    grafico, 
    processar_botao_grafico, 
    processar_tipo_grafico, 

)
from anulador import (
    listar_apostas, anular_aposta, navegar_pagina, fechar_menu, 
    exibir_menu_anular, modificar_placar, definir_placar, atualizar_placar
)
from fale_conosco import fale_conosco

# Importa a função genérica de escolha de liga do common.py
from common import processar_escolha_liga_generico

from apscheduler.schedulers.background import BackgroundScheduler

# ------------------------------------------------------------------------------
#                          Funções Principais
# ------------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe o painel inicial com botões para todas as funções do bot."""
    keyboard = [
        [InlineKeyboardButton("✅ Produtos", callback_data="menu_produtos")],
        [InlineKeyboardButton("📊 Resultados", callback_data="menu_parcial")],
        [InlineKeyboardButton("📈 Gráficos", callback_data="menu_grafico")],
        [InlineKeyboardButton("📞 Fale Conosco", callback_data="menu_fale_conosco")],
        [InlineKeyboardButton("📝 Painel ADM", callback_data="menu_anular")],
        [InlineKeyboardButton("❌ Fechar Menu", callback_data="fechar_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "Bem-vindo ao Striker Bot! 👋\nEscolha uma das opções abaixo para começar:",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        if update.callback_query.data == "menu_produtos":
            await produtos(update, context)
        else:
            await update.callback_query.message.edit_text(
                "Bem-vindo ao Striker Bot! 👋\nEscolha uma das opções abaixo para começar:",
                reply_markup=reply_markup
            )

async def processar_painel_principal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa os botões do painel principal."""
    query = update.callback_query
    await query.answer()

    if query.data == "menu_produtos":
        await produtos(update, context)
    elif query.data == "menu_parcial":
        await parcial(update, context)
    elif query.data == "menu_grafico":
        await grafico(update, context)
    elif query.data == "menu_fale_conosco":
        await fale_conosco(update, context)
    elif query.data == "menu_anular":
        await exibir_menu_anular(update, context)
    elif query.data == "fechar_menu":
        await query.edit_message_text("✅ Menu fechado. Use /start para abrir novamente.")
    elif query.data == "menu_principal":
        await start(update, context)

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde com uma mensagem padrão para entradas desconhecidas."""
    await update.message.reply_text(
        "Olá! 👋\nPara ver os resultados da Striker, basta usar o comando /parcial.\n"
    )

async def voltar_ao_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Redireciona o usuário para o menu principal."""
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def voltar_ao_anterior(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Redireciona o usuário para a página anterior."""
    query = update.callback_query
    await query.answer()

    # Recupera a última página visitada
    if "pilha_navegacao" in context.user_data and context.user_data["pilha_navegacao"]:
        ultima_pagina = context.user_data["pilha_navegacao"].pop()
        if ultima_pagina == "grafico":
            await grafico(update, context)
        elif ultima_pagina == "parcial":
            await parcial(update, context)
    else:
        await start(update, context)

# ------------------------------------------------------------------------------
#                                MAIN
# ------------------------------------------------------------------------------

# Estados do formulário
NOME, BANCA, UNIDADE, USUARIO, SENHA = range(5) 

def main():
    application = Application.builder().token(BOT_TOKEN_PARCIAL).build()

    # ConversationHandler para Cadastro do Broker
    broker_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(fazer_parte_broker, pattern="^join_broker$")],
        states={
            0: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, obter_nome),
                CallbackQueryHandler(fazer_parte_broker, pattern="^voltar_inicio$")
            ],
            1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, obter_banca),
                CallbackQueryHandler(obter_nome, pattern="^voltar_nome$")
            ],
            2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, obter_unidade),
                CallbackQueryHandler(obter_banca, pattern="^voltar_banca$")
            ],
            3: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, obter_usuario),
                CallbackQueryHandler(obter_unidade, pattern="^voltar_unidade$")
            ],
            4: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, obter_senha),
                CallbackQueryHandler(obter_usuario, pattern="^voltar_usuario$")
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )
    application.add_handler(broker_handler)

    # Handlers de Comando
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("parcial", parcial))
    application.add_handler(CommandHandler("grafico", grafico))
    application.add_handler(CommandHandler("anular", listar_apostas))

    # Handlers de menus e callbacks
    application.add_handler(CallbackQueryHandler(start, pattern="^menu_produtos$"))
    application.add_handler(CallbackQueryHandler(processar_painel_principal, pattern="^menu_.*"))
    application.add_handler(CallbackQueryHandler(produtos, pattern="^menu_produtos$"))
    application.add_handler(CallbackQueryHandler(produtos_detalhe, pattern="^produtos_(broker|canal_vip|canal_gratuito)$"))
    application.add_handler(CallbackQueryHandler(produtos_opcao, pattern="^(info|join|faq)_(broker|canal_vip|canal_gratuito)$"))

    # Handler para Parciais (datas etc.)
    application.add_handler(CallbackQueryHandler(processar_botao_parcial, pattern="^parcial_.*"))
    application.add_handler(MessageHandler(filters.Regex(r"^datas_.*"), processar_datas_intervalo, block=False))

    # Handler para Gráficos (tipos de gráfico etc.)
    application.add_handler(CallbackQueryHandler(processar_tipo_grafico, pattern="^grafico_tipo_.*"))
    application.add_handler(CallbackQueryHandler(processar_botao_grafico, pattern="^grafico_.*"))

    # >>> Handler GENÉRICO de escolha de liga (common.py) <<<
    application.add_handler(
        CallbackQueryHandler(
            processar_escolha_liga_generico,
            pattern=r"^liga_(battle|h2h|todas)\|(parcial|grafico)$"
        )
    )

    # Resto: anular, navegar, fechar_menu...
    application.add_handler(CallbackQueryHandler(anular_aposta, pattern=r"^anular_\d+"))
    application.add_handler(CallbackQueryHandler(navegar_pagina, pattern="^pagina_\\d+"))
    application.add_handler(CallbackQueryHandler(fechar_menu, pattern="^fechar_menu$"))
    application.add_handler(CallbackQueryHandler(voltar_ao_anterior, pattern="^voltar_ao_anterior$"))

    # Handlers para "Mudar Placar" e "Anular Apostas"
    application.add_handler(CallbackQueryHandler(modificar_placar, pattern="^modificar_aposta$"))
    application.add_handler(CallbackQueryHandler(definir_placar, pattern=r"^modificar_\d+$"))
    application.add_handler(CallbackQueryHandler(listar_apostas, pattern="^listar_apostas$"))
    application.add_handler(MessageHandler(filters.Regex(r"^\d+x\d+$"), atualizar_placar))

    # Fallback
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
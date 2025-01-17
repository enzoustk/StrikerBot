from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from produtos.navegacao import PRODUTOS_INFO, duvidas_keyboard, duvidas_texto
from produtos.formulario_broker import fazer_parte_broker

# Função para o menu principal de Produtos
async def produtos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe o menu principal de Produtos."""
    keyboard = [
        [InlineKeyboardButton("📈 Broker", callback_data="produtos_broker")],
        [InlineKeyboardButton("💎 Canal VIP", callback_data="produtos_canal_vip")],
        [InlineKeyboardButton("🆓 Canal Gratuito", callback_data="produtos_canal_gratuito")],
        [InlineKeyboardButton("🔙 Voltar ao Menu Principal", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    new_text = "Escolha uma das opções abaixo:"

    if update.callback_query:
        query = update.callback_query
        current_text = query.message.text

        if current_text != new_text:
            await query.message.edit_text(new_text, reply_markup=reply_markup)
        else:
            await query.answer("Menu de produtos já está exibido!")
    else:
        await update.message.reply_text(new_text, reply_markup=reply_markup)

# Função para detalhes de produtos
async def produtos_detalhe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe os detalhes de um produto selecionado."""
    query = update.callback_query
    produto = query.data.replace("produtos_", "")  # Remove o prefixo "produtos_"

    if produto in PRODUTOS_INFO:
        info = PRODUTOS_INFO[produto]
        keyboard = [
            [InlineKeyboardButton(opcao["texto"], callback_data=opcao["callback_data"])]
            for opcao in info["opcoes"]
        ] + [[InlineKeyboardButton("🔙 Voltar", callback_data="menu_produtos")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        new_text = f"{info['titulo']}\n\n{info['descricao']}"
        current_text = query.message.text

        if current_text != new_text:
            await query.message.edit_text(new_text, reply_markup=reply_markup)
        else:
            await query.answer("Opções já exibidas!")
    else:
        await query.message.edit_text("Produto não encontrado! Use /start para reiniciar o menu.")

# Função para gerenciar opções específicas
async def produtos_opcao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa as opções selecionadas em um produto."""
    query = update.callback_query
    callback_parts = query.data.split("_", 1)  # Divide apenas na primeira ocorrência de "_"

    if len(callback_parts) == 2:
        opcao, produto = callback_parts
    else:
        await query.message.edit_text("Opção inválida! Use /start para reiniciar o menu.")
        return

    if produto in PRODUTOS_INFO and opcao in PRODUTOS_INFO[produto]["acoes"]:
        if produto == "broker" and opcao == "join":
            # Chamar a função que inicia o formulário do broker
            await fazer_parte_broker(update, context)
        elif opcao == "faq":
            # Exibir texto de dúvidas com os botões de contato
            reply_markup = InlineKeyboardMarkup(duvidas_keyboard + [[InlineKeyboardButton("🔙 Voltar", callback_data=f"produtos_{produto}")]])
            await query.message.edit_text(duvidas_texto, reply_markup=reply_markup)
        else:
            mensagem = PRODUTOS_INFO[produto]["acoes"][opcao]
            new_text = mensagem
            current_text = query.message.text

            if current_text != new_text:
                await query.message.edit_text(
                    new_text,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 Voltar", callback_data=f"produtos_{produto}")]]
                    )
                )
            else:
                await query.answer("Mensagem já exibida!")
    else:
        await query.message.edit_text("Opção não encontrada! Use /start para reiniciar o menu.")

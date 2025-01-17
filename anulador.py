import logging
import requests
import pandas as pd
from common import calcular_pl
from constants import CHAT_ID
from telegram.ext import ContextTypes
from common import escape_markdown
from constants import FILE_PATH_DADOS
from constants import BOT_TOKEN_PARCIAL, USERS_PERMITIDOS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log no console
    ]
)

def load_apostas():
    """Carrega a planilha de apostas do arquivo em ordem inversa."""
    return pd.read_excel(FILE_PATH_DADOS).iloc[::-1].reset_index(drop=True)

def anular_aposta_por_id(mensagem_id, bot_token, chat_id):
    """
    Anula uma aposta na planilha e edita a mensagem correspondente no canal do Telegram.
    """
    try:
        logging.info("Iniciando a anulação da aposta...")
        logging.info(f"ID da mensagem fornecido: {mensagem_id}")

        # Carregar a planilha
        logging.info(f"Carregando planilha: {FILE_PATH_DADOS}")
        df_apostas = pd.read_excel(FILE_PATH_DADOS)
        logging.info("Planilha carregada com sucesso.")

        # Procurar a aposta pelo ID Mensagem
        aposta_encontrada = df_apostas[df_apostas['ID Mensagem'] == mensagem_id]

        if not aposta_encontrada.empty:
            aposta = aposta_encontrada.iloc[0]
            logging.info(f"Aposta encontrada: {aposta}")

            # Editar mensagem no Telegram
            texto_anulado = (
                f"⚽ Times: {aposta['Time Casa']} x {aposta['Time Fora']}\n"
                f"🏆 Liga: Esoccer Battle - 8 mins play\n"
                f"🎯 Aposta: {aposta['Tipo Aposta']} {aposta['Linha']} ⬇\n"
                f"📈 Odd: {aposta['Odd']}\n\n"
                "♻️ Anulada ♻️"
            )

            sucesso = editar_mensagem_telegram(bot_token, chat_id, mensagem_id, texto_anulado)

            if sucesso:
                logging.info("Mensagem editada com sucesso no Telegram.")

                # Atualizar a planilha
                df_apostas.loc[df_apostas['ID Mensagem'] == mensagem_id, 'P/L'] = 0
                df_apostas.loc[df_apostas['ID Mensagem'] == mensagem_id, 'Anulada'] = 'Sim'
                df_apostas.to_excel(FILE_PATH_DADOS, index=False)
                logging.info("Planilha atualizada com sucesso.")
                return True
            else:
                logging.error("Erro ao editar a mensagem no Telegram.")
        else:
            logging.warning("Aposta não encontrada na planilha com o ID fornecido.")

        return False

    except Exception as e:
        logging.exception(f"Erro ao anular aposta: {e}")
        return False

def editar_mensagem_telegram(bot_token, chat_id, mensagem_id, texto_mensagem):
    """
    Edita uma mensagem no canal do Telegram.
    """
    try:
        logging.info(f"Tentando editar a mensagem {mensagem_id} no canal {chat_id}...")
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        params = {
            "chat_id": chat_id,
            "message_id": mensagem_id,
            "text": texto_mensagem,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=params)

        if response.status_code == 200:
            logging.info("Mensagem editada com sucesso no Telegram.")
            return True
        else:
            logging.error(f"Erro ao editar a mensagem: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logging.exception(f"Erro ao editar mensagem no Telegram: {e}")
        return False

async def exibir_menu_anular(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe o menu do Painel ADM com as opções de Mudar Placar e Anular Apostas."""
    query = update.callback_query
    await query.answer()

    # Teclado com os dois botões
    keyboard = [
        [InlineKeyboardButton("🔄 Mudar o Placar", callback_data="modificar_aposta")],  # Atualizado para coincidir com o handler
        [InlineKeyboardButton("❌ Anular Apostas", callback_data="listar_apostas")],  # Atualizado para coincidir com o handler
        [InlineKeyboardButton("⬅ Voltar", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("🛠️ Painel ADM - Escolha uma opção:", reply_markup=reply_markup)

async def anular_aposta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Capturar o índice da aposta do callback_data
    _, index = query.data.split("_")
    index = int(index)

    # Carregar apostas do contexto e validar
    df_apostas = pd.DataFrame(context.user_data['apostas'])
    if index < len(df_apostas):
        aposta = df_apostas.iloc[index]
        mensagem_id = aposta['ID Mensagem']

        if not pd.isna(mensagem_id):
            # Chamar a função de anulação
            sucesso = anular_aposta_por_id(mensagem_id, BOT_TOKEN_PARCIAL, CHAT_ID)

            if sucesso:
                await query.edit_message_text(f"Aposta anulada com sucesso.")
            else:
                await query.edit_message_text("Falha ao anular a aposta. Verifique os logs.")
        else:
            await query.edit_message_text("ID da mensagem inválido.")
    else:
        await query.edit_message_text("Aposta não encontrada.")

async def listar_apostas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe as últimas apostas ao digitar /anular ou clicar no botão correspondente."""
    user_id = update.effective_user.id
    if user_id in USERS_PERMITIDOS:
        df_apostas = load_apostas()
        context.user_data['pagina'] = 0
        context.user_data['apostas'] = df_apostas.to_dict(orient="records")
        # Função de escape no envio
        mensagem, teclado = criar_menu_apostas(df_apostas, 0)
        mensagem = escape_markdown(mensagem)

        if update.message:
            # Chamada por comando
            await update.message.reply_text(mensagem, reply_markup=teclado, parse_mode="Markdown")
        elif update.callback_query:
            # Chamada por botão
            await update.callback_query.message.edit_text(mensagem, reply_markup=teclado, parse_mode="Markdown")
    else:
        resposta = "❌ Você não tem permissão para anular apostas."
        if update.message:
            await update.message.reply_text(resposta)
        elif update.callback_query:
            await update.callback_query.message.edit_text(resposta)

async def navegar_pagina(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Obter página solicitada
    pagina = int(query.data.split('_')[1])
    df_apostas = load_apostas()

    # Criar a mensagem e escapar os caracteres
    mensagem, teclado = criar_menu_apostas(df_apostas, pagina)
    mensagem = escape_markdown(mensagem)

    # Enviar mensagem formatada
    await query.edit_message_text(mensagem, reply_markup=teclado, parse_mode="Markdown")

async def fechar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.delete()

async def mudar_placar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lógica para mudar o placar (em construção)."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ Função de Mudar o Placar em desenvolvimento.")

async def modificar_placar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Exibe as apostas para selecionar qual terá o placar modificado.
    """
    user_id = update.effective_user.id
    if user_id in USERS_PERMITIDOS:
        df_apostas = load_apostas()
        context.user_data['pagina'] = 0
        context.user_data['apostas'] = df_apostas.to_dict(orient="records")
        mensagem, teclado = criar_menu_apostas(df_apostas, 0, "modificar_")
        mensagem = escape_markdown(mensagem)

        if update.message:
            await update.message.reply_text(mensagem, reply_markup=teclado, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.edit_text(mensagem, reply_markup=teclado, parse_mode="Markdown")
    else:
        resposta = "❌ Você não tem permissão para modificar placares."
        if update.message:
            await update.message.reply_text(resposta)
        elif update.callback_query:
            await update.callback_query.message.edit_text(resposta)

async def definir_placar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Recebe o novo placar e atualiza a aposta correspondente.
    """
    query = update.callback_query
    await query.answer()

    # Capturar o índice da aposta selecionada
    _, index = query.data.split("_")
    index = int(index)

    # Armazenar índice no contexto
    context.user_data['index_modificar'] = index

    await query.edit_message_text(
        "Digite o novo placar no formato `2x1` (2 gols mandante, 1 visitante):",
        parse_mode="Markdown"
    )

async def atualizar_placar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa a entrada do placar, atualiza a planilha e a mensagem do Telegram.
    """
    if update.message:
        novo_placar = update.message.text
        user_id = update.effective_user.id

        if user_id in USERS_PERMITIDOS:
            try:
                # Validar o formato do placar
                if "x" not in novo_placar:
                    raise ValueError("Formato inválido. Use o formato `2x1`.")

                home_score, away_score = map(int, novo_placar.split("x"))
                index = context.user_data.get('index_modificar')

                if index is not None:
                    # Carregar apostas e encontrar a aposta correspondente
                    df_apostas = load_apostas()
                    aposta = df_apostas.iloc[index]
                    mensagem_id = aposta['ID Mensagem']

                    # Calcular novo P/L
                    tipo_aposta = 'over' if 'Over' in aposta['Tipo Aposta'] else 'under'
                    handicap = aposta['Linha']
                    odd = aposta['Odd']
                    novo_pl = calcular_pl(tipo_aposta, handicap, odd, home_score, away_score)

                    # Atualizar planilha
                    novo_placar_texto = f"{home_score}-{away_score}"
                    df_apostas.loc[index, 'Placar Final'] = novo_placar_texto
                    df_apostas.loc[index, 'P/L'] = novo_pl
                    df_apostas.to_excel(FILE_PATH_DADOS, index=False)

                    # Determinar emojis para o P/L
                    emoji = ""
                    if aposta['Anulada'] == 'sim':
                        emoji = "Anulada 🔄"
                    elif novo_pl == -1:
                        emoji = "❌"
                    elif novo_pl == 0:
                        emoji = "🔄"
                    elif novo_pl == -0.5:
                        emoji = "🔄❌"
                    elif 0 < novo_pl < 0.65:
                        emoji = "🔄✅"
                    elif novo_pl >= 0.65:
                        emoji = "✅✅✅"

                    # Determinar mensagem de "Fogo EV"
                    ev_message = ""
                    if aposta['Fogo EV'] == 1:
                        ev_message = "🔥"
                    elif aposta['Fogo EV'] == 2:
                        ev_message = "🔥🔥"
                    elif aposta['Fogo EV'] == 3:
                        ev_message = "🔥🔥🔥"
                    elif aposta['Fogo EV'] == 4:
                        ev_message = "🔥🔥🔥🔥"

                    # Construir texto da mensagem
                    jogador_casa = aposta['Time Casa']
                    jogador_fora = aposta['Time Fora']
                    direcao_aposta = "⬆" if "Over" in aposta['Tipo Aposta'] else "⬇"
                    ev_section = f"⚠️ *EV*: {ev_message}\n" if aposta['Fogo EV'] > 0 else ""

                    texto_mensagem = (
                        f"⚽ Times: {jogador_casa} x {jogador_fora}\n"
                        f"🏆 Liga: Esoccer Battle - 8 mins play\n"
                        f"🎯 Aposta: {aposta['Tipo Aposta']} {handicap} {direcao_aposta}\n"
                        f"📈 Odd: {odd}\n"
                        f"{ev_section}\n"
                        f"{emoji}\n\n"
                        f"➡ Resultado: {novo_placar_texto}"
                    ).strip()

                    # Sanitizar texto para MarkdownV2
                    for char in ['.', '-', '(', ')', '|', '#', '_']:
                        texto_mensagem = texto_mensagem.replace(char, f"\\{char}")

                    # Editar mensagem no Telegram
                    url_telegram = f"https://api.telegram.org/bot{BOT_TOKEN_PARCIAL}/editMessageText"
                    params = {
                        "chat_id": CHAT_ID,
                        "message_id": mensagem_id,
                        "text": texto_mensagem,
                        "parse_mode": "MarkdownV2",
                        "disable_web_page_preview": True
                    }
                    response = requests.post(url_telegram, data=params)

                    if response.status_code == 200:
                        await update.message.reply_text("✅ Placar atualizado com sucesso!")
                    else:
                        await update.message.reply_text("❌ Erro ao editar mensagem no Telegram.")
                else:
                    await update.message.reply_text("❌ Aposta não encontrada.")
            except Exception as e:
                await update.message.reply_text(f"Erro ao processar: {e}")
        else:
            await update.message.reply_text("❌ Você não tem permissão para modificar placares.")

def criar_menu_apostas(df, pagina, prefixo_callback="anular_"):
    """
    Cria a mensagem formatada e os botões de navegação/anulação/modificação.
    """
    inicio = pagina * 5
    fim = inicio + 5
    apostas_exibidas = df.iloc[inicio:fim]

    mensagem = "Últimas Apostas:\n\n"
    for i, row in apostas_exibidas.iterrows():
        horario_envio = pd.to_datetime(row['Horário Envio'], errors='coerce')
        hora_envio = horario_envio.strftime("%H:%M") if pd.notna(horario_envio) else "N/A"
        placar_final = row.get('Placar Final', 'N/A')

        mensagem += (
            f"{i+1}. {hora_envio} | {row['Time Casa']} x {row['Time Fora']}\n"
            f"🎯 {row['Tipo Aposta']} {row['Linha']} | Placar: {placar_final}\n"
            "———————\n"
        )

    botoes_anular = [
        InlineKeyboardButton(f"{i+1}", callback_data=f"{prefixo_callback}{i}")
        for i in range(inicio, min(fim, len(df)))
    ]

    botoes_navegacao = []
    if pagina > 0:
        botoes_navegacao.append(InlineKeyboardButton("⬅ Página Anterior", callback_data=f"pagina_{pagina-1}"))
    botoes_navegacao.append(InlineKeyboardButton("Fechar Menu", callback_data="fechar_menu"))
    if fim < len(df):
        botoes_navegacao.append(InlineKeyboardButton("Próxima Página ➡", callback_data=f"pagina_{pagina+1}"))

    return mensagem, InlineKeyboardMarkup([botoes_anular, botoes_navegacao])

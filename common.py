#common.py

import re
import pandas as pd
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from constants import PLANILHA_BATTLE_8_PATH, PLANILHA_H2H_8_PATH, LIGA_LABELS


def load_planilha_battle():
    """Carrega a versão mais recente da planilha Battle 8"""
    return pd.read_excel(PLANILHA_BATTLE_8_PATH)

def load_planilha_h2h():
    """Carrega a versão mais recente da planilha H2H"""
    return pd.read_excel(PLANILHA_H2H_8_PATH)

def escape_markdown(text):
    """
    Escapa apenas os caracteres necessários para o Markdown padrão do Telegram.
    """
    return text.translate(str.maketrans({
        "*": r"\*", "_": r"\_", "[": r"\[", "]": r"\]", "`": r"\`"
    }))

def filter_by_current_month(file_path):
    df = pd.read_excel(file_path)
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'], format='%Y-%m-%d %H:%M:%S')
    current_month = datetime.now().month
    current_year = datetime.now().year
    return df[(df['Horário Envio'].dt.month == current_month) & 
              (df['Horário Envio'].dt.year == current_year) & 
              (df['Anulada'] != 'Sim')]

def filter_by_custom_range(file_path, start_date, end_date):
    """Filtra os dados com entrada DD/MM e ajusta o ano automaticamente."""
    try:
        current_year = datetime.now().year
        start_date = pd.to_datetime(f"{start_date}/{current_year}", format='%d/%m/%Y')
        end_date = pd.to_datetime(f"{end_date}/{current_year}", format='%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise ValueError("Formato inválido! Use o formato DD/MM para as datas.")
    
    df = pd.read_excel(file_path)
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'], format='%Y-%m-%d %H:%M:%S')
    df = df[(df['Horário Envio'] >= start_date) & 
            (df['Horário Envio'] <= end_date) & 
            (df['Anulada'] != 'Sim')]
    return df

def botao_voltar_menu():
    """Cria o botão para voltar ao menu principal."""
    return InlineKeyboardButton("🔙 Menu Principal", callback_data="voltar_ao_menu")

def botao_voltar_anterior():
    """Cria o botão para voltar à página anterior."""
    return InlineKeyboardButton("🔙 Voltar", callback_data="voltar_ao_anterior")

def adicionar_a_pilha(context, pagina_atual):
    """Adiciona a página atual à pilha de navegação."""
    if "pilha_navegacao" not in context.user_data:
        context.user_data["pilha_navegacao"] = []
    if not context.user_data["pilha_navegacao"] or context.user_data["pilha_navegacao"][-1] != pagina_atual:
        context.user_data["pilha_navegacao"].append(pagina_atual)

def remover_da_pilha(context):
    """Remove a última página da pilha de navegação."""
    if "pilha_navegacao" in context.user_data and context.user_data["pilha_navegacao"]:
        return context.user_data["pilha_navegacao"].pop()
    return None

def pegar_pagina_atual(context):
    """Recupera a página atual sem removê-la da pilha de navegação."""
    if "pilha_navegacao" in context.user_data and context.user_data["pilha_navegacao"]:
        return context.user_data["pilha_navegacao"][-1]
    return None

def calcular_pl(tipo_aposta, handicap, odd, home_score, away_score):
    valor_apostado = 1
    total_gols = home_score + away_score

    if tipo_aposta.lower() == 'over':
        ajuste_resultado = total_gols - handicap
    elif tipo_aposta.lower() == 'under':
        ajuste_resultado = handicap - total_gols
    else:
        raise ValueError("Tipo de aposta deve ser 'over' ou 'under'")

    if ajuste_resultado >= 0.5:
        return (odd - 1) * valor_apostado
    elif ajuste_resultado == 0.25:
        return (odd - 1) * valor_apostado / 2
    elif ajuste_resultado == 0:
        return 0
    elif ajuste_resultado == -0.25:
        return -0.5 * valor_apostado
    elif ajuste_resultado <= -0.5:
        return -1 * valor_apostado

async def exibir_menu_ligas(update: Update, context: ContextTypes.DEFAULT_TYPE, fluxo: str) -> None:
    """
    Exibe o menu de seleção de ligas (Battle, H2H, Todas).
    :param fluxo: Identifica qual fluxo chamou a seleção de liga (por ex.: "parcial", "grafico").
                  Isso será embutido no callback_data para sabermos para onde ir depois.
    """
    keyboard = [
        [InlineKeyboardButton("Battle 8min", callback_data=f"liga_battle|{fluxo}")],
        [InlineKeyboardButton("H2H GG 8min", callback_data=f"liga_h2h|{fluxo}")],
        [InlineKeyboardButton("Todas", callback_data=f"liga_todas|{fluxo}")],
        [InlineKeyboardButton("Voltar", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        # Se vier de um comando /parcial ou /grafico
        await update.message.reply_text("Escolha a liga desejada:", reply_markup=reply_markup)
    elif update.callback_query:
        # Se vier de um botão
        await update.callback_query.message.edit_text("Escolha a liga desejada:", reply_markup=reply_markup)

async def processar_escolha_liga_generico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler genérico que processa a escolha de liga para qualquer fluxo:
    "parcial", "grafico", etc.

    Espera callback_data no formato: liga_{battle|h2h|todas}|{fluxo}
      Ex.: "liga_battle|parcial"
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data  # Ex: "liga_battle|parcial"
    # Regex para capturar (battle|h2h|todas) e (parcial|grafico)
    match = re.match(r"^liga_(battle|h2h|todas)\|(parcial|grafico)$", callback_data)
    if not match:
        await query.edit_message_text("❌ Escolha de liga ou fluxo inválido.")
        return

    liga_escolhida, fluxo = match.groups()  # Ex.: ("battle", "parcial")
    context.user_data["liga"] = liga_escolhida  # Salva a liga no user_data

    # Dependendo do fluxo, chamamos a função apropriada
    if fluxo == "parcial":
        from parcial import processar_menu_data
        await processar_menu_data(update, context)
    elif fluxo == "grafico":
        from grafico import exibir_menu_data_grafico
        await exibir_menu_data_grafico(update, context)

def get_dataframe_by_liga(context):
    liga = context.user_data.get("liga")
    
    if liga == "battle":
        return load_planilha_battle()
    elif liga == "h2h":
        return load_planilha_h2h()
    else:
        return pd.concat([load_planilha_battle(), load_planilha_h2h()], ignore_index=True)  

def get_liga_name(context):
    """
    Retorna o nome amigável da liga, com base em context.user_data["liga"].
    Ex.: "battle" -> "Battle 8min", "h2h" -> "H2H GG 8min", etc.
    """
    liga_key = context.user_data.get("liga", "")
    return LIGA_LABELS.get(liga_key, "Desconhecida")
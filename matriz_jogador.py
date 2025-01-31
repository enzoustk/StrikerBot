# matriz_jogador.py

import re
import pandas as pd
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from common import (
    get_dataframe_by_liga,
    get_liga_name,
    botao_voltar_anterior,
    escape_markdown
)

# ---------------------------------------------------------------------------
# Passo 1: Escolha de Data
# ---------------------------------------------------------------------------
async def processar_menu_data_jogador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Chamado após o usuário escolher a liga (fluxo="jogador").
    Exibe o menu de seleção de datas (Hoje, Ontem, etc.),
    tal como em parcial.py.
    """
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Hoje", callback_data="jogador_hoje")],
        [InlineKeyboardButton("Mês Atual", callback_data="jogador_mes")],
        [
            InlineKeyboardButton("Ontem", callback_data="jogador_ontem"),
            InlineKeyboardButton("Últ. 7d", callback_data="jogador_7d")
        ],
        [
            InlineKeyboardButton("Mês Anterior", callback_data="jogador_mes_anterior"),
            InlineKeyboardButton("Outra Data", callback_data="jogador_intervalo")
        ],
        [InlineKeyboardButton("Voltar", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(
        "Escolha o período para Saldo por Jogador:",
        reply_markup=reply_markup
    )


async def processar_botao_jogador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa o callback_data do tipo 'jogador_hoje', 'jogador_ontem', etc.
    Armazena o dataframe filtrado no user_data e chama a função
    que pergunta o tipo de aposta (Over, Under ou All).
    """
    query = update.callback_query
    await query.answer()

    data_escolha = query.data  # Ex: "jogador_hoje", "jogador_mes", ...
    hoje = datetime.now()

    df_filtrado = pd.DataFrame()
    titulo = "Saldo por Jogador"

    if data_escolha == "jogador_hoje":
        data_str = hoje.strftime("%d/%m")
        df_filtrado = filtrar_por_dia_unico(context, data_str)
        titulo = f"Saldo por Jogador - {data_str}"

    elif data_escolha == "jogador_ontem":
        data_ontem = hoje - timedelta(days=1)
        data_str = data_ontem.strftime("%d/%m")
        df_filtrado = filtrar_por_dia_unico(context, data_str)
        titulo = f"Saldo por Jogador - {data_str}"

    elif data_escolha == "jogador_mes":
        df_filtrado = filtrar_mes_atual(context)
        titulo = "Saldo por Jogador - Mês Atual"

    elif data_escolha == "jogador_7d":
        df_filtrado = filtrar_ultimos_7_dias(context)
        titulo = "Saldo por Jogador - Últimos 7 Dias"

    elif data_escolha == "jogador_mes_anterior":
        df_filtrado = filtrar_mes_anterior(context)
        titulo = "Saldo por Jogador - Mês Anterior"

    elif data_escolha == "jogador_intervalo":
        # Pede as datas
        await query.message.edit_text(
            "Digite a data de início no formato DD/MM (ex: 09/02)",
            reply_markup=InlineKeyboardMarkup([[botao_voltar_anterior()]])
        )
        context.user_data['esperando_data_inicio_jogador'] = True
        return

    # Se já temos df_filtrado, armazenamos e chamamos o submenu Over/Under/All
    if data_escolha != "jogador_intervalo":
        if df_filtrado.empty:
            await query.edit_message_text("❌ Nenhuma aposta encontrada para esse período.")
            return

        context.user_data["df_jogador_filtrado"] = df_filtrado
        context.user_data["titulo_jogador"] = titulo

        # Agora escolhemos se será Over, Under, ou Both
        await escolher_tipo_aposta(update, context, query)


async def processar_datas_intervalo_jogador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Lida com a digitação do intervalo personalizado de datas para Saldo por Jogador.
    """
    if not context.user_data:
        context.user_data.clear()

    # Fluxo de data início
    if context.user_data.get('esperando_data_inicio_jogador'):
        context.user_data['data_inicio_jogador'] = update.message.text.strip()
        context.user_data['esperando_data_inicio_jogador'] = False
        context.user_data['esperando_data_fim_jogador'] = True
        await update.message.reply_text(
            "Agora, digite a data final (DD/MM)",
            reply_markup=InlineKeyboardMarkup([[botao_voltar_anterior()]])
        )

    # Fluxo de data fim
    elif context.user_data.get('esperando_data_fim_jogador'):
        data_inicio = context.user_data.pop('data_inicio_jogador')
        data_fim = update.message.text.strip()
        context.user_data['esperando_data_fim_jogador'] = False

        df_filtrado = filtrar_por_intervalo(context, data_inicio, data_fim)
        if df_filtrado.empty:
            await update.message.reply_text("❌ Nenhuma aposta encontrada nesse intervalo.")
            return

        titulo = f"Saldo por Jogador - {data_inicio} a {data_fim}"
        context.user_data["df_jogador_filtrado"] = df_filtrado
        context.user_data["titulo_jogador"] = titulo

        # Próximo passo: escolher Over, Under, All
        await update.message.reply_text("Intervalo escolhido com sucesso!")
        # Opcionalmente, pode chamar escolher_tipo_aposta sem "callback_query"
        await escolher_tipo_aposta(update, context)


# ---------------------------------------------------------------------------
# Passo 2: Escolha do tipo de aposta (Over, Under ou All)
# ---------------------------------------------------------------------------
async def escolher_tipo_aposta(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None) -> None:
    """
    Exibe o menu de tipo de aposta (Over, Under ou Over e Under).
    Pode ser chamado tanto de processar_botao_jogador quanto do fluxo intervalo.
    """
    if query is None and isinstance(update, Update):
        # Se viemos de update.message em vez de callback
        keyboard = [
            [
                InlineKeyboardButton("Over", callback_data="jogador_tipo_over"),
                InlineKeyboardButton("Under", callback_data="jogador_tipo_under"),
            ],
            [InlineKeyboardButton("Over e Under", callback_data="jogador_tipo_all")],
            [InlineKeyboardButton("Voltar", callback_data="menu_principal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Escolha o tipo de aposta que deseja filtrar:",
            reply_markup=reply_markup
        )
    else:
        # Se viemos via CallbackQuery
        query = query or update.callback_query
        await query.answer()
        keyboard = [
            [
                InlineKeyboardButton("Over", callback_data="jogador_tipo_over"),
                InlineKeyboardButton("Under", callback_data="jogador_tipo_under"),
            ],
            [InlineKeyboardButton("Over e Under", callback_data="jogador_tipo_all")],
            [InlineKeyboardButton("Voltar", callback_data="menu_principal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Escolha o tipo de aposta que deseja filtrar:",
            reply_markup=reply_markup
        )


async def processar_tipo_aposta_jogador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Recebe o callback_data com 'jogador_tipo_over/under/all' e exibe o saldo.
    """
    query = update.callback_query
    await query.answer()

    escolha = query.data  # Ex: "jogador_tipo_over"
    if escolha == "jogador_tipo_over":
        context.user_data["aposta"] = "over"
    elif escolha == "jogador_tipo_under":
        context.user_data["aposta"] = "under"
    else:
        context.user_data["aposta"] = "all"

    df_filtrado = context.user_data.get("df_jogador_filtrado", pd.DataFrame())
    titulo = context.user_data.get("titulo_jogador", "Saldo por Jogador")

    if df_filtrado.empty:
        await query.edit_message_text("❌ Nenhuma aposta encontrada para esse período.")
        return

    await exibir_saldo_jogador(update, context, df_filtrado, titulo, query)


# ---------------------------------------------------------------------------
# Passo 3: Exibir Saldos (Total e HotTips) com formatação final
# ---------------------------------------------------------------------------
async def exibir_saldo_jogador(update: Update, context: ContextTypes.DEFAULT_TYPE, df, titulo, query=None):
    """
    Monta duas mensagens:
      1) "Total" (filtro Over/Under/All)
      2) "Hot Tips" (se houver Fogo EV > 0)

    Com a formatação e ROI.
    """
    liga = get_liga_name(context) or "Geral"
    tipo_aposta = context.user_data.get("aposta", "all").lower()

    # 1) Filtrar df por Over, Under ou All
    if tipo_aposta == "over":
        df = df[df['Tipo Aposta'].str.contains("over", case=False, na=False)]
        subtitulo_aposta = "Over"
    elif tipo_aposta == "under":
        df = df[df['Tipo Aposta'].str.contains("under", case=False, na=False)]
        subtitulo_aposta = "Under"
    else:
        subtitulo_aposta = "Over e Under"

    if df.empty:
        # Se após o filtro não sobrou nada
        msg_nada = f"❌ Nenhuma aposta encontrada ({subtitulo_aposta}) no período."
        if query:
            await query.edit_message_text(msg_nada)
        else:
            await update.message.reply_text(msg_nada)
        return

    # Mensagem 1: "Total"
    msg_total = montar_saldo_jogador(df, titulo, liga, tipo="Total", aposta_desc=subtitulo_aposta)
    if query:
        await query.edit_message_text(msg_total, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg_total, parse_mode="Markdown")

    # Mensagem 2: "Hot Tips"
    df_hot = df[df['Fogo EV'] > 0].copy()
    if not df_hot.empty:
        msg_hot = montar_saldo_jogador(df_hot, titulo, liga, tipo="HotTips", aposta_desc=subtitulo_aposta)
        if query:
            chat_id = query.message.chat_id
            await context.bot.send_message(chat_id=chat_id, text=msg_hot, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg_hot, parse_mode="Markdown")


# ---------------------------------------------------------------------------
#  Montagem do texto final: com ROI, top 10 e bottom 10 invertido
# ---------------------------------------------------------------------------
def montar_saldo_jogador(df, titulo, liga, tipo="Total", aposta_desc="Over e Under"):
    """
    Gera o texto final, incluindo ROI e invertendo a listagem dos piores.
    Agora acessamos row.PL ao invés de row._asdict()["P/L"].
    """
    df_saldos = agrupar_por_jogador_com_count(df)
    if df_saldos.empty:
        return f"❌ Nenhum dado encontrado para {titulo}."

    # Calcular ROI = (PL / Qtd) * 100
    df_saldos["ROI"] = (df_saldos["PL"] / df_saldos["Qtd"]) * 100

    # Ordenar do maior para o menor PL
    df_saldos.sort_values(by="PL", ascending=False, inplace=True, ignore_index=True)

    # Top 10 e Bottom 10
    top_10 = df_saldos.head(10).copy()
    bottom_10 = df_saldos.tail(10).copy()
    bottom_10.sort_values(by="PL", ascending=True, inplace=True, ignore_index=True)

    # Escapar strings
    safe_titulo = escape_markdown(str(titulo))
    safe_liga   = escape_markdown(str(liga))
    safe_tipo   = escape_markdown(str(tipo))
    safe_aposta = escape_markdown(str(aposta_desc))

    # Cabeçalho
    texto = (
        f"{safe_titulo}\n"
        f"Tipo: {safe_tipo}\n"
        f"Liga: {safe_liga}\n"
        f"Aposta: {safe_aposta}\n\n"
    )

    # 10 Melhores
    texto += "10 Melhores (Saldo e ROI):\n\n"
    for i, row in enumerate(top_10.itertuples(), start=1):
        jogador = escape_markdown(str(row.Jogador))
        pl  = row.PL
        roi = row.ROI
        prefixo = "✅" if pl > 0 else "❌" if pl < 0 else "🔄"
        texto += (f"{i} {prefixo} {jogador}: {pl:+.2f}u | {roi:.1f}%\n")

    # 10 Piores
    texto += "\n10 Piores (Saldo e ROI):\n\n"
    bottom_10_reversed = list(bottom_10.itertuples())[::-1]
    rank = 10
    for row in bottom_10_reversed:
        jogador = escape_markdown(str(row.Jogador))
        pl  = row.PL
        roi = row.ROI
        prefixo = "✅" if pl > 0 else "❌" if pl < 0 else "🔄"
        texto += (f"{rank} {prefixo} {jogador}: {pl:+.2f}u | {roi:.1f}%\n")
        rank -= 1

    return texto


# ---------------------------------------------------------------------------
# Função auxiliar para agrupar e contar quantas apostas cada jogador teve
# ---------------------------------------------------------------------------
def agrupar_por_jogador_com_count(df):
    """
    Retorna DataFrame com:
      Jogador, PL (soma), Qtd (contagem de tips)
    """
    df = df.copy()
    df['Time Casa'] = df['Time Casa'].apply(extract_player_name)
    df['Time Fora'] = df['Time Fora'].apply(extract_player_name)

    # Construir uma lista (jogador, pl) para cada time
    lines = []
    for _, row in df.iterrows():
        pl = row['P/L']
        casa = row['Time Casa']
        fora = row['Time Fora']

        if casa:
            lines.append((casa, pl))
        if fora:
            lines.append((fora, pl))

    if not lines:
        return pd.DataFrame(columns=["Jogador", "PL", "Qtd"])

    # Converte para DF
    df_players = pd.DataFrame(lines, columns=["Jogador", "PL_original"])  
    # Observação: criei "PL_original" para evitar confusão com "sum" mais abaixo.

    # Agrupa por jogador, soma PL e conta linhas
    grouped = df_players.groupby("Jogador")["PL_original"].agg(["sum", "count"]).reset_index()
    grouped.rename(columns={"sum": "PL", "count": "Qtd"}, inplace=True)

    return grouped


def extract_player_name(team_name):
    """
    Extrai o nome do jogador entre parênteses, ou retorna o texto original caso não encontre.
    Ex: "Team X (Jogador)" -> "Jogador".
    """
    match = re.search(r'\((.*?)\)', str(team_name))
    return match.group(1) if match else str(team_name)


# ---------------------------------------------------------------------------
#  Funções de filtro de datas
# ---------------------------------------------------------------------------
def filtrar_por_dia_unico(context, dia_str: str):
    df = get_dataframe_by_liga(context).copy()
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'], errors='coerce')
    df['DataStr'] = df['Horário Envio'].dt.strftime('%d/%m')
    df = df[(df['DataStr'] == dia_str) & (df['Anulada'] != 'Sim')]
    return df

def filtrar_ultimos_7_dias(context):
    df = get_dataframe_by_liga(context).copy()
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Data'] = df['Horário Envio'].dt.date
    data_limite = datetime.now().date() - timedelta(days=6)
    return df[(df['Data'] >= data_limite) & (df['Anulada'] != 'Sim')]

def filtrar_mes_atual(context):
    df = get_dataframe_by_liga(context).copy()
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Data'] = df['Horário Envio'].dt.date
    hoje = datetime.now()
    primeiro_dia = datetime(hoje.year, hoje.month, 1).date()
    return df[(df['Data'] >= primeiro_dia) & (df['Anulada'] != 'Sim')]

def filtrar_mes_anterior(context):
    df = get_dataframe_by_liga(context).copy()
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Data'] = df['Horário Envio'].dt.date

    hoje = datetime.now()
    primeiro_dia_mes_atual = datetime(hoje.year, hoje.month, 1)
    ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
    primeiro_dia_mes_anterior = datetime(
        ultimo_dia_mes_anterior.year, 
        ultimo_dia_mes_anterior.month, 
        1
    ).date()

    return df[
        (df['Data'] >= primeiro_dia_mes_anterior) &
        (df['Data'] <= ultimo_dia_mes_anterior.date()) &
        (df['Anulada'] != 'Sim')
    ]

def filtrar_por_intervalo(context, data_inicio, data_fim):
    df = get_dataframe_by_liga(context).copy()
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'], errors='coerce')
    df['Data'] = df['Horário Envio'].dt.date

    try:
        ano_min = df['Data'].min().year if not df.empty else datetime.now().year
        ano_max = df['Data'].max().year if not df.empty else datetime.now().year

        di = datetime.strptime(data_inicio, '%d/%m').date().replace(year=ano_min)
        dfim = datetime.strptime(data_fim, '%d/%m').date().replace(year=ano_max)

        if dfim < di:
            raise ValueError("Data final anterior à data inicial")

        return df[
            (df['Data'] >= di) & (df['Data'] <= dfim) & 
            (df['Anulada'] != 'Sim')
        ]
    except ValueError as e:
        print("Erro ao converter datas:", e)
        return pd.DataFrame()

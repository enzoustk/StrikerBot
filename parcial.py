# parcial.py

import re
import calendar
import pandas as pd
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# Importa do common.py as funções necessárias (incluindo exibir_menu_ligas, etc.)
from common import (
    escape_markdown,
    botao_voltar_anterior,
    exibir_menu_ligas,
    get_dataframe_by_liga,
    get_liga_name
)


# ---------------------------------------------------------------------------
#  A. Novo submenu principal de "Resultados"
# ---------------------------------------------------------------------------
async def parcial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Ao clicar em "Resultados" (menu_parcial), exibe este submenu:
    [1] Gerar Gráficos
    [2] Saldo por Jogador (placeholder)
    [3] Relatório de Apostas
    """
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = [
        [InlineKeyboardButton("Gerar Gráficos", callback_data="sub_gerar_graficos")],
        [InlineKeyboardButton("Saldo por Jogador", callback_data="sub_saldo_jogador")],
        [InlineKeyboardButton("Relatório de Apostas", callback_data="sub_relatorio_apostas")],
        [InlineKeyboardButton("Voltar", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Escolha uma opção para ver os resultados:", reply_markup=reply_markup)
    else:
        await query.message.edit_text("Escolha uma opção para ver os resultados:", reply_markup=reply_markup)


async def processar_submenu_resultados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Recebe o callback_data dos botões do submenu de Resultados.
    """
    query = update.callback_query
    await query.answer()

    if query.data == "sub_gerar_graficos":
        # O fluxo do gráfico é chamado via exibir_menu_ligas, mas com fluxo="grafico"
        await exibir_menu_ligas(update, context, fluxo="grafico")

    # parcial.py (no processar_submenu_resultados)
    elif query.data == "sub_saldo_jogador":
        # Agora chamamos o fluxo jogador
        await exibir_menu_ligas(update, context, fluxo="jogador")

    elif query.data == "sub_relatorio_apostas":
        # Chamamos o fluxo tradicional de Parciais (data, etc.), que começa pela escolha de liga
        await exibir_menu_ligas(update, context, fluxo="parcial")


# ---------------------------------------------------------------------------
#  B. Fluxo "Relatório de Apostas" (antigo fluxo do /parcial)
# ---------------------------------------------------------------------------
async def processar_menu_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Chamado após a escolha de liga (via common.py) para o fluxo "parcial".
    Exibe o menu de seleção de datas.
    """
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("Hoje", callback_data="parcial_hoje")],
        [InlineKeyboardButton("Mês Atual", callback_data="parcial_mes")],
        [
            InlineKeyboardButton("Ontem", callback_data="parcial_ontem"),
            InlineKeyboardButton("Últ. 7d", callback_data="parcial_7d")
        ],
        [
            InlineKeyboardButton("Mês Anterior", callback_data="parcial_mes_anterior"),
            InlineKeyboardButton("Outra Data", callback_data="parcial_intervalo")
        ],
        [InlineKeyboardButton("Voltar", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Escolha a data desejada:", reply_markup=reply_markup)


async def processar_botao_parcial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa os botões do menu de data (Hoje, Ontem, Mês Atual, etc.) para gerar o relatório.
    """
    query = update.callback_query
    await query.answer()

    hoje = datetime.now()
    if query.data == "parcial_hoje":
        data = hoje.strftime("%d/%m")
        await enviar_parcial(update, context, data, query)
    elif query.data == "parcial_ontem":
        data = (hoje - timedelta(days=1)).strftime("%d/%m")
        await enviar_parcial(update, context, data, query)
    elif query.data == "parcial_mes":
        df_filtrado = filter_by_current_month(context)
        await enviar_parcial_com_df(update, context, df_filtrado, "📅 Saldo Mês Atual", query)
    elif query.data == "parcial_7d":
        df_filtrado = filter_by_last_7_days(context)
        await enviar_parcial_com_df(update, context, df_filtrado, "📅 Últimos 7 dias", query)
    elif query.data == "parcial_mes_anterior":
        df_filtrado = filter_by_previous_month(context)
        await enviar_parcial_com_df(update, context, df_filtrado, "📅 Saldo Mês Anterior", query)
    elif query.data == "parcial_intervalo":
        await query.edit_message_text(
            "Digite a data de início no formato DD/MM (ex: 09/02)",
            reply_markup=InlineKeyboardMarkup([[botao_voltar_anterior()]])
        )
        context.user_data['esperando_data_inicio'] = True


async def processar_datas_intervalo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Lida com a digitação do intervalo personalizado de datas.
    """
    if not context.user_data:
        context.user_data.clear()

    # Fluxo para intervalo personalizado
    if context.user_data.get('esperando_data_inicio'):
        context.user_data['data_inicio'] = update.message.text.strip()
        context.user_data['esperando_data_inicio'] = False
        context.user_data['esperando_data_fim'] = True
        await update.message.reply_text(
            "Agora, digite a data final (DD/MM)",
            reply_markup=InlineKeyboardMarkup([[botao_voltar_anterior()]])
        )
    elif context.user_data.get('esperando_data_fim'):
        data_inicio = context.user_data.pop('data_inicio')
        data_fim = update.message.text.strip()
        context.user_data['esperando_data_fim'] = False

        try:
            df_filtrado = filter_by_custom_range(context, data_inicio, data_fim)
            titulo = f"📅 Relatório - {data_inicio} a {data_fim}"
            await enviar_parcial_com_df(update, context, df_filtrado, titulo)
        except ValueError as e:
            await update.message.reply_text(
                f"❌ {e}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar", callback_data="menu_parcial")]])
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Erro ao processar o intervalo: {e}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar", callback_data="menu_parcial")]])
            )


# ---------------------------------------------------------------------------
#  C. Funções que enviam o relatório de apostas (Parcial)
# ---------------------------------------------------------------------------
def filter_by_current_month(context):
    df = get_dataframe_by_liga(context)
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Data'] = df['Horário Envio'].dt.date

    hoje = datetime.now()
    primeiro_dia_mes_atual = datetime(hoje.year, hoje.month, 1).date()
    return df[(df['Data'] >= primeiro_dia_mes_atual) & (df['Anulada'] != 'Sim')]

def filter_by_last_7_days(context):
    df = get_dataframe_by_liga(context)
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Data'] = df['Horário Envio'].dt.date

    data_limite = datetime.now().date() - timedelta(days=6)
    data_atual = datetime.now().date()
    return df[(df['Data'] >= data_limite) & (df['Data'] <= data_atual) & (df['Anulada'] != 'Sim')]

def filter_by_previous_month(context):
    df = get_dataframe_by_liga(context)
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

def filter_by_date(context, target_date):
    df = get_dataframe_by_liga(context)
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Time Casa'] = df['Time Casa'].apply(extract_player_name)
    df['Time Fora'] = df['Time Fora'].apply(extract_player_name)

    return df[
        (df['Horário Envio'].dt.strftime('%d/%m') == target_date) &
        (df['Anulada'] != 'Sim')
    ]

def filter_by_custom_range(context, data_inicio, data_fim):
    df = get_dataframe_by_liga(context)
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'], errors='coerce')
    df['Data'] = df['Horário Envio'].dt.date

    try:
        df_ano_inicio = df['Data'].min().year if not df.empty else datetime.now().year
        di = datetime.strptime(data_inicio, '%d/%m').date().replace(year=df_ano_inicio)

        df_ano_fim = df['Data'].max().year if not df.empty else datetime.now().year
        dfim = datetime.strptime(data_fim, '%d/%m').date().replace(year=df_ano_fim)

        if dfim < di:
            raise ValueError("A data final é anterior à data inicial.")

        return df[
            (df['Data'] >= di) & (df['Data'] <= dfim) &
            (df['Anulada'] != 'Sim')
        ]
    except ValueError as ve:
        raise ValueError(f"Formato de data inválido ou intervalo incorreto: {ve}")


async def enviar_parcial(update: Update, context: ContextTypes.DEFAULT_TYPE, data_recebida, query=None):
    """
    Envia o relatório parcial para a data especificada (ex: "Hoje", "Ontem").
    """
    try:
        liga = get_liga_name(context) or "Geral"
        df_filtrado = filter_by_date(context, data_recebida)
        if df_filtrado.empty:
            resposta = f"❌ Nenhuma aposta encontrada para a data **{data_recebida}** na liga **{liga}**."
            if query:
                await query.edit_message_text(resposta, parse_mode="Markdown")
            else:
                await update.message.reply_text(resposta, parse_mode="Markdown")
            return

        # Cálculo das métricas gerais
        lucro, total_apostas, roi, green, meio_green, void, meio_red, red = calculate_metrics(df_filtrado)
        balance_by_time = calculate_balance_by_time(df_filtrado)

        # Construção do Relatório Geral
        resposta_total = format_response(
            title=data_recebida,
            tipo="Geral",
            liga=liga,
            lucro=lucro,
            total_apostas=total_apostas,
            roi=roi,
            green=green,
            meio_green=meio_green,
            void=void,
            meio_red=meio_red,
            red=red,
            balance_by_time=balance_by_time
        )

        if query:
            await query.edit_message_text(resposta_total, parse_mode="Markdown")
        else:
            await update.message.reply_text(resposta_total, parse_mode="Markdown")

        # Filtra e envia Hot Tips
        df_hot_tips = df_filtrado[df_filtrado['Fogo EV'] > 0]
        if not df_hot_tips.empty:
            lucro_hot, total_hot, roi_hot, green_hot, meio_green_hot, void_hot, meio_red_hot, red_hot = calculate_metrics(df_hot_tips)
            balance_hot_by_time = calculate_balance_by_time(df_hot_tips)

            resposta_hot_tips = format_response(
                title=data_recebida,
                tipo="Hot Tips",
                liga=liga,
                lucro=lucro_hot,
                total_apostas=total_hot,
                roi=roi_hot,
                green=green_hot,
                meio_green=meio_green_hot,
                void=void_hot,
                meio_red=meio_red_hot,
                red=red_hot,
                balance_by_time=balance_hot_by_time
            )

            chat_id = update.effective_chat.id
            await context.bot.send_message(chat_id=chat_id, text=resposta_hot_tips, parse_mode="Markdown")

    except Exception as e:
        resposta_erro = f"❌ Erro ao processar a data **{data_recebida}**: {e}"
        if query:
            await query.edit_message_text(resposta_erro, parse_mode="Markdown")
        else:
            if update.message:
                await update.message.reply_text(resposta_erro, parse_mode="Markdown")
            else:
                print(resposta_erro)

async def enviar_parcial_com_df(update: Update, context: ContextTypes.DEFAULT_TYPE, df, titulo, query=None):
    """
    Envia o relatório (Total/Geral e Hot Tips) a partir de um DataFrame filtrado,
    com a formatação de saldos (ex: Saldo Mês Atual, etc.).
    """
    if df.empty:
        resposta = "❌ Nenhuma aposta encontrada no período selecionado."
        if query:
            await query.edit_message_text(resposta, parse_mode="Markdown")
        else:
            await update.message.reply_text(resposta, parse_mode="Markdown")
        return

    df = df.copy()
    df['Data'] = pd.to_datetime(df['Horário Envio']).dt.date

    # Determina intervalo de datas
    start_date = df['Data'].min()
    end_date = df['Data'].max()

    # Ajusta o título para Mês Atual, Mês Anterior, etc.
    if titulo == "📅 Saldo Mês Atual":
        current_month = datetime.now().month
        month_name = calendar.month_name[current_month].capitalize()
        titulo = f"📅 Saldo Parcial: {month_name}"
    elif titulo == "📅 Saldo Mês Anterior":
        today = datetime.now()
        first_day_current_month = datetime(today.year, today.month, 1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        previous_month_name = calendar.month_name[last_day_previous_month.month].capitalize()
        titulo = f"📅 Saldo: {previous_month_name}"

    liga_escolhida = get_liga_name(context) or "Geral"

    # ----------------------- Saldos Gerais -----------------------
    summary = generate_summary_by_date(df, start_date, end_date)
    resumo_diario_str = "**Resumo Diário:**\n\n"
    for data, saldo in summary.items():
        emoji = "✅" if saldo > 0 else "❌" if saldo < 0 else "🔄"
        resumo_diario_str += f"{data.strftime('%d/%m')}: {emoji} {saldo:+.2f}u\n"

    lucro_total, total_apostas, roi, _, _, _, _, _ = calculate_metrics(df)

    df_over = df[df['Tipo Aposta'].str.contains('Over', case=False)]
    df_under = df[df['Tipo Aposta'].str.contains('Under', case=False)]
    total_over = df_over['P/L'].sum()
    total_under = df_under['P/L'].sum()
    roi_over = (total_over / len(df_over)) * 100 if len(df_over) else 0
    roi_under = (total_under / len(df_under)) * 100 if len(df_under) else 0

    melhor_over, pior_over = generate_player_performance(df_over, 'Over')
    melhor_under, pior_under = generate_player_performance(df_under, 'Under')

    saldo_titulo = titulo
    resposta_total = (
        f"**{saldo_titulo}**\n\n"
        f"Tipo: Geral\n"
        f"Liga: {liga_escolhida}\n\n"
        f"{resumo_diario_str}"
        f"\n✅ **Total**: {lucro_total:+.2f}u | {total_apostas} Tips | {roi:.2f}% ROI\n"
        "\n⬆️ **Over** ⬆️:\n"
        f"Total: {'✅' if total_over > 0 else '❌'} {total_over:+.2f}u | {len(df_over)} Tips | {roi_over:.2f}% ROI\n"
        f"Melhor jogador: {melhor_over}\n"
        f"Pior jogador: {pior_over}\n"
        "\n⬇️ **Under** ⬇️:\n"
        f"Total: {'✅' if total_under > 0 else '❌'} {total_under:+.2f}u | {len(df_under)} Tips | {roi_under:.2f}% ROI\n"
        f"Melhor jogador: {melhor_under}\n"
        f"Pior jogador: {pior_under}\n"
    )

    if query:
        await query.edit_message_text(resposta_total, parse_mode="Markdown")
    else:
        await update.message.reply_text(resposta_total, parse_mode="Markdown")

    # ----------------------- Hot Tips -----------------------
    df_hot_tips = df[df['Fogo EV'] > 0].copy()
    if not df_hot_tips.empty:
        summary_hot = generate_summary_by_date(df_hot_tips, start_date, end_date)
        resumo_diario_ht_str = "**Resumo Diário:**\n\n"
        for data, saldo in summary_hot.items():
            emoji = "✅" if saldo > 0 else "❌" if saldo < 0 else "🔄"
            resumo_diario_ht_str += f"{data.strftime('%d/%m')}: {emoji} {saldo:+.2f}u\n"

        lucro_ht, total_ht, roi_ht, _, _, _, _, _ = calculate_metrics(df_hot_tips)

        df_over_ht = df_hot_tips[df_hot_tips['Tipo Aposta'].str.contains('Over', case=False)]
        df_under_ht= df_hot_tips[df_hot_tips['Tipo Aposta'].str.contains('Under', case=False)]
        total_over_ht = df_over_ht['P/L'].sum()
        total_under_ht= df_under_ht['P/L'].sum()

        roi_over_ht  = (total_over_ht / len(df_over_ht)) * 100 if len(df_over_ht) else 0
        roi_under_ht = (total_under_ht / len(df_under_ht)) * 100 if len(df_under_ht) else 0

        melhor_over_ht, pior_over_ht   = generate_player_performance(df_over_ht,   'Over')
        melhor_under_ht, pior_under_ht = generate_player_performance(df_under_ht, 'Under')

        saldo_titulo_ht = titulo
        resposta_hot_tips = (
            f"**{saldo_titulo_ht}**\n\n"
            f"Tipo: Hot Tips 🔥\n"
            f"Liga: {liga_escolhida}\n\n"
            f"{resumo_diario_ht_str}"
            f"\n✅ **Total**: {lucro_ht:+.2f}u | {total_ht} Tips | {roi_ht:.2f}% ROI\n"
            "\n⬆️ **Over** ⬆️:\n"
            f"Total: {'✅' if total_over_ht > 0 else '❌'} {total_over_ht:+.2f}u | {len(df_over_ht)} Tips | {roi_over_ht:.2f}% ROI\n"
            f"Melhor jogador: {melhor_over_ht}\n"
            f"Pior jogador: {pior_over_ht}\n"
            "\n⬇️ **Under** ⬇️:\n"
            f"Total: {'✅' if total_under_ht > 0 else '❌'} {total_under_ht:+.2f}u | {len(df_under_ht)} Tips | {roi_under_ht:.2f}% ROI\n"
            f"Melhor jogador: {melhor_under_ht}\n"
            f"Pior jogador: {pior_under_ht}\n"
        )

        await update.effective_message.reply_text(resposta_hot_tips, parse_mode="Markdown")


# ---------------------------------------------------------------------------
#  D. Funções auxiliares de cálculo
# ---------------------------------------------------------------------------
def extract_player_name(team_name):
    match = re.search(r'\((.*?)\)', str(team_name))
    return match.group(1) if match else str(team_name)

def calculate_metrics(df):
    lucro = df['P/L'].sum()
    total_apostas = len(df)
    roi = (lucro / total_apostas * 100) if total_apostas != 0 else 0

    green = len(df[df['P/L'] > 0.65])
    meio_green = len(df[(df['P/L'] > 0) & (df['P/L'] <= 0.65)])
    void = len(df[df['P/L'] == 0])
    meio_red = len(df[df['P/L'] == -0.5])
    red = len(df[df['P/L'] == -1])

    return lucro, total_apostas, roi, green, meio_green, void, meio_red, red

def calculate_balance_by_time(df):
    df = df.copy()
    df['Hora'] = pd.to_datetime(df['Horário Envio']).dt.hour
    bins = [0, 4, 8, 12, 16, 20, 24]
    labels = [
        '00:00 até 03:59',
        '04:00 até 07:59',
        '08:00 até 11:59',
        '12:00 até 15:59',
        '16:00 até 19:59',
        '20:00 até 23:59'
    ]
    df['Faixa Horária'] = pd.cut(df['Hora'], bins=bins, labels=labels, right=False)
    return df.groupby('Faixa Horária', observed=False)['P/L'].sum()

def format_response(title, tipo, liga, lucro, total_apostas, roi, green, meio_green, void, meio_red, red, balance_by_time):
    """
    Formata a mensagem do relatório diário no formato solicitado.
    """
    tipo_emoji = "🔥" if tipo == "Hot Tips" else ""
    response = (
        f"Relatório: {title} \n\n"
        f"Tipo: {tipo} {tipo_emoji}\n"
        f"Liga: {liga} \n\n"
        f"💰Lucro: {lucro:.2f}\n"
        f"📊Total de Apostas: {total_apostas}\n"
        f"📈ROI: {roi:.2f}%\n\n"
        f"----------\n\n"
        f"Green: {green}\n"
        f"Meio Green: {meio_green}\n"
        f"Void: {void}\n"
        f"Meio Red: {meio_red}\n"
        f"Red: {red}\n\n"
        f"----------\n\n"
        f"⏰Saldo por Horário:\n"
    )
    for faixa, saldo in balance_by_time.items():
        if saldo > 0:
            emoji = "✅"
        elif saldo < 0:
            emoji = "❌"
        else:
            emoji = "🔄"
        response += f" {faixa}: {saldo:+.2f} {emoji}\n"

    return response

def generate_summary_by_date(df, start_date, end_date):
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    df['Data'] = pd.to_datetime(df['Horário Envio']).dt.date
    daily_summary = df.groupby('Data')['P/L'].sum()
    daily_summary = daily_summary.reindex(all_dates, fill_value=0.0)
    return daily_summary

def generate_player_performance(df, aposta_tipo):
    """
    Gera o melhor e pior jogador com base no saldo acumulado (P/L).
    """
    df_tipo = df[df['Tipo Aposta'].str.contains(aposta_tipo, case=False)]
    if df_tipo.empty:
        return "N/A", "N/A"

    players_pl = []
    for _, row in df_tipo.iterrows():
        casa = extract_player_name(row['Time Casa'])
        fora = extract_player_name(row['Time Fora'])
        pl = row['P/L']
        if casa:
            players_pl.append((casa, pl))
        if fora:
            players_pl.append((fora, pl))

    if not players_pl:
        return "N/A", "N/A"

    df_players = pd.DataFrame(players_pl, columns=['Jogador', 'P/L'])
    performance = df_players.groupby('Jogador')['P/L'].sum().sort_values(ascending=False)

    melhor_jogador = f"{performance.idxmax()} (✅ {performance.max():.2f})"
    pior_jogador = f"{performance.idxmin()} (❌ {performance.min():.2f})"

    return melhor_jogador, pior_jogador

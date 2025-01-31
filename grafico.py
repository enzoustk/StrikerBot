# grafico.py

import io
import re
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Import da função genérica para exibir o menu de ligas e obter o DataFrame:
from common import exibir_menu_ligas, get_dataframe_by_liga


# --------------------------------------------------------------------------
#  1. O fluxo de "Gerar Gráficos" agora é chamado dentro do submenu "Resultados"
#     (sub_gerar_graficos -> processar_escolha_liga_generico -> exibir_menu_data_grafico)
# --------------------------------------------------------------------------

async def exibir_menu_data_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Chamado após a escolha de liga (via common.py) com fluxo="grafico".
    Exibe o menu de intervalos de tempo para gerar os gráficos (Hoje, Ontem, 7 dias etc.).
    """
    query = update.callback_query
    keyboard = [
        [
            InlineKeyboardButton("Hoje", callback_data="grafico_hoje"),
            InlineKeyboardButton("Ontem", callback_data="grafico_ontem")
        ],
        [
            InlineKeyboardButton("Últimos 7 Dias", callback_data="grafico_7d"),
            InlineKeyboardButton("Mês Atual", callback_data="grafico_mes")
        ],
        [
            InlineKeyboardButton("Mês Anterior", callback_data="grafico_mes_anterior"),
        ],
        [InlineKeyboardButton("Voltar", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(
        "Escolha o intervalo de tempo para gerar os gráficos:",
        reply_markup=reply_markup
    )


async def processar_botao_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa a escolha do intervalo de tempo para geração dos gráficos.
    """
    query = update.callback_query
    await query.answer()

    df = get_dataframe_by_liga(context)
    hoje = datetime.now()

    if query.data == "grafico_hoje":
        df_filtrado = filtrar_intervalo_custom(df, hoje.strftime("%d/%m"), hoje.strftime("%d/%m"))
        titulo = f"Saldo Parcial - {hoje.strftime('%d/%m')}"

    elif query.data == "grafico_ontem":
        data_ontem = hoje - timedelta(days=1)
        df_filtrado = filtrar_intervalo_custom(df, data_ontem.strftime("%d/%m"), data_ontem.strftime("%d/%m"))
        titulo = f"Saldo Total - {data_ontem.strftime('%d/%m')}"

    elif query.data == "grafico_7d":
        df_filtrado = filtrar_ultimos_7_dias(df)
        titulo = "Saldo Total - Últimos 7 Dias"

    elif query.data == "grafico_mes":
        df_filtrado = filtrar_mes_atual(df)
        titulo = "Saldo Mensal Parcial"

    elif query.data == "grafico_mes_anterior":
        df_filtrado = filtrar_mes_anterior(df)
        titulo = "Saldo Total - Mês Anterior"

    context.user_data['df_filtrado'] = df_filtrado
    context.user_data['titulo'] = titulo

    await query.message.edit_text(f"Intervalo selecionado: {titulo}")
    await mostrar_opcoes_tipo_grafico(update, context, query)

async def mostrar_opcoes_tipo_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """
    Exibe opções de tipo de gráfico (Totais, Hot Tips, Ambos).
    """
    keyboard = [
        [
            InlineKeyboardButton("Totais", callback_data="grafico_tipo_totais"),
            InlineKeyboardButton("Hot Tips", callback_data="grafico_tipo_hottips")
        ],
        [InlineKeyboardButton("Ambos", callback_data="grafico_tipo_ambos")],
        [InlineKeyboardButton("Voltar", callback_data="grafico")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.message.edit_text("Escolha o tipo de gráfico:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Escolha o tipo de gráfico:", reply_markup=reply_markup)


async def processar_tipo_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa o tipo de gráfico selecionado e gera os gráficos.
    """
    query = update.callback_query
    await query.answer()

    tipo_grafico = query.data.split("_")[-1]  # Ex: "totais", "hottips", "ambos"
    df_filtrado = context.user_data.get('df_filtrado')
    titulo = context.user_data.get('titulo')

    if df_filtrado is None or df_filtrado.empty:
        await query.message.edit_text(
            "❌ Nenhum dado encontrado para gerar gráficos.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar", callback_data="grafico")]])
        )
        return

    await query.message.edit_text("⏳ Gerando gráficos...")
    await gerar_graficos(update, query, df_filtrado, titulo, tipo_grafico)

# ------------------------------------------------------------------------------
# Geração dos gráficos
# ------------------------------------------------------------------------------
async def gerar_graficos(update, query, df, titulo, tipo_grafico):
    """Gera os gráficos de acordo com o tipo solicitado: Totais, Hot Tips ou Ambos."""
    if tipo_grafico in ["totais", "ambos"]:
        await gerar_graficos_individuais(query, df, f"{titulo}")

    if tipo_grafico in ["hottips", "ambos"]:
        df_hottips = df[df['Fogo EV'] > 0]
        if not df_hottips.empty:
            await gerar_graficos_individuais(query, df_hottips, f"{titulo} - Hot Tips")


async def gerar_graficos_individuais(query, df, titulo):
    """
    Gera 3 gráficos de exemplo e envia via Telegram:
      1) Saldo por Tipo de Aposta
      2) Top 5 Jogadores
      3) Lucro Acumulado
    """
    # Gráfico 1: Saldo por Tipo de Aposta
    combined_performance = df.groupby('Tipo Aposta')['P/L'].sum().reset_index()
    combined_performance['Tipo Aposta'] = combined_performance['Tipo Aposta'].fillna("Saldo Total")
    combined_performance.loc[len(combined_performance)] = ['Saldo Total', df['P/L'].sum()]

    combined_performance['color'] = calcular_cor_paleta(combined_performance, 'P/L')

    plt.figure(figsize=(8, 6))
    bars = plt.bar(combined_performance['Tipo Aposta'],
                   combined_performance['P/L'],
                   color=combined_performance['color'],
                   edgecolor='black')
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height(),
                 round(bar.get_height(), 2),
                 ha='center', va='bottom', fontsize=10)
    plt.ylabel('P/L (Lucro/Perda)', fontsize=12)
    plt.xlabel('Tipo de Aposta')
    plt.title(f"{titulo}", fontsize=14, weight='bold')
    await enviar_grafico(query, plt)

    # Gráfico 2: Top 5 Jogadores
    top_5_players = get_top_5_players(df)
    top_5_players['color'] = calcular_cor_paleta(top_5_players, 'P/L')

    plt.figure(figsize=(10, 6))
    bars = plt.bar(top_5_players['Jogador'], top_5_players['P/L'],
                   color=top_5_players['color'],
                   edgecolor='black')
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height(),
                 round(bar.get_height(), 2),
                 ha='center', va='bottom', fontsize=10)
    plt.ylabel('P/L (Lucro/Perda)', fontsize=12)
    plt.xlabel('Jogadores')
    plt.title(f"{titulo} - Top 5 Jogadores", fontsize=14, weight='bold')
    plt.xticks(rotation=45)
    await enviar_grafico(query, plt)

    # Gráfico 3: Lucro Acumulado
    df = df.copy()
    df['Lucro Acumulado'] = df['P/L'].cumsum()
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(df)), df['Lucro Acumulado'],
             marker='o', color='green', linestyle='-', linewidth=2)
    plt.fill_between(range(len(df)),
                     df['Lucro Acumulado'], color='lightgreen', alpha=0.3)
    plt.ylabel('Lucro Acumulado (P/L)', fontsize=12)
    plt.title(f"{titulo} - Lucro Acumulado", fontsize=14, weight='bold')
    plt.grid(True)
    await enviar_grafico(query, plt)

async def enviar_grafico(query, plt):
    """
    Salva o gráfico em buffer e envia pelo Telegram.
    """
    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    await query.message.reply_photo(photo=buffer)
    plt.close()


# ------------------------------------------------------------------------------
# Funções auxiliares de filtro e cálculo
# ------------------------------------------------------------------------------
def filtrar_intervalo_custom(df, data_inicio, data_fim):
    df = df.copy()
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Data'] = df['Horário Envio'].dt.strftime('%d/%m')

    df_filtrado = df[
        (df['Data'] >= data_inicio) &
        (df['Data'] <= data_fim) &
        (df['Anulada'] != 'Sim')
    ]
    return df_filtrado

def filtrar_ultimos_7_dias(df):
    df = df.copy()
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Data'] = df['Horário Envio'].dt.date

    data_limite = datetime.now().date() - timedelta(days=6)
    df_filtrado = df[
        (df['Data'] >= data_limite) &
        (df['Anulada'] != 'Sim')
    ]
    return df_filtrado

def filtrar_mes_atual(df):
    df = df.copy()
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])
    df['Data'] = df['Horário Envio'].dt.date

    hoje = datetime.now()
    primeiro_dia_mes = datetime(hoje.year, hoje.month, 1).date()
    df_filtrado = df[
        (df['Data'] >= primeiro_dia_mes) &
        (df['Anulada'] != 'Sim')
    ]
    return df_filtrado

def filtrar_mes_anterior(df):
    df = df.copy()
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

    df_filtrado = df[
        (df['Data'] >= primeiro_dia_mes_anterior) &
        (df['Data'] <= ultimo_dia_mes_anterior.date()) &
        (df['Anulada'] != 'Sim')
    ]
    return df_filtrado

def get_top_5_players(df):
    df = df.copy()

    def extract_player_name(team_name):
        match = re.search(r'\((.*?)\)', str(team_name))
        return match.group(1) if match else None

    players_pl = []
    for _, row in df.iterrows():
        casa = extract_player_name(row['Time Casa'])
        fora = extract_player_name(row['Time Fora'])
        pl = row['P/L']
        if casa:
            players_pl.append((casa, pl))
        if fora:
            players_pl.append((fora, pl))

    if not players_pl:
        return pd.DataFrame(columns=['Jogador', 'P/L'])

    df_players = pd.DataFrame(players_pl, columns=['Jogador', 'P/L'])
    top_5_players = df_players.groupby('Jogador')['P/L'].sum().nlargest(5).reset_index()

    return top_5_players

def calcular_cor_paleta(df, col_valor):
    max_valor = df[col_valor].abs().max()
    paleta_verde = sns.light_palette("green", n_colors=10)
    paleta_vermelha = sns.light_palette("red", n_colors=10)

    def mapear_cor(valor):
        if valor > 0:
            idx = int((valor / max_valor) * 9) if max_valor else 0
            return paleta_verde[min(idx, 9)]
        elif valor < 0:
            idx = int((abs(valor) / max_valor) * 9) if max_valor else 0
            return paleta_vermelha[min(idx, 9)]
        return (1, 1, 1)

    return df[col_valor].apply(mapear_cor).tolist()

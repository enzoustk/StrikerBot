import pandas as pd

PLANILHA_BATTLE_8 = pd.read_excel('../StrikerBetBot/arquivos/planilhas/apostas_feitas.xlsx')
PLANILHA_H2H_8 =pd.read_excel('../sbbh2h/arquivos/planilhas/apostas_feitas.xlsx')
FILE_PATH_DADOS = 'a'
CHAT_ID = 'b'

BOT_TOKEN_PARCIAL = "7709297039:AAFTRjYDzfZZ9yYL0XWwbtcCoboeLWqGagY"
USERS_PERMITIDOS = [6045850973, 987654321]  # Substitua pelos IDs reais dos usuários
CHAT_FORMULARIO = -1002343941988  # Substitua pelo ID do grupo no Telegram

MESES_PT_BR = {
    "January": "Janeiro", "February": "Fevereiro", "March": "Março",
    "April": "Abril", "May": "Maio", "June": "Junho",
    "July": "Julho", "August": "Agosto", "September": "Setembro",
    "October": "Outubro", "November": "Novembro", "December": "Dezembro"
}

LIGA_LABELS = {
    "battle": "Battle 8min",
    "h2h": "H2H GG 8min",
    "todas": "Geral",
}

from telegram import InlineKeyboardButton

#Geral - Botões
informacoes = "ℹ️ Mais Informações"
fazer_parte = "✅ Fazer Parte"
duvidas = "❓ Tire suas dúvidas"

#Texto Geral
duvidas_texto = "Contate-nos com suas dúvidas pelos meios abaixo:"
# Botões comuns de dúvidas
duvidas_keyboard = [
    [InlineKeyboardButton("Telegram", url="https://t.me/enzou_stk")],
    [InlineKeyboardButton("WhatsApp", url="https://wa.me/message/AXZSBKJI6EDTA1")],
]

#Broker
titulo_broker = "🤖 Broker 🤖"
descricao_broker = "🤖 Investimentos Automáticos"
info_broker = (
    "O que é o Broker?\n\n"
    "O cliente manda sua conta para a Striker, que realiza todos os investimentos até a limitação da conta. "
    "Nesse momento, o cliente é responsável por sacar o montante final da conta.\n\n"
    "⁉️Informações Principais\n\n"
    "▫️Site usado: bet365;\n"
    "▫️Lucro é repartido ao limitar a conta;\n"
    "▫️Caso a conta termine no prejuízo, não haverá nenhuma compensação até o cliente recuperar o número de unidades em prejuízo;\n"
    "▫️Em caso de inatividade prolongada do cliente, a Striker reserva o direito de passar a vaga dele adiante com um aviso prévio de 24h.\n\n"
    "💰 Financeiro:\n\n"
    "▫️Divisão dos Lucros: 50% Striker / 50% Cliente\n"
    "▫️Banca Mínima: R$5.000\n"
    "▫️Divisão de Banca: 50 a 100u\n"
    "▫️Stake Mínima: R$50\n"
    "▫️Divisão de eventuais perdas: Não.\n\n"
    "💰 Informações Adicionais:\n\n"
    "▫️O cliente não deve acessar a conta durante a operação.\n"
    "▫️Caso queira saber o saldo da conta, basta perguntar à equipe Striker.\n"
    "▫️O Uso de eventuais bônus e créditos de apostas faz parte das operações normais e é de posse da Equipe Striker.\n"
    


)

#Canal VIP
titulo_vip = "💎 Canal VIP 💎"
descricao_vip= "💎 O Melhor do FIFA em um Único Canal"
join_vip = "Em breve!"
info_vip = (
    "Receba em seu Telegram as Melhores Apostas da Striker\n\n"
    "Entrar no VIP Garante Acesso ao Canal VIP e ao Canal Hot Tips\n\n"
    "Sobre o VIP:\n\n"
    "Horário: 24h/d\n"
    "Mercado: Gols Asiáticos\n"
    "Não usamos aba Pré-evento\n"
    "Divisão de Banca Recomendada: 100u\n"
    "Não usamos software de terceiros para enviar/fazer apostas\n"
    "Liga: Esoccer Battle - 8 mins play\n\n"
    "O que é o canal Hot Tips?\n\n"
    "O Canal Hot Tips é uma vertende das Apostas do Canal VIP que tendem a capturar um ROI mais alto e resultados mais estáveis em menos entradas. A lucratividade tende a ser mendo em relação ao Canal VIP Tradicional, porém, temos um ROI maior e um volume menor."
)

#Canal Free
titulo_free = "🆓 Canal Gratuito"
descricao_free = "Legenda Free"
join_free = "Join Free"
info_free = "Info Free"

PRODUTOS_INFO = {
    "broker": {
        "titulo": titulo_broker,
        "descricao": descricao_broker,
        "opcoes": [
            {"texto": informacoes, "callback_data": "info_broker"},
            {"texto": fazer_parte, "callback_data": "join_broker"},
            {"texto": duvidas, "callback_data": "faq_broker"},
        ],
        "acoes": {
            "info": info_broker,
            "join": "Entre no Broker",
            "faq": duvidas_texto,
        },
    },
    "canal_vip": {
        "titulo": titulo_vip,
        "descricao": descricao_vip,
        "opcoes": [
            {"texto": informacoes, "callback_data": "info_canal_vip"},
            {"texto": fazer_parte, "callback_data": "join_canal_vip"},
            {"texto": duvidas, "callback_data": "faq_canal_vip"},
        ],
        "acoes": {
            "info": info_vip,
            "join": join_vip,
            "faq": duvidas_texto,
        },
    },
    "canal_gratuito": {
        "titulo": titulo_free,
        "descricao": descricao_free,
        "opcoes": [
            {"texto": informacoes, "callback_data": "info_canal_gratuito"},
            {"texto": fazer_parte, "callback_data": "join_canal_gratuito"},
            {"texto": duvidas, "callback_data": "faq_canal_gratuito"},
        ],
        "acoes": {
            "info": info_free,
            "join": join_free,
            "faq": duvidas_texto,
        },
    },
}
              
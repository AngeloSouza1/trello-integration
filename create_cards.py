import os
import requests
from dotenv import load_dotenv

# Carregar credenciais do .env
load_dotenv()

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")

# Pegar a primeira lista do board
LISTS_URL = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
response = requests.get(LISTS_URL, params=params)

if response.status_code == 200:
    lists = response.json()
    LIST_ID = lists[0]["id"]  # Pegando a primeira lista do board
else:
    print("Erro ao buscar as listas:", response.text)
    exit()

# Criando 10 cards de teste com descrições variadas
cards = [
     {
            "name": "📦 Implementar API de Pagamentos",
            "desc": """Objetivo: Desenvolver e integrar um sistema de pagamentos seguro.
            
Passos:
1️⃣ Escolher um gateway de pagamento confiável (ex: Stripe, PayPal).
2️⃣ Criar credenciais e configurar ambiente de teste.
3️⃣ Desenvolver a API de pagamentos e integração com backend.
4️⃣ Implementar webhook para capturar transações em tempo real.
5️⃣ Testar fluxo completo de compra e realizar simulações.

⚠️ Bloqueios possíveis: Erros na configuração do webhook, rejeição de transações, taxas inesperadas do gateway.
"""
        },
        {
            "name": "🛠 Refatorar Código Backend",
            "desc": """Objetivo: Melhorar a organização e a eficiência do código backend.

Passos:
1️⃣ Identificar trechos de código duplicados e refatorar para reaproveitamento.
2️⃣ Melhorar a estrutura dos módulos e aplicar padrões de design.
3️⃣ Otimizar consultas SQL para reduzir tempo de resposta.
4️⃣ Revisar logs e implementar melhorias na monitoração de erros.
5️⃣ Garantir cobertura de testes após as alterações.

⚠️ Bloqueios possíveis: Refatoração pode quebrar funcionalidades existentes, necessidade de reescrita de testes.
"""
        },
        {
            "name": "📢 Criar Estratégia de Marketing Digital",
            "desc": """Objetivo: Elaborar um plano para aumentar a visibilidade do produto.

Passos:
1️⃣ Definir público-alvo e persona.
2️⃣ Criar cronograma de postagens e campanhas.
3️⃣ Testar diferentes formatos de anúncios e medir conversões.
4️⃣ Otimizar SEO para melhorar tráfego orgânico.
5️⃣ Implementar automação de marketing para retenção de clientes.

⚠️ Bloqueios possíveis: Baixa taxa de conversão inicial, necessidade de ajustes em campanhas pagas.
"""
        }
    
]

# Criar os cards no Trello
for card in cards:
    CREATE_CARD_URL = "https://api.trello.com/1/cards"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "idList": LIST_ID,
        "name": card["name"],
        "desc": card["desc"]
    }
    response = requests.post(CREATE_CARD_URL, params=params)
    if response.status_code == 200:
        print(f"✅ Card '{card['name']}' criado com sucesso!")
    else:
        print(f"❌ Erro ao criar '{card['name']}':", response.text)

import os
import requests
from dotenv import load_dotenv

# Carregar credenciais do .env
load_dotenv()

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")

# Buscar todas as listas do board
LISTS_URL = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
response = requests.get(LISTS_URL, params=params)

if response.status_code != 200:
    print("❌ Erro ao buscar as listas:", response.text)
    exit()

lists = response.json()

# Definir ID da lista "Concluído"
list_done_id = None
for trello_list in lists:
    if trello_list["name"].strip().lower() == "concluído":
        list_done_id = trello_list["id"]
        print(f"✅ Lista 'Concluído' detectada com ID: {list_done_id}")

# Estrutura de cards para cada lista (10 cards por lista)
tasks_per_category = [
    [  # 📌 Lista: Desenvolvimento de Software
        {
            "name": "💻 Implementar API RESTful",
            "desc": """Criar uma API RESTful com autenticação JWT.

Passos:
1️⃣ Criar rotas para CRUD de usuários.
2️⃣ Implementar autenticação segura com JWT.
3️⃣ Testar integração com o frontend.
4️⃣ Criar logs para monitoramento de erros.
5️⃣ Publicar API e documentar endpoints.

⚠️ Bloqueios possíveis: Problemas na autenticação, conflitos de versão na API."""
        },
        {
            "name": "🛠 Otimizar Banco de Dados",
            "desc": """Melhorar a performance das consultas SQL.

Passos:
1️⃣ Analisar queries lentas e identificar gargalos.
2️⃣ Criar índices nas tabelas mais acessadas.
3️⃣ Implementar cache para reduzir tempo de resposta.
4️⃣ Testar performance antes e depois das otimizações.
5️⃣ Monitorar a estabilidade após mudanças.

⚠️ Bloqueios possíveis: Erros na criação de índices, necessidade de refatoração."""
        }
    ],
    [  # 📌 Lista: Concluído (tarefas finalizadas)
        {
            "name": "✅ Migrar Servidor para Nova Infraestrutura",
            "desc": """Finalizado: Migração de ambiente concluída com sucesso.

Passos Concluídos:
✔️ Configurar novo servidor.
✔️ Transferir dados e arquivos críticos.
✔️ Testar aplicações para garantir funcionalidade.
✔️ Atualizar configurações DNS e verificar acessibilidade.
✔️ Monitorar performance pós-migração.

🎉 Este projeto foi finalizado com êxito!"""
        },
        {
            "name": "✅ Implementação de Dashboard Analítico",
            "desc": """Finalizado: Novo painel analítico entregue.

Passos Concluídos:
✔️ Criar gráficos interativos para visualização de métricas.
✔️ Implementar banco de dados para coleta de estatísticas.
✔️ Otimizar queries para análise em tempo real.
✔️ Integrar API para atualização automática de dados.
✔️ Realizar testes finais e coletar feedbacks.

🎉 Dashboard em produção e operando corretamente!"""
        }
    ]
]

# Criar cards no Trello
def create_card_with_comment(list_id, card):
    """Cria um card no Trello e adiciona um comentário relevante"""
    CREATE_CARD_URL = "https://api.trello.com/1/cards"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "idList": list_id,
        "name": card["name"],
        "desc": card["desc"]
    }
    response = requests.post(CREATE_CARD_URL, params=params)

    if response.status_code == 200:
        card_data = response.json()
        card_id = card_data["id"]
        print(f"✅ Card '{card['name']}' criado com sucesso!")

        # Se o card estiver na lista "Concluído", adicionar etiqueta e checklist
        if list_id == list_done_id:
            add_label_to_card(card_id, "Finalizado", "green")
            add_checklist_to_card(card_id)

        # Adicionar comentário no card
        add_comment_to_card(card_id, f"🔎 Revisão concluída para: {card['name']}")
    else:
        print(f"❌ Erro ao criar '{card['name']}':", response.text)


def add_comment_to_card(card_id, comment_text):
    """Adiciona um comentário a um card do Trello"""
    COMMENT_URL = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "text": comment_text
    }
    response = requests.post(COMMENT_URL, params=params)

    if response.status_code == 200:
        print(f"💬 Comentário adicionado ao card!")
    else:
        print(f"❌ Erro ao adicionar comentário ao card:", response.text)


def add_label_to_card(card_id, label_name, color):
    """Adiciona uma etiqueta a um card do Trello"""
    LABEL_URL = f"https://api.trello.com/1/cards/{card_id}/labels"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "name": label_name,
        "color": color
    }
    response = requests.post(LABEL_URL, params=params)

    if response.status_code == 200:
        print(f"🏷️ Etiqueta '{label_name}' adicionada ao card!")
    else:
        print(f"❌ Erro ao adicionar etiqueta:", response.text)


def add_checklist_to_card(card_id):
    """Adiciona um checklist a um card do Trello e marca todas as tarefas como concluídas"""
    CHECKLIST_URL = f"https://api.trello.com/1/cards/{card_id}/checklists"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "name": "Tarefas Concluídas"
    }
    response = requests.post(CHECKLIST_URL, params=params)

    if response.status_code == 200:
        checklist_id = response.json()["id"]
        print(f"✅ Checklist adicionado ao card!")
        add_checklist_items(checklist_id)
    else:
        print(f"❌ Erro ao adicionar checklist:", response.text)


def add_checklist_items(checklist_id):
    """Marca todas as tarefas como concluídas no checklist"""
    items = ["Tarefa 1", "Tarefa 2", "Tarefa 3", "Tarefa 4", "Tarefa 5"]

    for item in items:
        CHECKITEM_URL = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems"
        params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN,
            "name": item,
            "checked": "true"  # Marcar como concluído
        }
        response = requests.post(CHECKITEM_URL, params=params)
        if response.status_code == 200:
            print(f"✔️ Item '{item}' marcado como concluído!")
        else:
            print(f"❌ Erro ao adicionar item '{item}':", response.text)


# Criar 10 cards para cada lista disponível no Trello
for i, trello_list in enumerate(lists):
    list_id = trello_list["id"]
    list_name = trello_list["name"]

    print(f"\n🔹 Criando cards para a lista '{list_name}'...")

    tasks = tasks_per_category[i % len(tasks_per_category)]
    for card in tasks:
        create_card_with_comment(list_id, card)

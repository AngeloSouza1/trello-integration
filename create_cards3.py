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

# Estrutura de **5 cards detalhados por lista**
tasks_template = [
    {
        "name": "💻 Implementar API RESTful",
        "desc": """**Objetivo:** Criar uma API RESTful eficiente e segura.

**Requisitos:**
- Suporte a autenticação JWT
- CRUD completo de usuários e permissões
- Documentação via Swagger ou Postman

**Passos para implementação:**
1️⃣ Criar banco de dados e definir schema.
2️⃣ Criar rotas GET, POST, PUT e DELETE para os usuários.
3️⃣ Implementar autenticação e autorização com JWT.
4️⃣ Criar testes automatizados para validação.
5️⃣ Documentar e publicar API.

⚠️ **Possíveis Bloqueios:** Erros de integração com frontend, necessidade de ajustes na segurança."""
    },
    {
        "name": "🛠 Otimizar Banco de Dados",
        "desc": """**Objetivo:** Melhorar a performance e escalabilidade do banco.

**Requisitos:**
- Identificação de queries lentas
- Criação de índices para otimização
- Implementação de cache em camadas

**Passos para otimização:**
1️⃣ Analisar logs de consultas para identificar gargalos.
2️⃣ Criar índices eficientes em colunas estratégicas.
3️⃣ Implementar cache para reduzir carga no banco.
4️⃣ Testar melhorias em ambiente de homologação.
5️⃣ Monitorar métricas de desempenho.

⚠️ **Possíveis Bloqueios:** Impacto negativo em queries existentes, necessidade de refatoração."""
    },
    {
        "name": "📊 Criar Dashboard Analítico",
        "desc": """**Objetivo:** Criar um painel de métricas em tempo real.

**Requisitos:**
- Conexão com banco de dados e APIs externas
- Gráficos interativos e filtros avançados
- Suporte a exportação de relatórios

**Passos para criação:**
1️⃣ Definir KPIs e métricas relevantes.
2️⃣ Criar layout do painel e design responsivo.
3️⃣ Implementar consultas otimizadas no backend.
4️⃣ Criar visualizações dinâmicas com gráficos interativos.
5️⃣ Testar usabilidade e performance.

⚠️ **Possíveis Bloqueios:** Baixo desempenho em queries, dificuldades na integração com APIs."""
    },
    {
        "name": "📦 Automatizar Deploy no AWS",
        "desc": """**Objetivo:** Criar um pipeline de CI/CD para automação de deploys.

**Requisitos:**
- Uso de GitHub Actions ou Jenkins
- Deploy automático na AWS (Lambda, EC2 ou S3)
- Monitoramento e rollback automático

**Passos para implementação:**
1️⃣ Configurar pipeline no repositório.
2️⃣ Criar scripts para automação de build e deploy.
3️⃣ Testar integração contínua com ambiente de staging.
4️⃣ Implementar logs e alertas para falhas.
5️⃣ Validar segurança e permissões de acesso.

⚠️ **Possíveis Bloqueios:** Erros de autenticação AWS, necessidade de ajustes nos scripts."""
    },
    {
        "name": "🔐 Melhorar Segurança do Sistema",
        "desc": """**Objetivo:** Fortalecer a segurança da aplicação.

**Requisitos:**
- Implementação de autenticação multifator
- Encriptação de dados sensíveis
- Monitoramento de acessos suspeitos

**Passos para implementação:**
1️⃣ Adicionar autenticação multifator (2FA).
2️⃣ Implementar logs para auditoria de acessos.
3️⃣ Revisar permissões de usuários e tokens de acesso.
4️⃣ Implementar encriptação de dados críticos.
5️⃣ Realizar testes de segurança e simulações de ataques.

⚠️ **Possíveis Bloqueios:** Complexidade na implementação, impacto na experiência do usuário."""
    }
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


# Criar 5 cards para cada lista no Trello
for trello_list in lists:
    list_id = trello_list["id"]
    list_name = trello_list["name"]

    print(f"\n🔹 Criando 5 cards para a lista '{list_name}'...")

    for card in tasks_template:
        create_card_with_comment(list_id, card)

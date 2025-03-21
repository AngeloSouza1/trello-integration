import os
import requests
import google.generativeai as genai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime


# Carregar variáveis do .env
load_dotenv()

# Credenciais do Trello e Google Gemini
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")

# Credenciais de e-mail
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")

# Verificar se todas as credenciais foram carregadas corretamente
if not all([TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_BOARD_ID, GEMINI_API_KEY, EMAIL_REMETENTE, EMAIL_DESTINATARIO, EMAIL_SENHA]):
    raise ValueError("❌ ERRO: Algumas credenciais não foram carregadas. Verifique seu arquivo .env.")

# Configurar a API do Google Gemini
genai.configure(api_key=GEMINI_API_KEY)


# Função para buscar os cards de uma lista específica no Trello e retornar o nome do board
def get_trello_cards(list_name="A FAZER"):
    """
    Busca os cards de uma lista específica no Trello e retorna o nome do quadro.

    :param list_name: Nome da lista no Trello para buscar os cards.
    :return: Nome do quadro, Nome da lista e Lista de cards.
    """
    try:
        # Buscar informações do board
        board_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}"
        params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
        response = requests.get(board_url, params=params)

        if response.status_code != 200:
            print(f"❌ Erro ao buscar informações do board: {response.text}")
            return None, None, []

        board_name = response.json().get("name", "Desconhecido")

        # Obter todas as listas do board
        lists_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
        response = requests.get(lists_url, params=params)

        if response.status_code != 200:
            print(f"❌ Erro ao buscar listas do Trello: {response.text}")
            return board_name, None, []

        lists = response.json()

        # Filtrar a lista pelo nome
        list_id = next((l["id"] for l in lists if l["name"].strip().lower() == list_name.strip().lower()), None)

        if not list_id:
            print(f"⚠️ Nenhuma lista encontrada com o nome '{list_name}'. Verifique se o nome está correto.")
            return board_name, list_name, []

        # Buscar os cards dessa lista específica
        cards_url = f"https://api.trello.com/1/lists/{list_id}/cards"
        response = requests.get(cards_url, params=params)

        if response.status_code == 200:
            cards = response.json()
            if not cards:
                print(f"⚠️ Nenhum card encontrado na lista '{list_name}'.")
            return board_name, list_name, cards
        else:
            print(f"❌ Erro ao buscar os cards da lista '{list_name}': {response.text}")
            return board_name, list_name, []

    except Exception as e:
        print(f"❌ Erro inesperado ao buscar os cards: {str(e)}")
        return None, None, []



# Função para analisar os cards com Google Gemini
def analyze_cards(cards):
    try:
        card_texts = "\n".join([f"- {card['name']}: {card['desc']}" for card in cards if card.get('desc')])

        if not card_texts:
            return "⚠️ Nenhuma descrição de card encontrada. Adicione descrições aos cards no Trello."

        prompt = f"""
        Você é um assistente de produtividade. Analise os seguintes cards do Trello e forneça insights:
        {card_texts}

        Sugira melhorias, identifique bloqueios e classifique as tarefas por prioridade.
        """

        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content(prompt)

        return response.text.strip()  # Retorna o texto gerado pelo Gemini
    except Exception as e:
        return f"❌ Erro ao processar insights com Gemini: {str(e)}"

# Função para criar um novo card no Trello com os insights do Gemini
def create_insights_card(insights):
    """Cria um card de insights no Trello, arquivando um existente caso haja."""

    if not insights or "❌" in insights or "⚠️" in insights:
        print("⚠️ Nenhum insight válido para publicar no Trello.")
        return

    try:
        # Buscar todas as listas do board no Trello
        lists_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
        params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
        response = requests.get(lists_url, params=params)

        if response.status_code != 200:
            print("❌ Erro ao buscar listas do Trello:", response.text)
            return

        lists = response.json()
        if not lists:
            print("⚠️ Nenhuma lista encontrada no board do Trello.")
            return

        # Procurar a lista específica "Tarefas"
        target_list_name = "Tarefas"
        list_id = next((l["id"] for l in lists if l["name"].strip().lower() == target_list_name.strip().lower()), None)

        if not list_id:
            print(f"⚠️ A lista '{target_list_name}' não foi encontrada no Trello. Verifique o nome exato.")
            return

        print(f"✅ Lista '{target_list_name}' encontrada! Criando insights nela...")

        # Buscar os cards da lista para verificar se já existe um de insights
        cards_url = f"https://api.trello.com/1/lists/{list_id}/cards"
        response = requests.get(cards_url, params=params)

        if response.status_code != 200:
            print("❌ Erro ao buscar cards da lista:", response.text)
            return

        cards = response.json()
        existing_insight_card = next((card for card in cards if "📌 Insights de Produtividade" in card["name"]), None)

        # Se já existir um card de insights, arquivá-lo antes de criar um novo
        if existing_insight_card:
            archive_url = f"https://api.trello.com/1/cards/{existing_insight_card['id']}/closed"
            archive_params = {**params, "value": "true"}
            archive_response = requests.put(archive_url, params=archive_params)

            if archive_response.status_code == 200:
                print(f"✅ Card de insights anterior arquivado: {existing_insight_card['name']}")
            else:
                print(f"❌ Erro ao arquivar o card de insights antigo:", archive_response.text)

        # Gerar a data e hora atual no formato DD/MM/YYYY HH:MM
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Criar o novo card de insights com a data e hora
        create_card_url = "https://api.trello.com/1/cards"
        params.update({
            "idList": list_id,
            "name": f"📌 Insights de Produtividade - {now}",
            "desc": insights
        })

        response = requests.post(create_card_url, params=params)
        if response.status_code == 200:
            print(f"✅ Novo card de insights publicado com sucesso na lista '{target_list_name}'!")
        else:
            print("❌ Erro ao criar card no Trello:", response.text)

    except Exception as e:
        print("❌ Erro inesperado ao criar insights no Trello:", str(e))

        

# Função para enviar insights por e-mail com nome do board e lista
def send_email(insights, board_name, list_name, board_report):
    """Envia e-mail formatado com insights e relatório do Trello."""

    if not insights or "❌" in insights or "⚠️" in insights:
        print("⚠️ Nenhum insight válido para enviar por e-mail.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = EMAIL_DESTINATARIO
        msg["Subject"] = f"📌 Relatório Trello - {board_name} ({list_name})"

        # Remover qualquer formatação de negrito nos insights
        insights_clean = insights.replace("*", "")

        corpo_email = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                h3 {{
                    color: #007BFF;
                    border-bottom: 2px solid #007BFF;
                    padding-bottom: 5px;
                }}
                p {{
                    margin: 5px 0;
                }}
                .section {{
                    background: #f9f9f9;
                    padding: 15px;
                    margin-top: 10px;
                    border-radius: 8px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                table, th, td {{
                    border: 1px solid #ddd;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #007BFF;
                    color: white;
                }}
                .alert {{
                    color: #D9534F;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <h2>📌 Relatório de Produtividade - {board_name}</h2>
            <h3>📋 Lista analisada: {list_name}</h3>

            <div class="section">
                <h4>🔹 Insights de Tarefas</h4>
                <p>{insights_clean.replace('\n', '<br>')}</p>
            </div>

            <div class="section">
                <h3>📊 Relatório Completo do Quadro</h3>
                <p>{board_report.replace('**', '').replace('\n', '<br>')}</p>
            </div>

            <br>
            <p style="font-size: 12px; color: gray;">Este e-mail foi gerado automaticamente pelo sistema de automação Trello + Gemini.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(corpo_email, "html"))

        # Configuração do SMTP (Usando SSL)
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        server.quit()

        print(f"✅ E-mail enviado com sucesso para {EMAIL_DESTINATARIO} sobre '{list_name}' no quadro '{board_name}'!")

    except Exception as e:
        print("❌ Erro ao enviar e-mail:", str(e))

def generate_board_report():
    """Gera um relatório completo do quadro do Trello, analisando todas as listas e cards."""

    lists_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.get(lists_url, params=params)

    if response.status_code != 200:
        return f"❌ Erro ao buscar listas do Trello: {response.text}"

    lists = response.json()
    if not lists:
        return "⚠️ Nenhuma lista encontrada no quadro do Trello."

    total_cards = 0
    completed_cards = 0
    pending_cards = 0
    blocked_cards = 0
    tasks_per_list = {}

    # Inicializando a variável report corretamente
    report = "📊 Relatório do Quadro Trello\n\n"
    report += f"🔹 Total de listas: {len(lists)}\n\n"

    for lista in lists:
        list_name = lista["name"]
        list_id = lista["id"]

        # Buscar cards dessa lista
        cards_url = f"https://api.trello.com/1/lists/{list_id}/cards"
        response = requests.get(cards_url, params=params)

        if response.status_code != 200:
            continue

        cards = response.json()

        # Filtrar os cards, removendo o de insights
        real_cards = [card for card in cards if "📌 Insights de Produtividade" not in card["name"]]

        tasks_per_list[list_name] = len(real_cards)
        total_cards += len(real_cards)

        # Contar cards concluídos e pendentes
        for card in real_cards:
            if "done" in list_name.lower() or "concluído" in list_name.lower():
                completed_cards += 1
            else:
                pending_cards += 1
            
            # Verificar bloqueios (sem descrição ou sem responsáveis)
            if not card.get("desc") or not card.get("idMembers"):
                blocked_cards += 1

    # Percentual de progresso
    progress_percentage = (completed_cards / total_cards * 100) if total_cards > 0 else 0

    report += f"✅ Total de tarefas: {total_cards}\n"
    report += f"✔️ Concluídas: {completed_cards} ({progress_percentage:.2f}%)\n"
    report += f"⏳ Pendentes: {pending_cards}\n"
    report += f"⚠️ Bloqueios detectados (sem descrição ou responsáveis): {blocked_cards}\n\n"

    report += "📌 Distribuição de tarefas por lista:\n"
    for list_name, count in tasks_per_list.items():
        report += f"- {list_name}: {count} tarefas\n"

    # Sugestões baseadas nos dados coletados
    report += "\n💡 Sugestões para Melhorar o Fluxo de Trabalho:\n"
    if progress_percentage < 50:
        report += "- O progresso do quadro está abaixo de 50%. Considere revisar prioridades.\n"
    if blocked_cards > 0:
        report += "- Existem tarefas sem responsáveis ou descrição. Definir donos e escopo pode agilizar a entrega.\n"
    if completed_cards == 0:
        report += "- Nenhuma tarefa foi concluída ainda. Avalie os bloqueios.\n"

    return report
        
        



    

# Definir a lista desejada no Trello
LISTA_ANALISADA = "Tarefas"  # Altere para a lista que deseja analisar

# Executar a análise
board_name, list_name, cards = get_trello_cards(LISTA_ANALISADA)

if cards:
    insights = analyze_cards(cards)
    print("\n🔹 Insights do Gemini:\n", insights)
    
    # Criar um card no Trello com os insights
    create_insights_card(insights)

    # Gerar o relatório completo do quadro Trello
    board_report = generate_board_report()
    print("\n📊 Relatório do Quadro Trello:\n", board_report)

    # Criar um card no Trello com o relatório
    if board_report.strip():
        create_insights_card(board_report)

    # Enviar os insights e o relatório por e-mail
    send_email(insights, board_name, list_name, board_report)

else:
    print(f"⚠️ Nenhum card encontrado na lista '{LISTA_ANALISADA}' do quadro '{board_name}'.")




import os
import io
import re
import requests
import google.generativeai as genai
import smtplib
import matplotlib.pyplot as plt
import tkinter as tk
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage  
from dotenv import load_dotenv
from datetime import datetime
from collections import Counter
from tkinter import ttk, messagebox


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


# Função para criar um novo card no Trello com os insights do Gemini
def create_insights_card(insights, list_id, list_name):
    """Cria um card de insights no Trello na lista específica onde os cards foram analisados."""

    if not insights or "❌" in insights or "⚠️" in insights:
        print("⚠️ Nenhum insight válido para publicar no Trello.")
        return

    try:
        # Gerar a data e hora atual no formato DD/MM/YYYY HH:MM
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Buscar os cards da lista para verificar se já existe um de insights
        cards_url = f"https://api.trello.com/1/lists/{list_id}/cards"
        params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
        response = requests.get(cards_url, params=params)

        if response.status_code != 200:
            print(f"❌ Erro ao buscar cards da lista '{list_name}':", response.text)
            return

        cards = response.json()
        existing_insight_card = next((card for card in cards if f"📌 Insights e Recomendações -> {list_name}" in card["name"]), None)

        # Se já existir um card de insights, arquivá-lo antes de criar um novo
        if existing_insight_card:
            archive_url = f"https://api.trello.com/1/cards/{existing_insight_card['id']}/closed"
            archive_params = {**params, "value": "true"}
            archive_response = requests.put(archive_url, params=archive_params)

            if archive_response.status_code == 200:
                print(f"✅ Card de insights anterior arquivado na lista '{list_name}': {existing_insight_card['name']}")
            else:
                print(f"❌ Erro ao arquivar o card de insights antigo:", archive_response.text)

        # Criar o novo card de insights na mesma lista analisada
        create_card_url = "https://api.trello.com/1/cards"
        params.update({
            "idList": list_id,
            "name": f"📌 Insights e Recomendações -> {list_name} ({now})",
            "desc": insights
        })

        response = requests.post(create_card_url, params=params)
        if response.status_code == 200:
            print(f"✅ Novo card de insights publicado com sucesso na lista '{list_name}'!")
        else:
            print(f"❌ Erro ao criar card no Trello na lista '{list_name}':", response.text)

    except Exception as e:
        print(f"❌ Erro inesperado ao criar insights no Trello: {str(e)}")


def generate_charts(completed_tasks, pending_tasks, blocked_tasks, tasks_per_list):
    """Gera múltiplos gráficos para análise do Trello e retorna um dicionário com imagens em buffer."""
    img_buffers = {}

    # 📊 Gráfico 1: Status das Tarefas (Concluídas, Pendentes, Bloqueadas)
    total_tasks = completed_tasks + pending_tasks + blocked_tasks

    if total_tasks > 0:
        fig, ax = plt.subplots()
        labels = ["Concluídas", "Pendentes", "Bloqueadas"]
        values = [completed_tasks, pending_tasks, blocked_tasks]
        colors = ["#28a745", "#ffc107", "#dc3545"]  # Verde, Amarelo, Vermelho
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors, shadow=True)
        ax.set_title("📊 Status das Tarefas")
        
        # Melhorar legibilidade
        for text in texts + autotexts:
            text.set_fontsize(12)

        img_buffer1 = io.BytesIO()
        plt.savefig(img_buffer1, format="png", bbox_inches="tight")
        plt.close(fig)  # Fecha o gráfico para liberar memória
        img_buffer1.seek(0)  # Retornar ao início do buffer
        img_buffers["status_tarefas"] = img_buffer1
    else:
        print("⚠️ Nenhuma tarefa registrada. O gráfico de status será omitido.")

    # 📊 Gráfico 2: Distribuição de Tarefas por Lista
    if tasks_per_list and sum(tasks_per_list.values()) > 0:
        fig, ax = plt.subplots(figsize=(8, 5))
        list_names = list(tasks_per_list.keys())
        task_counts = list(tasks_per_list.values())

        bars = ax.bar(list_names, task_counts, color="#007BFF")

        ax.set_xlabel("Listas")
        ax.set_ylabel("Número de Tarefas")
        ax.set_title("📌 Distribuição de Tarefas por Lista")
        plt.xticks(rotation=45, ha="right")

        # Exibir valores sobre as barras
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height}", 
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5), 
                        textcoords="offset points",
                        ha="center", 
                        fontsize=12, 
                        color="black")

        img_buffer2 = io.BytesIO()
        plt.savefig(img_buffer2, format="png", bbox_inches="tight")
        plt.close(fig)  # Fecha o gráfico para liberar memória
        img_buffer2.seek(0)  # Retornar ao início do buffer
        img_buffers["distribuicao_listas"] = img_buffer2
    else:
        print("⚠️ Nenhuma tarefa registrada nas listas. O gráfico de distribuição será omitido.")

    return img_buffers




def generate_board_report(available_lists):
    """Gera um relatório completo do quadro do Trello, analisando todas as listas e cards."""

    lists_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.get(lists_url, params=params)

    if response.status_code != 200:
        return f"❌ Erro ao buscar listas do Trello: {response.text}", 0, 0, 0, {}

    lists = response.json()
    if not lists:
        return "⚠️ Nenhuma lista encontrada no quadro do Trello.", 0, 0, 0, {}

    total_cards = 0
    completed_cards = 0
    pending_cards = 0
    blocked_cards = 0
    tasks_per_list = {list_name: 0 for list_name in available_lists.values()}  # Inicializa a contagem

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

        # Classificar corretamente os cards
        for card in real_cards:
            card_name = card.get("name", "").lower()
            card_desc = card.get("desc", "").lower()

            if any(keyword in list_name.lower() for keyword in ["concluído", "finalizado", "done"]):
                completed_cards += 1
            elif any(keyword in list_name.lower() for keyword in ["pendente", "em andamento", "to do", "doing"]):
                pending_cards += 1
            else:
                blocked_cards += 1  # Se não for concluída nem pendente, considera bloqueada

    # **Correção na distribuição de porcentagens**
    completed_percentage = (completed_cards / total_cards * 100) if total_cards > 0 else 0
    pending_percentage = (pending_cards / total_cards * 100) if total_cards > 0 else 0
    blocked_percentage = (blocked_cards / total_cards * 100) if total_cards > 0 else 0

    report += f"✅ Total de tarefas: {total_cards}\n"
    report += f"✔️ Concluídas: {completed_cards} ({completed_percentage:.2f}%)\n"
    report += f"⏳ Pendentes: {pending_cards} ({pending_percentage:.2f}%)\n"
    report += f"⚠️ Bloqueadas: {blocked_cards} ({blocked_percentage:.2f}%)\n\n"

    report += "📌 Distribuição de tarefas por lista:\n"
    for list_name, count in tasks_per_list.items():
        report += f"- {list_name}: {count} tarefas\n"

    # Sugestões baseadas nos dados coletados
    report += "\n💡 Sugestões para Melhorar o Fluxo de Trabalho:\n"
    if completed_percentage < 50:
        report += "- O progresso do quadro está abaixo de 50%. Considere revisar prioridades.\n"
    if blocked_cards > 0:
        report += "- Existem tarefas sem responsáveis ou descrição. Definir donos e escopo pode agilizar a entrega.\n"
    if completed_cards == 0:
        report += "- Nenhuma tarefa foi concluída ainda. Avalie os bloqueios.\n"

    return report, completed_cards, pending_cards, blocked_cards, tasks_per_list



# Função para buscar os detalhes completos dos cards, incluindo comentários
def get_card_details(card_id):
    """
    Obtém detalhes completos de um card, incluindo seus comentários.
    
    :param card_id: ID do card no Trello.
    :return: Texto concatenado com nome, descrição e comentários do card.
    """
    url = f"https://api.trello.com/1/cards/{card_id}/actions"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "filter": "commentCard",  # Filtra apenas comentários
        "fields": "data"
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"⚠️ Erro ao buscar comentários do card {card_id}: {response.text}")
        return ""

    comments = response.json()
    comment_texts = [f"- {c['data']['text']}" for c in comments if "text" in c["data"]]

    return "\n".join(comment_texts)



# Função para analisar os cards com Google Gemini
def analyze_cards(cards, list_name, available_lists):
    try:
        if not cards:
            return f"⚠️ Nenhuma tarefa encontrada para análise na lista '{list_name}'."

        # Criar a estrutura para separar os insights por lista (caso "Todas" tenha sido escolhida)
        insights_text = ""
        cards_by_list = {}

        for card in cards:
            list_name_card = available_lists.get(card.get("idList"), "Lista Desconhecida")
            task_name = card["name"]
            description = card.get("desc", "Sem descrição disponível")
            last_activity = card.get("dateLastActivity", "Sem dados")
            members = card.get("idMembers", [])
            labels = [label["name"] for label in card.get("labels", [])]
            comments = [action["data"]["text"] for action in card.get("actions", []) if "text" in action["data"]]

            # Criar um resumo das informações do card
            card_info = f"""
            - **{task_name}**  
              📋 **Descrição**: {description}  
              📅 **Última atividade**: {last_activity}  
              👤 **Responsáveis**: {'Sem responsável' if not members else len(members)}  
              🏷 **Etiquetas**: {', '.join(labels) if labels else 'Nenhuma'}  
              💬 **Comentários**: {len(comments)} registrados  
            """

            # Classificar os insights dentro da lista correta
            if list_name == "Todas":
                if list_name_card not in cards_by_list:
                    cards_by_list[list_name_card] = []
                cards_by_list[list_name_card].append(card_info)
            else:
                insights_text += f"{card_info}\n"

        # Ajustar o título do relatório com base na lista selecionada
        if list_name == "Todas":
            title = "📌 Análise de Tarefas em Todas as Listas: Insights e Recomendações"
        else:
            title = f"📌 Análise de Tarefas na Lista '{list_name}': Insights e Recomendações"

        # Se todas as listas forem analisadas, organizar os insights por lista
        if list_name == "Todas":
            insights_text = "### 📌 Insights por Lista:\n\n"
            for list_name_card, card_texts in cards_by_list.items():
                insights_text += f"#### 📋 Lista: {list_name_card}\n"
                insights_text += "\n".join(card_texts) + "\n\n"

        if not insights_text.strip():
            return f"⚠️ Nenhuma descrição de card encontrada na lista '{list_name}'. Adicione descrições aos cards no Trello."

        # **📌 Prompt otimizado para o Gemini**
        prompt = f"""
        Você é um assistente especialista em produtividade e gestão de tarefas. 
        Sua tarefa é analisar os seguintes cards do Trello e fornecer insights organizados, com tópicos claros.

        ### 📋 Lista analisada: {list_name}

        **Tarefas analisadas:**  
        {insights_text}

        ### 🔍 Checklist de Efetividade  
        Para cada tarefa, analise os seguintes critérios:  
        ✅ **A tarefa possui descrição detalhada?**  
        ✅ **Possui responsável atribuído?**  
        ✅ **Possui prazo definido?**  
        ✅ **Foi concluída dentro do prazo estimado?**  
        ✅ **Teve revisões ou retrabalho?**  
        ✅ **Houve bloqueios ou dificuldades relatadas?**  
        ✅ **A tarefa depende de outra para ser concluída?**  
        ✅ **Está alinhada com as prioridades estratégicas da empresa?**  
        ✅ **O esforço necessário foi adequado?**  
        ✅ **Alguma melhoria pode ser aplicada ao fluxo de trabalho?**  

        📊 **Com base nessa análise, forneça insights organizados:**  
        - **Pontos fortes e positivos das tarefas analisadas**  
        - **Pontos fracos ou gargalos no fluxo de trabalho**  
        - **Recomendações para melhorar eficiência e produtividade**  
        - **Sugestão de priorização (Alta, Média, Baixa)**  
        - **Tempo estimado de conclusão das tarefas baseado em atividades passadas**  
        - **Possíveis dependências e interações entre tarefas**  
        - **Alertas sobre tarefas sem responsáveis ou com bloqueios identificados**  

        **Formato de saída esperado:**  
        - Utilize linguagem objetiva e estratégica.  
        - Separe os insights em tópicos claros e numerados para facilitar a leitura.  
        - Inclua recomendações específicas para otimizar o fluxo de trabalho.  
        """

        # Chamar o modelo Gemini para gerar os insights
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content(prompt)

        return response.text.strip()  # Retorna o texto gerado pelo Gemini

    except Exception as e:
        return f"❌ Erro ao processar insights com Gemini: {str(e)}"




# Função para buscar os cards de uma lista específica no Trello e retornar o nome do board
def get_available_lists():
    """Busca e retorna todas as listas disponíveis no Trello."""
    try:
        lists_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
        params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
        response = requests.get(lists_url, params=params)

        if response.status_code != 200:
            print(f"❌ Erro ao buscar listas do Trello: {response.text}")
            return []

        lists = response.json()
        return lists

    except Exception as e:
        print(f"❌ Erro inesperado ao buscar as listas: {str(e)}")
        return []
    
 
 # 📊 Função para calcular métricas das tarefas
def calculate_task_metrics(cards, available_lists):
    """Calcula o número de tarefas concluídas, pendentes, bloqueadas e a distribuição por lista."""
    completed_tasks = 0
    pending_tasks = 0
    blocked_tasks = 0
    tasks_per_list = {list_name: 0 for list_name in available_lists.values()}  # Inicializar distribuição

    for card in cards:
        list_name = card.get("list_name", "Lista Desconhecida")
        
        # Atualizar a contagem de tarefas por lista
        tasks_per_list[list_name] = tasks_per_list.get(list_name, 0) + 1

        # Determinar status da tarefa
        if "concluído" in list_name.lower() or "done" in list_name.lower():
            completed_tasks += 1
        else:
            pending_tasks += 1

        # Identificar bloqueios (sem descrição ou sem responsáveis)
        if not card.get("desc") or not card.get("idMembers"):
            blocked_tasks += 1

    return completed_tasks, pending_tasks, blocked_tasks, tasks_per_list
 
 
 # Função para enviar insights por e-mail com nome do board e lista

from email.mime.image import MIMEImage
import io
import matplotlib.pyplot as plt

def generate_charts(completed_tasks, pending_tasks, blocked_tasks, tasks_per_list):
    """Gera múltiplos gráficos para análise do Trello."""
    img_buffers = {}

    # 📊 Gráfico 1: Status das Tarefas (Concluídas, Pendentes, Bloqueadas)
    fig, ax = plt.subplots()
    labels = ["Concluídas", "Pendentes", "Bloqueadas"]
    values = [completed_tasks, pending_tasks, blocked_tasks]
    colors = ["#28a745", "#ffc107", "#dc3545"]
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors, shadow=True)
    ax.set_title("📊 Status das Tarefas")

    img_buffer1 = io.BytesIO()
    plt.savefig(img_buffer1, format="png")
    plt.close(fig)
    img_buffers["status_tarefas"] = img_buffer1

    # 📊 Gráfico 2: Distribuição de Tarefas por Lista
    fig, ax = plt.subplots(figsize=(8, 5))
    list_names = list(tasks_per_list.keys())
    task_counts = list(tasks_per_list.values())

    ax.bar(list_names, task_counts, color="#007BFF")
    ax.set_xlabel("Listas")
    ax.set_ylabel("Número de Tarefas")
    ax.set_title("📌 Distribuição de Tarefas por Lista")
    plt.xticks(rotation=45, ha="right")

    img_buffer2 = io.BytesIO()
    plt.savefig(img_buffer2, format="png")
    plt.close(fig)
    img_buffers["distribuicao_listas"] = img_buffer2

    return img_buffers




def format_insights_table(insights):
    """Formata os insights em uma tabela HTML, garantindo que todos os itens sejam incluídos corretamente."""

    table_rows = ""
    lines = insights.split("\n")
    current_criteria = None
    sub_items = []
    processed_data = []

    for line in lines:
        line = line.strip()

        if not line:
            continue  # Ignora linhas vazias

        # Se for um critério novo (ex: "**Sugestão de Priorização:**")
        if line.startswith("**") and line.endswith(":**"):
            # Se houver sub-itens pendentes, adiciona-os antes de mudar de critério
            if sub_items and current_criteria:
                processed_data.append((f"<strong>{current_criteria}</strong>", "<ul>" + "".join(sub_items) + "</ul>"))
                sub_items = []

            current_criteria = line.replace("**", "").strip()

        # Se for um item de lista com marcador (ex: "* Implementar API RESTful")
        elif line.startswith("*") and current_criteria:
            sub_items.append(f"<li>{line.replace('*', '').strip()}</li>")

        # Se for um item de lista numerada (ex: "1. Definir prazos")
        elif line[0].isdigit() and "." in line and current_criteria:
            sub_items.append(f"<li>{line.strip()}</li>")

        # Se for um par chave-valor (ex: "Falta de prazo: O prazo não foi definido.")
        elif ":" in line and not line.startswith("*") and not line[0].isdigit():
            key, value = line.split(":", 1)
            processed_data.append((f"<strong>{key.strip()}</strong>", value.strip()))

        # Se for um critério seguido de um parágrafo (ex: "**5. Tempo Estimado de Conclusão:** Impossível estimar...")
        elif current_criteria and line:
            sub_items.append(f"{line}")

    # Adiciona os últimos sub-itens armazenados na tabela, se existirem
    if sub_items and current_criteria:
        processed_data.append((f"<strong>{current_criteria}</strong>", "<ul>" + "".join(sub_items) + "</ul>"))

    # Gera a tabela HTML
    table_rows = "".join(f"<tr><td>{key}</td><td>{value}</td></tr>" for key, value in processed_data)

    return f"""
    <table class="table-container">
        <tr>
            <th>Critério</th>
            <th>Análise</th>
        </tr>
        {table_rows}
    </table>
    """


def send_email(insights, board_name, list_name, board_report, completed_tasks, pending_tasks, blocked_tasks, tasks_per_list):
    """Envia e-mail formatado com insights detalhados, relatório completo do quadro e gráficos das tarefas."""

    if not insights.strip():
        print("⚠️ Nenhum insight válido para enviar por e-mail.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = EMAIL_DESTINATARIO
        msg["Subject"] = f"📌 Relatório Trello - {board_name}"

        # 📊 Gerar os gráficos e anexá-los
        charts = generate_charts(completed_tasks, pending_tasks, blocked_tasks, tasks_per_list)
        for chart_name, img_buffer in charts.items():
            image = MIMEImage(img_buffer.getvalue(), name=f"{chart_name}.png")
            image.add_header("Content-ID", f"<{chart_name}>")
            msg.attach(image)

        # 📌 Criar tabela de insights formatada corretamente
        insights_table = format_insights_table(insights)

        # 📌 Criar tabela de distribuição de tarefas por lista
        task_distribution = "".join(
            f"<tr><td>{list_name}</td><td>{count}</td></tr>" for list_name, count in tasks_per_list.items()
        )

        # 📌 Criar tabela detalhada do relatório do quadro
        detailed_report_rows = "".join(
            f"<tr><td><strong>{line.split(':')[0]}</strong></td><td>{line.split(':')[1] if ':' in line else line}</td></tr>"
            for line in board_report.split("\n") if line.strip()
        )

        # 📌 Criar tabela de sugestões para melhorar o fluxo de trabalho
        improvement_suggestions = [
            ("📌 Definir prazos", "Atribuir prazos claros para evitar atrasos e melhorar previsibilidade."),
            ("👤 Atribuir responsáveis", "Garantir que todas as tarefas tenham responsáveis para accountability."),
            ("🔄 Evitar tarefas duplicadas", "Consolidar atividades para melhor organização."),
            ("🏷️ Utilizar etiquetas", "Classificar tarefas por prioridade, status ou categoria."),
            ("📅 Revisões periódicas", "Monitorar e ajustar o fluxo de trabalho conforme necessário."),
        ]
        
        improvement_suggestions_table = "".join(
            f"<tr><td><strong>{suggestion}</strong></td><td>{description}</td></tr>"
            for suggestion, description in improvement_suggestions
        )

        # 📌 Corpo do e-mail formatado
        corpo_email = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #333;
                }}
                h2, h3 {{
                    color: #007BFF;
                }}
                .section {{
                    background: #f9f9f9;
                    padding: 15px;
                    margin-top: 10px;
                    border-radius: 8px;
                }}
                .highlight {{
                    font-weight: bold;
                    color: #D9534F;
                }}
                .table-container {{
                    margin-top: 20px;
                    border-collapse: collapse;
                    width: 100%;
                }}
                .table-container th, .table-container td {{
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: left;
                }}
                .table-container th {{
                    background-color: #007BFF;
                    color: white;
                    font-size: 14px;
                }}
                .image-container {{
                    text-align: center;
                    margin-top: 20px;
                }}
                .footer {{
                    font-size: 14px;
                    color: gray;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h2>📌 Relatório Completo do Trello - {board_name}</h2>

            <div class="section">
                <h3>📋 Insights da Lista: {list_name}</h3>
                {insights_table}
            </div>

            <div class="section">
                <h3>📊 Resumo do Quadro</h3>
                <table class="table-container">
                    <tr>
                        <th>Status</th>
                        <th>Quantidade</th>
                    </tr>
                    <tr>
                        <td>✔️ Concluídas</td>
                        <td>{completed_tasks}</td>
                    </tr>
                    <tr>
                        <td>⏳ Pendentes</td>
                        <td>{pending_tasks}</td>
                    </tr>
                    <tr>
                        <td class="highlight">⚠️ Bloqueadas</td>
                        <td class="highlight">{blocked_tasks}</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <h3>📌 Sugestões para Melhorar o Fluxo de Trabalho</h3>
                <table class="table-container">
                    <tr>
                        <th>Sugestão</th>
                        <th>Descrição</th>
                    </tr>
                    {improvement_suggestions_table}
                </table>
            </div>

            <p class="footer">Este e-mail foi gerado automaticamente pelo sistema de automação Trello + Gemini.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(corpo_email, "html"))

        # Enviar e-mail
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        server.quit()

        print(f"✅ E-mail enviado com sucesso para {EMAIL_DESTINATARIO}!")

    except Exception as e:
        print("❌ Erro ao enviar e-mail:", str(e))


 
def get_trello_cards(list_name=None):
    """
    Busca os cards de uma lista específica no Trello ou de todas as listas.

    :param list_name: Nome da lista no Trello para buscar os cards. Se None ou "Todas", busca todas as listas.
    :return: Nome do quadro, Dicionário com listas disponíveis, ID da lista escolhida (ou None se for todas), Lista de cards.
    """
    try:
        # Buscar informações do board
        board_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}"
        params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
        response = requests.get(board_url, params=params)

        if response.status_code != 200:
            print(f"❌ Erro ao buscar informações do board: {response.text}")
            return None, {}, None, []

        board_name = response.json().get("name", "Desconhecido")

        # Obter todas as listas do board
        lists_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
        response = requests.get(lists_url, params=params)

        if response.status_code != 200:
            print(f"❌ Erro ao buscar listas do Trello: {response.text}")
            return board_name, {}, None, []

        lists = response.json()
        available_lists = {lst["id"]: lst["name"] for lst in lists}

        # Parâmetros para buscar mais informações nos cards
        card_params = {
            **params,
            "fields": "name,desc,dateLastActivity,idMembers,labels",
            "actions": "commentCard",  # Buscar apenas comentários
            "actions_limit": 5  # Pegar os últimos 5 comentários por card
        }

        # Se o usuário quiser todas as listas
        if not list_name or list_name.strip().lower() == "todas":
            print("🔹 Gerando insights para TODAS as listas do quadro...")
            all_cards = []

            for list_id, list_name in available_lists.items():
                cards_url = f"https://api.trello.com/1/lists/{list_id}/cards"
                response = requests.get(cards_url, params=card_params)

                if response.status_code == 200:
                    cards = response.json()
                    for card in cards:
                        card["list_name"] = list_name  # Adiciona o nome da lista ao card
                    all_cards.extend(cards)

            return board_name, available_lists, None, all_cards  # Retorna None para list_id quando for todas as listas

        # Caso contrário, busca apenas a lista específica
        list_id = next((lid for lid, lname in available_lists.items() if lname.strip().lower() == list_name.strip().lower()), None)

        if not list_id:
            print(f"⚠️ Nenhuma lista encontrada com o nome '{list_name}'. Verifique se o nome está correto.")
            return board_name, available_lists, None, []

        # Buscar os cards dessa lista específica
        cards_url = f"https://api.trello.com/1/lists/{list_id}/cards"
        response = requests.get(cards_url, params=card_params)

        if response.status_code == 200:
            cards = response.json()
            for card in cards:
                card["list_name"] = list_name  # Adiciona o nome da lista ao card
            return board_name, available_lists, list_id, cards

        else:
            print(f"❌ Erro ao buscar os cards da lista '{list_name}': {response.text}")
            return board_name, available_lists, list_id, []

    except Exception as e:
        print(f"❌ Erro inesperado ao buscar os cards: {str(e)}")
        return None, {}, None, []






def update_list_options():
    """Atualiza a lista de opções do Trello automaticamente."""
    global available_lists
    board_name, available_lists, _, _ = get_trello_cards("Todas")
    
    list_options = ["Todas"] + list(available_lists.values())  # Adiciona "Todas" como opção inicial
    list_combobox["values"] = list_options
    list_combobox.set("")  # Limpa a seleção atual

def reset_application():
    """Reinicializa a interface para permitir nova seleção e geração de relatório."""
    update_list_options()  # Atualiza automaticamente a lista
    list_combobox.set("")
    insights_text.delete("1.0", tk.END)
    status_label.config(text="🔍 Selecione uma lista para gerar um novo relatório.", foreground="black")
    enable_buttons()
    reset_button.pack_forget()  # Oculta o botão "Nova Análise"

def disable_buttons():
    """Desabilita os botões enquanto o relatório está sendo gerado."""
    generate_button.config(state="disabled")
    update_button.config(state="disabled")

def enable_buttons():
    """Reativa os botões após a geração do relatório."""
    generate_button.config(state="normal")
    update_button.config(state="normal")

def process_trello_data():
    """Executa o processo de análise e envio de e-mail baseado na lista selecionada."""
    list_name = list_combobox.get().strip()

    if not list_name:
        messagebox.showerror("Erro", "Selecione uma lista do Trello.")
        return

    disable_buttons()  # Desativa os botões antes de processar
    status_label.config(text="🔄 Processando... Aguarde.", foreground="blue")
    root.update_idletasks()  # Atualiza a interface enquanto processa

    # ✅ Executar a análise com base na escolha do usuário
    board_name, available_lists, list_id, cards = get_trello_cards(list_name)

    if cards:
        # ✅ Gerar o relatório completo do Trello e capturar métricas das tarefas
        board_report, completed_tasks, pending_tasks, blocked_tasks, tasks_per_list = generate_board_report(available_lists)

        # ✅ Gerar insights (passando o dicionário de listas também)
        insights = analyze_cards(cards, list_name, available_lists)

        # ✅ Exibir os insights gerados na interface
        insights_text.delete("1.0", tk.END)
        insights_text.insert(tk.END, insights)

        # ✅ Enviar os insights e o relatório por e-mail
        send_email(insights, board_name, list_name, board_report, completed_tasks, pending_tasks, blocked_tasks, tasks_per_list)

        status_label.config(text="✅ Relatório gerado e e-mail enviado!", foreground="green")
        
        # ✅ Atualizar a lista automaticamente e mostrar o botão de "Nova Análise"
        update_list_options()
        reset_button.pack(pady=10)

    else:
        status_label.config(text="⚠️ Nenhum card encontrado na lista.", foreground="red")
        messagebox.showwarning("Aviso", f"Nenhum card encontrado na lista '{list_name}'.")

# Criar janela principal
root = tk.Tk()
root.title("Trello Insights Automação")
root.geometry("800x550")
root.configure(bg="#f4f4f4")

# Frame superior
frame_top = tk.Frame(root, bg="#007BFF", pady=10)
frame_top.pack(fill="x")

title_label = tk.Label(frame_top, text="📊 Automação de Relatórios do Trello", font=("Arial", 14, "bold"), bg="#007BFF", fg="white")
title_label.pack()

# Frame principal
frame_main = tk.Frame(root, bg="#f4f4f4", padx=10, pady=10)
frame_main.pack(fill="both", expand=True)

# Rótulo e Combobox para selecionar a lista
ttk.Label(frame_main, text="Selecione uma Lista do Trello:", font=("Arial", 12, "bold")).pack(pady=5)

# Atualizar automaticamente ao iniciar
board_name, available_lists, _, _ = get_trello_cards("Todas")
list_options = ["Todas"] + list(available_lists.values())

list_combobox = ttk.Combobox(frame_main, values=list_options, width=50, font=("Arial", 10))
list_combobox.pack(pady=5)

# Botões de ação
button_frame = tk.Frame(frame_main, bg="#f4f4f4")
button_frame.pack(pady=10)

# Botão de nova análise (inicialmente escondido)
reset_button = ttk.Button(frame_main, text="🔁 Nova Análise", command=reset_application)
reset_button.pack(pady=10)
reset_button.pack_forget()

update_button = ttk.Button(button_frame, text="🔄 Atualizar Listas", command=update_list_options)
update_button.pack(side="left", padx=5)

generate_button = ttk.Button(button_frame, text="📊 Gerar Relatório", command=process_trello_data)
generate_button.pack(side="right", padx=5)

# Status Label
status_label = tk.Label(frame_main, text="🔍 Selecione uma lista para gerar um relatório.", font=("Arial", 10, "italic"), fg="black", bg="#f4f4f4")
status_label.pack(pady=5)

# Caixa de texto para exibir os insights
ttk.Label(frame_main, text="🔍 Insights Gerados:", font=("Arial", 12, "bold")).pack(pady=5)
insights_text = tk.Text(frame_main, height=12, width=90, wrap="word", font=("Arial", 10))
insights_text.pack(pady=5)

# Atualizar listas automaticamente ao iniciar
update_list_options()

# Rodar a interface gráfica
root.mainloop()
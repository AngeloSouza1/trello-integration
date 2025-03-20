# 📊 Trello Insights Automation

Automação inteligente para geração de relatórios do Trello com **Google Gemini**, visualização de **gráficos**, envio por **e-mail** e **interface gráfica amigável** feita em Python.

---

## 🚀 Funcionalidades

- ✅ Seleção de listas do Trello (ou todas)
- 🔍 Análise inteligente das tarefas com IA (Gemini API)
- 📈 Geração de gráficos (status e distribuição)
- ✉️ Envio automático de relatórios por e-mail em HTML
- 🧠 Insights estratégicos com base nos cards
- 💻 Interface gráfica com tkinter (intuitiva e responsiva)
- 🔄 Atualização automática das listas do Trello
- 🔁 Geração de múltiplos relatórios com botão de reinício

---

## 🖼️ Interface

![Interface do app](./assets/interface-example.png)  
*(Adicione aqui um screenshot real da interface)*

---

## 🧠 Integrações Utilizadas

| Ferramenta        | Finalidade                                 |
|-------------------|---------------------------------------------|
| Trello API        | Coleta de dados do quadro e listas         |
| Google Gemini     | Geração de insights e recomendações         |
| Matplotlib        | Criação de gráficos de análise              |
| SMTP (Gmail)      | Envio automático dos relatórios por e-mail  |
| Tkinter           | Criação da interface gráfica                |

---

## 📦 Tecnologias

- Python 3.10+
- Trello API
- Google Generative AI API
- `python-dotenv`
- `requests`
- `smtplib`
- `matplotlib`
- `tkinter`

---

## ⚙️ Instalação

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio

2. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt

3. **Configure o arquivo .env:**
    ```bash
    TRELLO_API_KEY=...
    TRELLO_TOKEN=...
    TRELLO_BOARD_ID=...
    GOOGLE_GEMINI_API_KEY=...
    EMAIL_REMETENTE=seuemail@gmail.com
    EMAIL_SENHA=suasenha
    EMAIL_DESTINATARIO=emaildestino@gmail.com

⚠️ Para contas Gmail, ative o acesso a apps menos seguros ou gere uma senha de app.

---

## ▶️ Como Usar

1. **Execute o script principal**
   ```bash
   python trello_gemini.py

2. **Na interface gráfica:**

- Selecione uma lista do Trello (ou "Todas")
- Clique em "📊 Gerar Relatório"
- Aguarde a análise e visualize os insights
- O relatório será enviado automaticamente por e-mail

---

## 📧 Exemplo de E-mail Enviado

- Insights organizados em tabela
- Gráficos embutidos
- Resumo do quadro com progresso
- Sugestões para otimização de tarefas

---

## 📌 Exemplo de Insight Gerado

```bash
   **3. Recomendações para Melhorar Eficiência:**
    - Atribuir responsáveis para tarefas sem dono
    - Estabelecer prazos claros
    - Criar um sistema de etiquetagem por prioridade
```

---

## 🛡️ Licença
Este projeto está licenciado sob a MIT License.
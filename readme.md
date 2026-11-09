# 🛒 Despensa Inteligente - Backend API

Backend desenvolvido em **FastAPI (Python)** para gerenciar o estoque doméstico de alimentos, com foco na **redução de desperdício**. O sistema conta com leitura automatizada de notas fiscais (via QR Code/NFC-e e OCR com Inteligência Artificial), geração inteligente de receitas e integração com o banco de dados NoSQL em tempo real (**Firebase Firestore**).

---

## 🌐 Ambientes e Base URLs

* **Produção (Vercel):** `https://inventory-manager-pink.vercel.app`
* **Local (Desenvolvimento):** `http://127.0.0.1:8000`
* **Documentação Interativa (Swagger UI Local):** `http://127.0.0.1:8000/docs`

---

## 🚀 Tecnologias Utilizadas

* **FastAPI** (Framework API REST de alta performance)
* **Python 3.10+**
* **Google GenAI SDK** (`google-genai` com o modelo **Gemini 3.8 Flash**) para OCR de notas e geração de receitas
* **BeautifulSoup4** para Web Scraping de notas fiscais (NFC-e)
* **Firebase Admin SDK** para integração com o Cloud Firestore
* **Vercel** (Hospedagem Serverless da API)

---

## ⚙️ Como Rodar o Projeto Localmente

### 1. Clonar o Repositório e Criar o Ambiente Virtual
Abra o terminal na pasta do projeto e execute:
```powershell
python -m venv venv
source venv/bin/activate  # No Windows (PowerShell): .\venv\Scripts\Activate.ps1
```

### 2. Instalar as Dependências
```powershell
pip install -r requirements.txt
```

### 3. Configurar as Variáveis de Ambiente (`.env`)
Crie um arquivo `.env` na raiz da pasta do backend com base no exemplo abaixo:
```env
GEMINI_API_KEY=sua_chave_da_api_do_gemini_aqui
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
```
*(Nota: Certifique-se também de baixar o arquivo JSON de credenciais da sua conta de serviço do Firebase e salvá-lo como `serviceAccountKey.json` na raiz do projeto).*

### 4. Iniciar o Servidor de Desenvolvimento
```powershell
uvicorn main:app --reload
```
A API estará rodando em: `http://127.0.0.1:8000`

---

## 📚 Documentação de Endpoints

### 🌐 1. Health Check
* **Método:** `GET`
* **Rota:** `/`
* **URL de Produção:** `https://inventory-manager-pink.vercel.app/`
* **Descrição:** Verifica se a API está online.
* **Resposta (`200 OK`):**
  ```json
  {
    "status": "online",
    "message": "API da Despensa Inteligente rodando com sucesso!"
  }
  ```

---

### 🧾 2. Notas Fiscais (`/api/receipts`)

#### 📌 Abordagem A: Web Scraping via QR Code (NFC-e)
* **Método:** `POST`
* **Rota:** `/api/receipts/scrape-qrcode`
* **URL de Produção:** `https://inventory-manager-pink.vercel.app/api/receipts/scrape-qrcode`
* **Headers:** `Content-Type: application/json`
* **Body (JSON):**
  ```json
  {
    "url": "https://notafiscal.sefaz.ce.gov.br/..."
  }
  ```
* **Descrição:** Acessa o link da SEFAZ extraído do QR Code, faz a raspagem HTML e retorna a lista de produtos.

#### 📌 Abordagem B: OCR via Inteligência Artificial (Gemini)
* **Método:** `POST`
* **Rota:** `/api/receipts/ocr-image`
* **URL de Produção:** `https://inventory-manager-pink.vercel.app/api/receipts/ocr-image`
* **Headers:** `Content-Type: multipart/form-data`
* **Body (form-data):** Chave `file` com a imagem da nota fiscal (`.jpg` ou `.png`).
* **Descrição:** Envia a imagem para o Gemini 3.8 Flash extrair os produtos e quantidades em formato estruturado.

---

### 🍳 3. Receitas Inteligentes (`/api/recipes`)

#### 📌 Gerar Receita por Vencimento
* **Método:** `POST`
* **Rota:** `/api/recipes/generate`
* **URL de Produção:** `https://inventory-manager-pink.vercel.app/api/recipes/generate`
* **Headers:** `Content-Type: application/json`
* **Body (JSON):**
  ```json
  {
    "ingredients": ["Tomate", "Ovos", "Alface", "Leite"]
  }
  ```
* **Descrição:** Cruza os ingredientes disponíveis (focando nos próximos ao vencimento) e utiliza a IA para criar uma receita prática passo a passo.

---

### 📦 4. Estoque de Alimentos (`/api/items`)

#### 📌 Salvar Alimento no Firestore
* **Método:** `POST`
* **Rota:** `/api/items/`
* **URL de Produção:** `https://inventory-manager-pink.vercel.app/api/items/`
* **Headers:** `Content-Type: application/json`
* **Body (JSON):**
  ```json
  {
    "name": "Leite",
    "quantity": "2",
    "unit": "Litros",
    "category": "Laticínios",
    "expiration_date": "05/11/2026",
    "user_id": "id_do_usuario_firebase"
  }
  ```
* **Descrição:** Cadastra ou atualiza um item de alimento na despensa digital do usuário.

#### 📌 Listar Alimentos do Usuário
* **Método:** `GET`
* **Rota:** `/api/items/user/{user_id}`
* **URL de Produção:** `https://inventory-manager-pink.vercel.app/api/items/user/{user_id}`
* **Descrição:** Retorna todos os itens salvos no Firestore vinculados ao ID do usuário informado.
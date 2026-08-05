# MacNF

Backend construído com Django e Django REST Framework para gerenciar notas fiscais de fornecedores em múltiplas lojas, com um fluxo de aprovação baseado em papéis entre o estoquista e o setor fiscal.

O sistema valida CNPJ e chave de acesso de NFe com cálculo real de dígito verificador, comprime imagens enviadas automaticamente, mantém um histórico completo de ações por nota, e vem com um frontend simples de página única (`index.html` + `style.css`) com modo claro/escuro.

---

## Funcionalidades

| Funcionalidade                  | Descrição                                                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Gestão de Fornecedores          | CRUD de fornecedores com validação real de CNPJ (dígito verificador)                                         |
| Fluxo de Notas Fiscais          | Status: `pendente` → `em_analise` → `lancada`, com regras de permissão em cada etapa                         |
| Permissões por Papel            | Três papéis via Grupos do Django: `estoquista`, `setor_fiscal` e `setor_compras`                             |
| Validação de Chave de Acesso    | Chave de acesso da NFe validada com algoritmo real de dígito verificador (módulo 11)                         |
| Upload e Compressão de Arquivos | Aceita PDF/JPG/PNG/HEIC/WEBP (máx. 10 MB); imagens são comprimidas e convertidas para JPEG automaticamente   |
| Múltiplos Anexos                | Arquivos extras além do documento principal são salvos como anexos separados                                 |
| Observação e Resposta           | Estoquista pode deixar uma observação; fiscal/compras podem responder, com autor e data registrados          |
| Histórico de Ações              | Trilha de auditoria completa por nota (criada, editada, enviada, lançada, respondida)                        |
| Busca e Filtros                 | Busca por número, chave de acesso, observação ou nome do fornecedor; filtro por fornecedor e data de criação |
| Estatísticas e Relatórios       | Totais, contagem de lançadas no mês, e relatório por fornecedor filtrado por ano/mês                         |
| Suporte a Múltiplas Lojas       | Lojas já configuradas: Canguaretama, Praia de Pipa, São Miguel do Gostoso                                    |
| Autenticação por Token          | Endpoint de login customizado retorna token de autenticação e os papéis do usuário                           |

---

## Endpoints da API

Caminho base: `/api/`

**Autenticação**

| Método | Endpoint      | Descrição                                        |
| ------ | ------------- | ------------------------------------------------ |
| POST   | `/api/login/` | Autentica e retorna um token + papéis do usuário |

**Fornecedores**

| Método | Endpoint                  | Descrição                                                   |
| ------ | ------------------------- | ----------------------------------------------------------- |
| GET    | `/api/fornecedores/`      | Lista fornecedores                                          |
| POST   | `/api/fornecedores/`      | Cadastra um fornecedor                                      |
| GET    | `/api/fornecedores/<id>/` | Detalha um fornecedor                                       |
| PUT    | `/api/fornecedores/<id>/` | Atualiza um fornecedor                                      |
| DELETE | `/api/fornecedores/<id>/` | Remove um fornecedor (bloqueado se houver notas vinculadas) |

**Notas Fiscais**

| Método | Endpoint                  | Descrição                                                          |
| ------ | ------------------------- | ------------------------------------------------------------------ |
| GET    | `/api/notas/`             | Lista notas (filtrável por `search`, `fornecedor`, `data_criacao`) |
| POST   | `/api/notas/`             | Cadastra uma nota (aceita múltiplos arquivos)                      |
| GET    | `/api/notas/<id>/`        | Detalha uma nota, com histórico e anexos                           |
| PUT    | `/api/notas/<id>/`        | Atualiza uma nota (bloqueado quando `lancada`)                     |
| DELETE | `/api/notas/<id>/`        | Remove uma nota (bloqueado quando `lancada`)                       |
| POST   | `/api/notas/<id>/lancar/` | Marca a nota como lançada (apenas fiscal/compras)                  |
| GET    | `/api/notas/stats/`       | Totais e contagem de notas lançadas no mês                         |
| GET    | `/api/notas/relatorio/`   | Relatório de notas lançadas por ano/mês, agrupado por fornecedor   |

---

## Screenshots

**Login**
![Login](docs/screenshots/login.png)

**Lista de Notas**
![Lista de Notas](docs/screenshots/notas-list.png)

**Nova Nota**
![Nova Nota](docs/screenshots/nota-create.png)

**Relatório**
![Relatório](docs/screenshots/relatorio.png)

---

## Estrutura do Projeto

```
├── notas/                      # App principal
│   ├── models.py               # Fornecedor, NotaFiscal, AnexoNotaFiscal, HistoricoNotaFiscal
│   ├── serializers.py          # Validação de CNPJ / chave de acesso, validação de arquivo
│   ├── views.py                # ViewSets + ações customizadas (lancar, stats, relatorio)
│   ├── permissions.py          # Classes de permissão por papel
│   ├── signals.py              # Remove arquivos do storage ao excluir uma nota
│   ├── tests.py
│   └── urls.py                 # Rotas DRF
├── <projeto>/                  # Configurações do projeto Django
│   ├── settings.py
│   └── urls.py                 # URLconf raiz (/, /admin/, /api/)
├── templates/
│   └── index.html              # Frontend de página única
├── static/
│   └── style.css                # Estilo do frontend (modo claro/escuro, mobile-first)
├── Procfile                    # Definição de processo para o Heroku
├── runtime.txt                 # Versão do Python fixada
├── requirements.txt
└── manage.py
```

---

## Tecnologias

**Backend**

- Python 3.12
- Django 6.0.6
- Django REST Framework 3.17.1
- django-filter — filtragem de queries
- django-cors-headers — tratamento de CORS
- django-axes — proteção contra força bruta no login
- djangorestframework-simplejwt — suporte a JWT
- Pillow — compressão de imagens no upload
- validate-docbr — validação de CNPJ
- psycopg2-binary — driver PostgreSQL
- python-decouple — configuração via variáveis de ambiente
- whitenoise — servir arquivos estáticos
- django-storages + boto3 — armazenamento de arquivos compatível com S3

**Frontend**

- HTML5
- CSS3 (customizado, mobile-first, modo claro/escuro)

**Deploy**

- Gunicorn (servidor WSGI)
- Deploy estilo Heroku (`Procfile` + `runtime.txt`)
- PostgreSQL

---

## Como Executar

**1. Clonar o repositório**

```bash
git clone <repository-url>
cd macnf
```

**2. Criar e ativar o ambiente virtual**

```bash
python -m venv venv
# Windows
.\venv\Scripts\Activate
# Linux/Mac
source venv/bin/activate
```

**3. Instalar as dependências**

```bash
pip install -r requirements.txt
```

**4. Configurar variáveis de ambiente**

Crie um arquivo `.env` com as credenciais de banco de dados e storage (usadas via `python-decouple`), por exemplo:

```
SECRET_KEY=sua-chave-secreta
DEBUG=True
DATABASE_URL=postgres://usuario:senha@localhost:5432/notas_fiscais
```

**5. Aplicar as migrações**

```bash
python manage.py migrate
```

**6. Criar um superusuário**

```bash
python manage.py createsuperuser
```

**7. Iniciar o servidor**

```bash
python manage.py runserver
```

Acesse em `http://127.0.0.1:8000/`

> Depois de criar o superusuário, adicione-o ao grupo `estoquista`, `setor_fiscal` ou `setor_compras` pelo admin do Django para conceder as permissões do papel correspondente.

---

## Autores

- [Lucas Emanoel da Silva Freitas](https://www.linkedin.com/in/lucas-emanoel-38a440238/)

---

[Read in English](README.md)

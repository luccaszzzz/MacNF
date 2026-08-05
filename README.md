# MacNF

Backend built with Django and Django REST Framework for managing incoming supplier invoices (_notas fiscais_) across multiple store locations, with a role-based approval workflow between stock clerks and the fiscal (accounting) department.

The system validates CNPJ and NFe access keys with real check-digit calculations, compresses uploaded images automatically, keeps a full action history per invoice, and ships with a lightweight single-page frontend (`index.html` + `style.css`) featuring light/dark mode.

---

## Features

| Feature                   | Description                                                                                                      |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Supplier Management       | CRUD for suppliers (_fornecedores_) with real CNPJ validation (check digit)                                      |
| Invoice Workflow          | Status flow: `pendente` → `em_analise` → `lancada`, with permission rules per stage                              |
| Role-Based Permissions    | Three roles via Django Groups: `estoquista` (stock clerk), `setor_fiscal` (fiscal), `setor_compras` (purchasing) |
| NFe Key Validation        | Access key (`chave_acesso`) validated with a real modulo-11 check-digit algorithm                                |
| File Upload & Compression | Accepts PDF/JPG/PNG/HEIC/WEBP (max 10 MB); images are auto-compressed and converted to JPEG on save              |
| Multiple Attachments      | Extra files beyond the main invoice document are stored as separate attachments                                  |
| Observation & Reply       | Stock clerk can leave a note; fiscal/purchasing can reply, tracked with author and timestamp                     |
| Action History            | Full audit trail per invoice (created, edited, sent, launched, replied)                                          |
| Search & Filters          | Search by invoice number, access key, observation, or supplier name; filter by supplier and creation date        |
| Stats & Reports           | Totals, monthly launched count, and a supplier breakdown report by year/month                                    |
| Multi-Store Support       | Built-in store options: Canguaretama, Praia de Pipa, São Miguel do Gostoso                                       |
| Token Authentication      | Custom login endpoint returns an auth token plus the user's role flags                                           |

---

## API Endpoints

Base path: `/api/`

**Authentication**

| Method | Endpoint      | Description                                    |
| ------ | ------------- | ---------------------------------------------- |
| POST   | `/api/login/` | Authenticates and returns a token + role flags |

**Suppliers**

| Method | Endpoint                  | Description                                          |
| ------ | ------------------------- | ---------------------------------------------------- |
| GET    | `/api/fornecedores/`      | List suppliers                                       |
| POST   | `/api/fornecedores/`      | Create a supplier                                    |
| GET    | `/api/fornecedores/<id>/` | Retrieve a supplier                                  |
| PUT    | `/api/fornecedores/<id>/` | Update a supplier                                    |
| DELETE | `/api/fornecedores/<id>/` | Delete a supplier (blocked if linked invoices exist) |

**Invoices**

| Method | Endpoint                  | Description                                                          |
| ------ | ------------------------- | -------------------------------------------------------------------- |
| GET    | `/api/notas/`             | List invoices (filterable by `search`, `fornecedor`, `data_criacao`) |
| POST   | `/api/notas/`             | Create an invoice (accepts multiple files)                           |
| GET    | `/api/notas/<id>/`        | Retrieve an invoice, with history and attachments                    |
| PUT    | `/api/notas/<id>/`        | Update an invoice (blocked once `lancada`)                           |
| DELETE | `/api/notas/<id>/`        | Delete an invoice (blocked once `lancada`)                           |
| POST   | `/api/notas/<id>/lancar/` | Mark an invoice as launched (fiscal/purchasing only)                 |
| GET    | `/api/notas/stats/`       | Totals and monthly launched counts                                   |
| GET    | `/api/notas/relatorio/`   | Report of launched invoices by year/month, grouped by supplier       |

---

## Screenshots

**Login**
![Login](docs/screenshots/login.png)

**Invoice List**
![Invoice List](docs/screenshots/notas-list.png)

**New Invoice**
![New Invoice](docs/screenshots/nota-create.png)

**Report**
![Report](docs/screenshots/relatorio.png)

---

## Project Structure

```
├── notas/                      # Main app
│   ├── models.py               # Fornecedor, NotaFiscal, AnexoNotaFiscal, HistoricoNotaFiscal
│   ├── serializers.py          # CNPJ / access-key validation, file validation
│   ├── views.py                # ViewSets + custom actions (lancar, stats, relatorio)
│   ├── permissions.py          # Role-based permission classes
│   ├── signals.py              # Deletes stored files when an invoice is removed
│   ├── tests.py
│   └── urls.py                 # DRF router
├── <project>/                  # Django project settings
│   ├── settings.py
│   └── urls.py                 # Root URLconf (/, /admin/, /api/)
├── templates/
│   └── index.html              # Single-page frontend
├── static/
│   └── style.css                # Frontend styling (light/dark mode, mobile-first)
├── Procfile                    # Heroku process definition
├── runtime.txt                 # Python version pin
├── requirements.txt
└── manage.py
```

---

## Technologies

**Backend**

- Python 3.12
- Django 6.0.6
- Django REST Framework 3.17.1
- django-filter — query filtering
- django-cors-headers — CORS handling
- django-axes — brute-force login protection
- djangorestframework-simplejwt — JWT support
- Pillow — image compression on upload
- validate-docbr — CNPJ validation
- psycopg2-binary — PostgreSQL driver
- python-decouple — environment configuration
- whitenoise — static file serving
- django-storages + boto3 — S3-compatible file storage

**Frontend**

- HTML5
- CSS3 (custom, mobile-first, light/dark mode)

**Deployment**

- Gunicorn (WSGI server)
- Heroku-style deployment (`Procfile` + `runtime.txt`)
- PostgreSQL

---

## How to Run

**1. Clone the repository**

```bash
git clone <repository-url>
cd macnf
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
# Windows
.\venv\Scripts\Activate
# Linux/Mac
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file with your database and storage credentials (used via `python-decouple`), e.g.:

```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/notas_fiscais
```

**5. Apply migrations**

```bash
python manage.py migrate
```

**6. Create a superuser**

```bash
python manage.py createsuperuser
```

**7. Start the server**

```bash
python manage.py runserver
```

Access at `http://127.0.0.1:8000/`

> After creating your superuser, add them to the `estoquista`, `setor_fiscal`, or `setor_compras` group via the Django admin to grant the appropriate role permissions.

---

## Authors

- [Lucas Emanoel da Silva Freitas](https://www.linkedin.com/in/lucas-emanoel-38a440238/)

---

[Leia em Português](README.pt-br.md)

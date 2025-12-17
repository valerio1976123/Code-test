## Crazynet Device Backup (Python-only, no Docker)

Web app per gestire dispositivi di rete e fare backup configurazioni via SSH.

- **Backend + UI**: FastAPI + Jinja2 (templates) + Tailwind (CDN)
- **DB**: SQLite + SQLAlchemy 2.0 + Alembic
- **Auth**: JWT access+refresh + bcrypt
- **SSH**: Paramiko
- **Scheduler**: APScheduler (job ogni 30s) + limite concorrenza `MAX_PARALLEL_BACKUPS`
- **Backup storage**: `backend/./backups/`

---

## Struttura repo

- `backend/`
  - `app/` FastAPI + UI
  - `alembic/` migrazioni
  - `requirements.txt`
  - `.env.example`

---

## Avvio (no Docker)

### Backend + UI

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Genera e imposta le chiavi:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Poi modifica `backend/.env`:

- `APP_SECRET_KEY`: output del comando sopra (Fernet)
- `JWT_SECRET`: una stringa random lunga

### Migrazioni

```bash
alembic upgrade head
```

### Seed iniziale

Crea:
- 3 device **disabilitati**
- 1 schedule di esempio
- utente `admin/admin`

```bash
python -m app.seed
```

### Start

```bash
 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- **UI**: `http://localhost:8000/dashboard`
- **Login**: `http://localhost:8000/login`
- **Swagger**: `http://localhost:8000/docs`

---

## Scheduler (come funziona)

- Parte automaticamente allo startup di FastAPI.
- Ogni **30s** cerca schedule `is_enabled=1` con `next_run_at <= now`.
- Per ogni schedule dovuta crea una `BackupExecution` e calcola il prossimo `next_run_at`.
- Dispatch in un worker pool con limite `MAX_PARALLEL_BACKUPS`.
- Endpoint **Run now** (`POST /api/devices/{id}/run-now`) crea un’execution e prova a farla partire subito (se ci sono slot liberi).

---

## Test (minimi)

```bash
cd backend
pytest
```

Coprono:
- calcolo `next_run_at`
- path builder del file di backup

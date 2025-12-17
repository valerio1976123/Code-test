## Crazynet Device Backup (no Docker)

Web app per gestire dispositivi di rete e fare backup configurazioni via SSH.

- **Backend**: FastAPI + SQLite + SQLAlchemy 2.0 + Alembic
- **Auth**: JWT access+refresh + bcrypt
- **SSH**: Paramiko
- **Scheduler**: APScheduler (job ogni 30s) + limite concorrenza `MAX_PARALLEL_BACKUPS`
- **Backup storage**: `backend/./backups/`
- **Frontend**: React + TypeScript (Vite) + Mantine UI

---

## Struttura repo

- `backend/`
  - `app/` FastAPI
  - `alembic/` migrazioni
  - `requirements.txt`
  - `.env.example`
- `frontend/`
  - Vite React+TS

---

## Backend (FastAPI)

### Setup

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

### Avvio

```bash
uvicorn app.main:app --reload
```

- API: `http://localhost:8000/api`
- Swagger: `http://localhost:8000/docs`

---

## Frontend (React + TS)

### Setup + avvio

```bash
cd frontend
npm install
npm run dev
```

- UI: `http://localhost:5173`
- CORS già abilitato sul backend per `http://localhost:5173`

Opzionale: puoi cambiare la base API con:

```bash
# frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000/api
```

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

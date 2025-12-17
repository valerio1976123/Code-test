# Network Backup Manager (Laravel + React)

Web app per gestire dispositivi di rete e fare backup configurazioni via SSH, con dashboard e pianificazione.

## Struttura repo

- `backend/`: Laravel (API) + SQLite + Sanctum (SPA cookie) + queue/scheduler
- `frontend/`: React + TypeScript (Vite) + Tailwind + toast
- `docker-compose.yml`: nginx + php-fpm + worker + scheduler + frontend

## Backend (Laravel)

### Setup (locale, senza Docker)

```bash
cd backend
cp .env.example .env
touch database/database.sqlite
composer install
php artisan key:generate
php artisan migrate --seed
php artisan serve --host=0.0.0.0 --port=8000
```

In altri terminali:

```bash
cd backend
php artisan queue:work
php artisan schedule:work
```

### Backup storage

I file vengono salvati in `backend/storage/app/backups/<vendor>/<device>/<YYYY>/<MM>/...`.

## Frontend (React)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Di default il frontend punta a `http://localhost:8000/api`.

Credenziali seed:

- email: `admin@example.com`
- password: `password`

## Docker (nginx + php-fpm + node)

```bash
docker compose up -d --build
docker compose exec php composer install
docker compose exec php cp .env.example .env
docker compose exec php php artisan key:generate
docker compose exec php sh -lc "touch database/database.sqlite && php artisan migrate --seed"
```

- Backend via nginx: `http://localhost:8080`
- Frontend: `http://localhost:5173`

Nota: per Sanctum SPA cookie, assicurati che in `backend/.env`:

- `FRONTEND_URL=http://localhost:5173`
- `SANCTUM_STATEFUL_DOMAINS=localhost,127.0.0.1,localhost:5173,127.0.0.1:5173`

## Scheduler

Il comando `backups:tick` viene eseguito ogni minuto da `schedule:work` e dispatcha `RunBackupJob` nel database queue.


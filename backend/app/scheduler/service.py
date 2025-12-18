from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.backup.runner import run_backup_execution
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.execution import BackupExecution
from app.models.schedule import BackupSchedule
from app.scheduler.calculator import compute_next_run_at


class SchedulerService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._scheduler: BackgroundScheduler | None = None
        self._executor = ThreadPoolExecutor(max_workers=settings.MAX_PARALLEL_BACKUPS)
        self._futures: set[Future] = set()

    def start(self) -> None:
        with self._lock:
            if self._scheduler is not None:
                return
            sched = BackgroundScheduler(timezone="UTC")
            sched.add_job(self._tick, trigger="interval", seconds=30, id="crazynet_tick", max_instances=1)

            # Market monitor jobs (mock dev mode by default)
            try:
                from app.market.jobs import market_evaluate_alerts_job, market_refresh_data_job, market_run_predictions_job

                sched.add_job(
                    market_refresh_data_job,
                    trigger="interval",
                    seconds=max(30, int(settings.MARKET_PRICE_REFRESH_SECONDS)),
                    id="market_refresh_data",
                    max_instances=1,
                    coalesce=True,
                )
                sched.add_job(
                    market_run_predictions_job,
                    trigger="interval",
                    seconds=max(60, int(settings.MARKET_PREDICTION_REFRESH_SECONDS)),
                    id="market_run_predictions",
                    max_instances=1,
                    coalesce=True,
                )
                sched.add_job(
                    market_evaluate_alerts_job,
                    trigger="interval",
                    seconds=max(60, int(settings.MARKET_PREDICTION_REFRESH_SECONDS)),
                    id="market_evaluate_alerts",
                    max_instances=1,
                    coalesce=True,
                )
            except Exception:
                # Keep the legacy app usable even if market deps are not installed yet.
                pass

            sched.start()
            self._scheduler = sched

    def stop(self) -> None:
        with self._lock:
            if self._scheduler is not None:
                self._scheduler.shutdown(wait=False)
                self._scheduler = None
        try:
            self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass

    def dispatch_execution(self, execution_id: int) -> bool:
        """Try to dispatch a queued execution immediately.

        Returns True if it was submitted to the worker pool, False if no slots.
        """
        slots = self._available_slots()
        if slots <= 0:
            return False

        # claim execution to avoid double-dispatch
        with SessionLocal() as db:
            exe = db.get(BackupExecution, execution_id)
            if not exe or exe.status != "queued":
                return False
            exe.status = "running"
            exe.started_at = exe.started_at or datetime.utcnow()
            db.commit()

        future = self._executor.submit(self._run_execution, execution_id)
        self._futures.add(future)
        return True

    def _prune_futures(self) -> None:
        done = {f for f in self._futures if f.done()}
        self._futures -= done

    def _available_slots(self) -> int:
        self._prune_futures()
        return max(0, settings.MAX_PARALLEL_BACKUPS - len(self._futures))

    def _tick(self) -> None:
        # 1) materialize due schedules into queued executions
        now = datetime.utcnow()
        with SessionLocal() as db:
            due = db.execute(
                select(BackupSchedule)
                .where(BackupSchedule.is_enabled.is_(True))
                .where(BackupSchedule.next_run_at.is_not(None))
                .where(BackupSchedule.next_run_at <= now)
                .order_by(BackupSchedule.next_run_at.asc())
            ).scalars().all()

            for sch in due:
                exe = BackupExecution(device_id=sch.device_id, schedule_id=sch.id, status="queued")
                db.add(exe)

                sch.last_run_at = now
                sch.next_run_at = compute_next_run_at(
                    schedule_type=sch.schedule_type,
                    now=now,
                    run_once_at=sch.run_once_at,
                    time_of_day=sch.time_of_day,
                    weekdays_csv=sch.weekdays,
                    every_n_hours=sch.every_n_hours,
                    last_run_at=sch.last_run_at,
                )
            db.commit()

        # 2) dispatch queued executions into worker pool
        slots = self._available_slots()
        if slots <= 0:
            return

        with SessionLocal() as db:
            queued = db.execute(
                select(BackupExecution)
                .where(BackupExecution.status == "queued")
                .order_by(BackupExecution.created_at.asc())
                .limit(slots)
            ).scalars().all()

            now2 = datetime.utcnow()
            for exe in queued:
                exe.status = "running"
                exe.started_at = exe.started_at or now2
            db.commit()

            for exe in queued:
                future = self._executor.submit(self._run_execution, exe.id)
                self._futures.add(future)

    def _run_execution(self, execution_id: int) -> None:
        with SessionLocal() as db:
            run_backup_execution(db, execution_id)


scheduler_service = SchedulerService()

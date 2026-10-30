"""
Reliable Background Scheduler with Process Locking.
Ensures non-blocking scheduled execution of scheme discovery and deadline monitoring
across single and multi-worker deployment environments without duplicate execution.
"""

import fcntl
import logging
import os
import threading
import time
from datetime import datetime
from typing import Optional

from services.deadline_monitoring.deadline_service import DeadlineMonitoringService
from services.scheme_discovery.discovery_engine import SchemeDiscoveryEngine

logger = logging.getLogger("udyog_sathi.scheduler")


class SchemeIntelligenceScheduler:
    LOCK_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "scheduler.lock")

    def __init__(self, check_interval_seconds: int = 3600):
        self.check_interval_seconds = check_interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock_file = None

    def _acquire_process_lock(self) -> bool:
        """Acquires a non-blocking flock to guarantee single-worker execution."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.LOCK_FILE_PATH)), exist_ok=True)
            self._lock_file = open(self.LOCK_FILE_PATH, "w")
            fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_file.write(f"PID: {os.getpid()} - Started: {datetime.utcnow().isoformat()}\n")
            self._lock_file.flush()
            return True
        except (IOError, BlockingIOError, OSError) as e:
            logger.warning(f"Could not acquire process lock: {e}")
            if self._lock_file:
                try:
                    self._lock_file.close()
                except Exception:
                    pass
                self._lock_file = None
            return False

    def _release_process_lock(self):
        if self._lock_file:
            try:
                fcntl.flock(self._lock_file, fcntl.LOCK_UN)
                self._lock_file.close()
            except Exception:
                pass
            self._lock_file = None

    def _worker_loop(self):
        logger.info(f"[Scheduler] Background worker loop started (PID: {os.getpid()}).")

        # Initial run on startup
        self._run_cycles()

        while not self._stop_event.is_set():
            # Wait for interval or stop event
            if self._stop_event.wait(timeout=self.check_interval_seconds):
                break
            self._run_cycles()

        self._release_process_lock()
        logger.info("[Scheduler] Background worker loop stopped.")

    def _run_cycles(self):
        try:
            logger.info("[Scheduler] Running deadline monitoring cycle...")
            deadline_svc = DeadlineMonitoringService()
            summary = deadline_svc.run_monitoring_cycle()
            logger.info(
                f"[Scheduler] Deadline cycle complete: {summary.total_schemes_checked} checked, "
                f"{summary.open_schemes} open, {summary.new_alerts_created} new alerts."
            )
        except Exception as e:
            logger.error(f"[Scheduler] Deadline monitoring cycle error: {e}")

        try:
            logger.info("[Scheduler] Running automated source discovery...")
            discovery_engine = SchemeDiscoveryEngine()
            results = discovery_engine.run_all_discovery()
            new_imported = sum(r.new_documents_imported for r in results)
            logger.info(f"[Scheduler] Discovery run complete: {new_imported} new documents imported across {len(results)} sources.")
        except Exception as e:
            logger.error(f"[Scheduler] Scheme discovery run error: {e}")

    def start(self):
        """Starts background worker thread if lock can be acquired."""
        if not self._acquire_process_lock():
            logger.info(f"[Scheduler] Another process already holds the scheduler lock. Skipping on PID {os.getpid()}.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="SchemeSchedulerWorker")
        self._thread.start()
        logger.info("[Scheduler] Background scheduler thread started.")

    def stop(self):
        """Stops background worker thread gracefully."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._release_process_lock()


# Global scheduler instance
global_scheduler = SchemeIntelligenceScheduler()

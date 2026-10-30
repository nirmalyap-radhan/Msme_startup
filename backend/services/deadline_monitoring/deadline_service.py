"""
Deadline and Availability Monitoring Service.
Evaluates application and claim windows, calculates derived lifecycle statuses,
generates window alerts (30, 14, 7, 3, 1 days), and records audit history.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from services.deadline_monitoring.models import (
    DeadlineAlertItem,
    DeadlineMonitoringCycleSummary,
    DeadlineStatusEvaluation,
)
from services.scheme_ingestion.models import (
    ApplicationStatus,
    ClaimStatus,
    DiscoveryAuditLogModel,
    SchemeDeadlineAlertModel,
    SchemeModel,
    SchemeStatus,
)
from services.scheme_ingestion.storage import SchemeStorageRepository


class DeadlineMonitoringService:
    ALERT_THRESHOLDS = [30, 14, 7, 3, 1]
    INDIA_TZ = ZoneInfo("Asia/Kolkata")

    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session

    def _get_session(self) -> Session:
        if self._db:
            return self._db
        repo = SchemeStorageRepository()
        return repo.get_session()

    @classmethod
    def get_current_ist_time(cls) -> datetime:
        return datetime.now(cls.INDIA_TZ)

    def evaluate_scheme_deadlines(self, scheme: SchemeModel) -> DeadlineStatusEvaluation:
        """
        Calculates independent application_status and claim_status based on
        authoritative dates, rolling flags, and current Indian Standard Time.
        Never fabricates dates. If missing, marks as unknown or verification_required.
        """
        now = self.get_current_ist_time()
        orig_app_status = scheme.application_status or ApplicationStatus.UNKNOWN.value
        orig_claim_status = scheme.claim_status or ClaimStatus.UNKNOWN.value

        days_app: Optional[int] = None
        days_claim: Optional[int] = None
        new_app_status = ApplicationStatus.UNKNOWN
        new_claim_status = ClaimStatus.UNKNOWN

        # ----------------------------------------------------------------------
        # 1. APPLICATION STATUS DERIVATION
        # ----------------------------------------------------------------------
        if scheme.status in (SchemeStatus.SUPERSEDED.value, SchemeStatus.WITHDRAWN.value):
            new_app_status = ApplicationStatus.DISCONTINUED
        elif scheme.is_rolling:
            new_app_status = ApplicationStatus.OPEN
        elif scheme.application_deadline:
            # Deadline is set
            deadline_dt = scheme.application_deadline
            if deadline_dt.tzinfo is None:
                deadline_dt = deadline_dt.replace(tzinfo=timezone.utc).astimezone(self.INDIA_TZ)
            else:
                deadline_dt = deadline_dt.astimezone(self.INDIA_TZ)

            delta = deadline_dt - now
            days_app = int(round(delta.total_seconds() / 86400.0))

            start_dt = scheme.application_start_date
            if start_dt:
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc).astimezone(self.INDIA_TZ)
                else:
                    start_dt = start_dt.astimezone(self.INDIA_TZ)

                if now < start_dt:
                    new_app_status = ApplicationStatus.UPCOMING
                elif days_app < 0:
                    new_app_status = ApplicationStatus.CLOSED
                elif days_app <= 14:
                    new_app_status = ApplicationStatus.CLOSING_SOON
                else:
                    new_app_status = ApplicationStatus.OPEN
            else:
                if days_app < 0:
                    new_app_status = ApplicationStatus.CLOSED
                elif days_app <= 14:
                    new_app_status = ApplicationStatus.CLOSING_SOON
                else:
                    new_app_status = ApplicationStatus.OPEN
        else:
            # No deadline and not declared rolling
            new_app_status = ApplicationStatus.VERIFICATION_REQUIRED

        # ----------------------------------------------------------------------
        # 2. CLAIM STATUS DERIVATION
        # ----------------------------------------------------------------------
        if scheme.claim_deadline:
            claim_dt = scheme.claim_deadline
            if claim_dt.tzinfo is None:
                claim_dt = claim_dt.replace(tzinfo=timezone.utc).astimezone(self.INDIA_TZ)
            else:
                claim_dt = claim_dt.astimezone(self.INDIA_TZ)

            delta_claim = claim_dt - now
            days_claim = int(round(delta_claim.total_seconds() / 86400.0))

            if days_claim < 0:
                new_claim_status = ClaimStatus.CLAIMS_CLOSED
            elif days_claim <= 14:
                new_claim_status = ClaimStatus.CLAIMS_CLOSING_SOON
            else:
                new_claim_status = ClaimStatus.CLAIMS_OPEN
        elif scheme.is_rolling:
            new_claim_status = ClaimStatus.ROLLING_CLAIMS
        elif "reimbursement" in scheme.official_name.lower() or "subsidy" in scheme.official_name.lower():
            new_claim_status = ClaimStatus.VERIFICATION_REQUIRED
        else:
            new_claim_status = ClaimStatus.NOT_APPLICABLE

        status_changed = (new_app_status.value != orig_app_status) or (new_claim_status.value != orig_claim_status)

        return DeadlineStatusEvaluation(
            scheme_id=scheme.id,
            scheme_name=scheme.official_name,
            application_status=new_app_status,
            claim_status=new_claim_status,
            days_until_application_deadline=days_app,
            days_until_claim_deadline=days_claim,
            is_rolling=scheme.is_rolling or False,
            status_changed=status_changed,
            alerts_generated=[],
        )

    def run_monitoring_cycle(self) -> DeadlineMonitoringCycleSummary:
        """
        Runs a comprehensive deadline check across all schemes in the database.
        Generates alerts for 30, 14, 7, 3, and 1 days before deadline.
        Persists status changes and audit log entries.
        """
        session = self._get_session()
        should_close = (self._db is None)

        now_utc = datetime.utcnow()
        summary = DeadlineMonitoringCycleSummary(
            evaluated_at=now_utc,
            total_schemes_checked=0,
            open_schemes=0,
            closing_soon_schemes=0,
            closed_schemes=0,
            rolling_schemes=0,
            claims_open_schemes=0,
            new_alerts_created=0,
            status_transitions_count=0,
        )

        try:
            schemes: List[SchemeModel] = session.query(SchemeModel).all()
            summary.total_schemes_checked = len(schemes)

            for scheme in schemes:
                eval_res = self.evaluate_scheme_deadlines(scheme)

                # Update stats
                if eval_res.application_status == ApplicationStatus.OPEN:
                    summary.open_schemes += 1
                elif eval_res.application_status == ApplicationStatus.CLOSING_SOON:
                    summary.closing_soon_schemes += 1
                elif eval_res.application_status == ApplicationStatus.CLOSED:
                    summary.closed_schemes += 1

                if eval_res.is_rolling:
                    summary.rolling_schemes += 1

                if eval_res.claim_status in (ClaimStatus.CLAIMS_OPEN, ClaimStatus.ROLLING_CLAIMS):
                    summary.claims_open_schemes += 1

                # If status changed, record transition and write audit log
                if eval_res.status_changed:
                    prev_state = {
                        "application_status": scheme.application_status,
                        "claim_status": scheme.claim_status,
                    }
                    new_state = {
                        "application_status": eval_res.application_status.value,
                        "claim_status": eval_res.claim_status.value,
                    }

                    scheme.application_status = eval_res.application_status.value
                    scheme.claim_status = eval_res.claim_status.value
                    scheme.last_verified_at = now_utc

                    # Append to status history
                    history = list(scheme.status_history or [])
                    history.append({
                        "timestamp": now_utc.isoformat(),
                        "from_application": prev_state["application_status"],
                        "to_application": new_state["application_status"],
                        "from_claim": prev_state["claim_status"],
                        "to_claim": new_state["claim_status"],
                        "reason": "Scheduled deadline monitoring evaluation",
                    })
                    scheme.status_history = history

                    audit = DiscoveryAuditLogModel(
                        id=str(uuid4()),
                        scheme_id=scheme.id,
                        event_type="status_transition",
                        previous_state=prev_state,
                        new_state=new_state,
                        supporting_evidence=(
                            f"Application status changed to {eval_res.application_status.value}; "
                            f"Claim status changed to {eval_res.claim_status.value}"
                        ),
                        source_clause_or_url=scheme.source_url,
                    )
                    session.add(audit)
                    summary.status_transitions_count += 1

                # Generate window alerts if deadline is set
                if eval_res.days_until_application_deadline is not None:
                    days_left = eval_res.days_until_application_deadline
                    for threshold in self.ALERT_THRESHOLDS:
                        if 0 <= days_left <= threshold:
                            alert_type = f"application_deadline_{threshold}d"
                            # Check if alert already exists
                            existing_alert = session.query(SchemeDeadlineAlertModel).filter(
                                SchemeDeadlineAlertModel.scheme_id == scheme.id,
                                SchemeDeadlineAlertModel.alert_type == alert_type,
                                SchemeDeadlineAlertModel.is_dismissed == False,
                            ).first()

                            if not existing_alert:
                                alert_obj = SchemeDeadlineAlertModel(
                                    id=str(uuid4()),
                                    scheme_id=scheme.id,
                                    alert_type=alert_type,
                                    target_date=scheme.application_deadline,
                                    days_remaining=days_left,
                                    message=(
                                        f"Application deadline for '{scheme.official_name}' "
                                        f"approaching in {days_left} day(s) ({scheme.application_deadline.strftime('%d-%b-%Y') if scheme.application_deadline else 'N/A'})."
                                    ),
                                    is_dismissed=False,
                                )
                                session.add(alert_obj)
                                summary.new_alerts_created += 1

            session.commit()
            return summary
        except Exception:
            session.rollback()
            raise
        finally:
            if should_close:
                session.close()

    def list_active_alerts(self, limit: int = 50) -> List[DeadlineAlertItem]:
        session = self._get_session()
        should_close = (self._db is None)
        try:
            alerts = (
                session.query(SchemeDeadlineAlertModel, SchemeModel)
                .join(SchemeModel, SchemeDeadlineAlertModel.scheme_id == SchemeModel.id)
                .filter(SchemeDeadlineAlertModel.is_dismissed == False)
                .order_by(SchemeDeadlineAlertModel.days_remaining.asc(), SchemeDeadlineAlertModel.created_at.desc())
                .limit(limit)
                .all()
            )
            items = []
            for alert_row, scheme_row in alerts:
                items.append(DeadlineAlertItem(
                    alert_id=alert_row.id,
                    scheme_id=scheme_row.id,
                    scheme_name=scheme_row.official_name,
                    alert_type=alert_row.alert_type,
                    days_remaining=alert_row.days_remaining,
                    target_date=alert_row.target_date,
                    message=alert_row.message,
                    is_dismissed=alert_row.is_dismissed or False,
                    created_at=alert_row.created_at or datetime.utcnow(),
                ))
            return items
        finally:
            if should_close:
                session.close()

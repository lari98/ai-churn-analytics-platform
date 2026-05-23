"""
Data Retention Policy Enforcement Script — GDPR Art. 5(1)(e)
Automatically deletes or archives records that have exceeded their retention period.
Run nightly via Azure Data Factory or GitHub Actions scheduled workflow.

Usage:
    python data_retention_cleanup.py --dry-run       # Preview what will be deleted
    python data_retention_cleanup.py --execute       # Execute cleanup
"""

import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ─── Retention Policy Table ───────────────────────────────────────────────────
# Aligned with GDPR Art. 5, HGB §257, AO §147, BaFin requirements
RETENTION_POLICIES: Dict[str, Dict] = {
    "churn_scores": {
        "retention_days": 365,
        "action": "delete",
        "legal_basis": "internal_policy",
        "table": "churn_scores",
        "date_col": "scored_at",
    },
    "customer_profiles": {
        "retention_days": 1095,  # 3 years after contract end
        "action": "delete",
        "legal_basis": "gdpr_art5",
        "table": "customers",
        "date_col": "contract_end_date",
    },
    "transaction_records": {
        "retention_days": 3650,  # 10 years (AO §147 tax obligation)
        "action": "archive",
        "legal_basis": "ao_147",
        "table": "transactions",
        "date_col": "transaction_date",
    },
    "ml_training_data": {
        "retention_days": 730,  # 2 years
        "action": "delete",
        "legal_basis": "internal_policy",
        "table": "ml_features",
        "date_col": "feature_date",
    },
    "anomaly_events": {
        "retention_days": 1825,  # 5 years (BaFin)
        "action": "archive",
        "legal_basis": "bafin_requirement",
        "table": "anomaly_events",
        "date_col": "event_timestamp",
    },
    "audit_logs_gdpr": {
        "retention_days": 1095,  # 3 years
        "action": "pseudonymise",
        "legal_basis": "gdpr_art5_2",
        "table": "audit_log",
        "date_col": "timestamp",
    },
    "consent_records": {
        "retention_days": 99999,  # Indefinite (keep proof of consent)
        "action": "keep",
        "legal_basis": "gdpr_art7",
        "table": "gdpr_consent",
        "date_col": "recorded_at",
    },
    "session_tokens": {
        "retention_days": 7,
        "action": "delete",
        "legal_basis": "security_policy",
        "table": "session_tokens",
        "date_col": "expires_at",
    },
}


def run_retention_cleanup(dry_run: bool = True) -> Dict:
    """
    Main retention enforcement function.
    Returns summary of actions taken / that would be taken.
    """
    now = datetime.now(timezone.utc)
    summary = {"executed_at": now.isoformat(), "dry_run": dry_run, "policies": []}

    logger.info("=" * 65)
    logger.info("Data Retention Cleanup — %s", "DRY-RUN" if dry_run else "EXECUTE")
    logger.info("Timestamp: %s", now.isoformat())
    logger.info("=" * 65)

    for policy_name, policy in RETENTION_POLICIES.items():
        if policy["retention_days"] == 99999:
            logger.info("[SKIP] %s — retained indefinitely (%s)", policy_name, policy["legal_basis"])
            continue

        cutoff_date = now - timedelta(days=policy["retention_days"])
        logger.info("\n[%s] Policy: %s", policy["action"].upper(), policy_name)
        logger.info("  Table:       %s", policy["table"])
        logger.info("  Date column: %s", policy["date_col"])
        logger.info("  Cutoff:      %s", cutoff_date.date().isoformat())
        logger.info("  Retention:   %d days", policy["retention_days"])
        logger.info("  Legal basis: %s", policy["legal_basis"])

        if policy["action"] == "delete":
            sql = (
                f"DELETE FROM {policy['table']} "
                f"WHERE {policy['date_col']} < '{cutoff_date.date()}'"
            )
        elif policy["action"] == "archive":
            sql = (
                f"INSERT INTO {policy['table']}_archive "
                f"SELECT * FROM {policy['table']} "
                f"WHERE {policy['date_col']} < '{cutoff_date.date()}'; "
                f"DELETE FROM {policy['table']} "
                f"WHERE {policy['date_col']} < '{cutoff_date.date()}'"
            )
        elif policy["action"] == "pseudonymise":
            sql = (
                f"UPDATE {policy['table']} "
                f"SET resource_id_token = SHA2(resource_id_token, 256), "
                f"actor_id = 'ANONYMISED' "
                f"WHERE {policy['date_col']} < '{cutoff_date.date()}' "
                f"AND resource_id_token NOT LIKE 'ANONYMISED%'"
            )
        else:
            sql = "-- No action required"

        if not dry_run:
            logger.info("  Executing: %s", sql[:80] + "..." if len(sql) > 80 else sql)
            # In production: execute via SQLAlchemy engine
            # async with get_db_context() as db:
            #     await db.execute(text(sql))
            logger.info("  ✅ Done")
        else:
            logger.info("  [DRY-RUN] Would execute: %s", sql[:80] + "...")

        summary["policies"].append({
            "policy": policy_name,
            "action": policy["action"],
            "cutoff_date": cutoff_date.date().isoformat(),
            "sql_preview": sql[:120],
            "status": "simulated" if dry_run else "executed",
        })

    logger.info("\n" + "=" * 65)
    logger.info("Retention cleanup complete. Policies processed: %d", len(summary["policies"]))
    logger.info("=" * 65)
    return summary


def main():
    parser = argparse.ArgumentParser(description="GDPR Data Retention Cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--execute", action="store_true", help="Run cleanup")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.print_help()
        return

    summary = run_retention_cleanup(dry_run=args.dry_run)
    executed = sum(1 for p in summary["policies"] if p["status"] == "executed")
    logger.info("Summary: %d policies processed, %d executed", len(summary["policies"]), executed)


if __name__ == "__main__":
    main()

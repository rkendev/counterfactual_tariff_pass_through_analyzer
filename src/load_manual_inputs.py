from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psycopg2


@dataclass(frozen=True)
class ExposureRow:
    event_id: str
    firm_id: str
    exposed_flag: int
    exposure_bucket: Optional[str]
    evidence_note: Optional[str]


@dataclass(frozen=True)
class GrossMarginRow:
    event_id: str
    firm_id: str
    pre_period: str
    post_period: str
    gross_margin_pre: float
    gross_margin_post: float


def _req_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def load_exposure_csv(path: Path) -> list[ExposureRow]:
    rows: list[ExposureRow] = []
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"event_id", "firm_id", "exposed_flag", "exposure_bucket", "evidence_note"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"Exposure CSV missing columns: {sorted(missing)}")

        for row in r:
            event_id = (row["event_id"] or "").strip()
            firm_id = (row["firm_id"] or "").strip()
            exposed_flag = int((row["exposed_flag"] or "0").strip())
            exposure_bucket = (row["exposure_bucket"] or "").strip() or None
            evidence_note = (row["evidence_note"] or "").strip() or None

            if event_id == "" or firm_id == "":
                raise ValueError("Exposure CSV contains empty event_id or firm_id")
            if exposed_flag not in (0, 1):
                raise ValueError("exposed_flag must be 0 or 1")

            rows.append(
                ExposureRow(
                    event_id=event_id,
                    firm_id=firm_id,
                    exposed_flag=exposed_flag,
                    exposure_bucket=exposure_bucket,
                    evidence_note=evidence_note,
                )
            )
    return rows


def load_gross_margin_csv(path: Path) -> list[GrossMarginRow]:
    rows: list[GrossMarginRow] = []
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {
            "event_id",
            "firm_id",
            "pre_period",
            "post_period",
            "gross_margin_pre",
            "gross_margin_post",
        }
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"Observed gross margin CSV missing columns: {sorted(missing)}")

        for row in r:
            event_id = (row["event_id"] or "").strip()
            firm_id = (row["firm_id"] or "").strip()
            pre_period = (row["pre_period"] or "").strip()
            post_period = (row["post_period"] or "").strip()

            gmp = (row["gross_margin_pre"] or "").strip()
            gmo = (row["gross_margin_post"] or "").strip()

            if "REQUIRED" in {pre_period, post_period, gmp, gmo}:
                raise ValueError("Observed gross margin CSV still contains REQUIRED placeholders")

            gross_margin_pre = float(gmp)
            gross_margin_post = float(gmo)

            if event_id == "" or firm_id == "":
                raise ValueError("Observed gross margin CSV contains empty event_id or firm_id")

            rows.append(
                GrossMarginRow(
                    event_id=event_id,
                    firm_id=firm_id,
                    pre_period=pre_period,
                    post_period=post_period,
                    gross_margin_pre=gross_margin_pre,
                    gross_margin_post=gross_margin_post,
                )
            )
    return rows


def margin_change_sign(gm_pre: float, gm_post: float) -> int:
    diff = gm_post - gm_pre
    if diff > 0:
        return 1
    if diff < 0:
        return -1
    return 0


def upsert_exposure(cur, rows: list[ExposureRow]) -> None:
    sql = """
    INSERT INTO firm_event_exposure (event_id, firm_id, exposed_flag, exposure_bucket, evidence_note)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (event_id, firm_id)
    DO UPDATE SET
      exposed_flag = EXCLUDED.exposed_flag,
      exposure_bucket = EXCLUDED.exposure_bucket,
      evidence_note = EXCLUDED.evidence_note
    """
    for r in rows:
        cur.execute(sql, (r.event_id, r.firm_id, r.exposed_flag, r.exposure_bucket, r.evidence_note))


def upsert_observed_signs(cur, rows: list[GrossMarginRow]) -> None:
    sql = """
    INSERT INTO observed_margin_sign (event_id, firm_id, margin_change_sign)
    VALUES (%s, %s, %s)
    ON CONFLICT (event_id, firm_id)
    DO UPDATE SET
      margin_change_sign = EXCLUDED.margin_change_sign
    """
    for r in rows:
        s = margin_change_sign(r.gross_margin_pre, r.gross_margin_post)
        cur.execute(sql, (r.event_id, r.firm_id, s))


def main() -> None:
    event_id = "event_0002"
    base = Path("data") / "manual_inputs" / event_id

    exposure_csv = base / "exposure_labels.csv"
    observed_csv = base / "observed_gross_margin.csv"

    if not exposure_csv.exists():
        raise FileNotFoundError(f"Missing {exposure_csv}")
    if not observed_csv.exists():
        raise FileNotFoundError(f"Missing {observed_csv}")

    dsn = _req_env("DATABASE_URL")

    exposure_rows = load_exposure_csv(exposure_csv)

    observed_rows: list[GrossMarginRow] = []
    try:
        observed_rows = load_gross_margin_csv(observed_csv)
    except ValueError as e:
        msg = str(e)
        if "REQUIRED placeholders" in msg:
            print("Observed gross margin CSV still has REQUIRED placeholders. Skipping observed outcomes load for now.")
        else:
            raise

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            upsert_exposure(cur, exposure_rows)
            if observed_rows:
                upsert_observed_signs(cur, observed_rows)

    print("Loaded exposure labels. Observed outcomes loaded." if observed_rows else "Loaded exposure labels only.")


if __name__ == "__main__":
    main()

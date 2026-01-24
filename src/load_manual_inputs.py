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


@dataclass(frozen=True)
class FirmProfileRow:
    event_id: str
    firm_id: str
    firm_profile: str
    evidence_note: str


def _req_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _opt_env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v.strip() if v and v.strip() else default


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
                continue

            try:
                gross_margin_pre = float(gmp)
                gross_margin_post = float(gmo)
            except ValueError:
                print(
                    f"Skipping firm {firm_id}: non-numeric gross margin values "
                    f"(pre={gmp}, post={gmo})"
                )
                continue

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


def load_firm_profile_csv(path: Path) -> list[FirmProfileRow]:
    rows: list[FirmProfileRow] = []
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"event_id", "firm_id", "firm_profile", "evidence_note"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"Firm profile CSV missing columns: {sorted(missing)}")

        for row in r:
            event_id = (row["event_id"] or "").strip()
            firm_id = (row["firm_id"] or "").strip()
            firm_profile = (row["firm_profile"] or "").strip()
            evidence_note = (row["evidence_note"] or "").strip()

            if event_id == "" or firm_id == "":
                raise ValueError("Firm profile CSV contains empty event_id or firm_id")
            if firm_profile == "" or evidence_note == "":
                raise ValueError("Firm profile CSV contains empty firm_profile or evidence_note")

            rows.append(
                FirmProfileRow(
                    event_id=event_id,
                    firm_id=firm_id,
                    firm_profile=firm_profile,
                    evidence_note=evidence_note,
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


def upsert_firm_profiles(cur, rows: list[FirmProfileRow]) -> None:
    sql = """
    INSERT INTO firm_profile (event_id, firm_id, firm_profile, evidence_note)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (event_id, firm_id)
    DO UPDATE SET
      firm_profile = EXCLUDED.firm_profile,
      evidence_note = EXCLUDED.evidence_note
    """
    for r in rows:
        cur.execute(sql, (r.event_id, r.firm_id, r.firm_profile, r.evidence_note))


def _find_optional_profile_file(base: Path) -> Optional[Path]:
    candidates = [
        base / "firm_profile.csv",
        base / "firm_profiles.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def main() -> None:
    event_id = _opt_env("EVENT_ID", "event_0002")
    base = Path("data") / "manual_inputs" / event_id

    exposure_csv = base / "exposure_labels.csv"
    observed_csv = base / "observed_gross_margin.csv"
    profile_csv = _find_optional_profile_file(base)

    if not exposure_csv.exists():
        raise FileNotFoundError(f"Missing {exposure_csv}")

    dsn = _req_env("DATABASE_URL")

    exposure_rows = load_exposure_csv(exposure_csv)

    observed_rows: list[GrossMarginRow] = []
    if observed_csv.exists():
        observed_rows = load_gross_margin_csv(observed_csv)

    firm_profile_rows: list[FirmProfileRow] = []
    if profile_csv is not None:
        firm_profile_rows = load_firm_profile_csv(profile_csv)

        exposure_firms = {r.firm_id for r in exposure_rows}
        profile_firms = {r.firm_id for r in firm_profile_rows}
        missing_profiles = sorted(exposure_firms - profile_firms)
        if missing_profiles:
            raise ValueError(
                "Firm profile CSV is present but missing profiles for firms in exposure_labels.csv: "
                + ", ".join(missing_profiles)
            )

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            upsert_exposure(cur, exposure_rows)

            if firm_profile_rows:
                upsert_firm_profiles(cur, firm_profile_rows)

            if observed_rows:
                upsert_observed_signs(cur, observed_rows)

    msg = "Loaded exposure labels."
    if firm_profile_rows:
        msg += " Firm profiles loaded."
    if observed_rows:
        msg += " Observed outcomes loaded."
    else:
        msg += " Observed outcomes not loaded."
    print(msg)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Optional SQLite index for hurahura subject metadata.

The filesystem (META/*Tags*.json) remains the source of truth. When enabled via
miresearch.conf, this module mirrors study-level tags, per-series rows, full
JSON blobs, and configurable extra fields for local querying.
"""

from __future__ import annotations

import configparser
import json
import logging
import os
import sqlite3
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from hurahura.mi_config import MIResearch_config

logger = logging.getLogger(__name__)

DEFAULT_STUDY_COLUMNS = [
    "StudyDate",
    "StudyDescription",
    "StudyID",
    "StudyInstanceUID",
    "StudyTime",
    "PatientID",
    "PatientSex",
    "PatientBirthDate",
    "Modality",
    "Manufacturer",
    "MagneticFieldStrength",
    "BodyPartExamined",
    "AccessionNumber",
    "ANONYMISED",
    "Age",
]

SERIES_COLUMNS = [
    "SeriesNumber",
    "SeriesDescription",
    "StudyDate",
    "AcquisitionTime",
    "ScanDuration",
    "EchoTime",
    "RepetitionTime",
    "FlipAngle",
    "HeartRate",
    "DicomFileName",
]

_DB_INSTANCE = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, default=str, sort_keys=True)


def _parse_csv_list(value: str, keep_empty: bool = False) -> List[str]:
    if value is None or not str(value).strip():
        return []
    parts = [i.strip() for i in str(value).split(",")]
    if keep_empty:
        return parts
    return [i for i in parts if i]


def _parse_extra_field(spec: str) -> Tuple[str, str]:
    """Parse 'suffix:Tag' or 'Tag' (default suffix '')."""
    spec = spec.strip()
    if ":" in spec:
        suffix, tag = spec.split(":", 1)
        return suffix.strip(), tag.strip()
    return "", spec


class DatabaseConfig:
    """Database field map from miresearch.conf [database] section."""

    def __init__(self) -> None:
        self.study_columns: List[str] = list(DEFAULT_STUDY_COLUMNS)
        self.meta_suffixes: Optional[List[str]] = None  # None => discover on full sync
        self.extra_fields: List[Tuple[str, str]] = []
        self.sync_all_meta_json = True

    @classmethod
    def from_parser(cls, cp: configparser.ConfigParser) -> "DatabaseConfig":
        inst = cls()
        if not cp.has_section("database"):
            return inst
        if cp.has_option("database", "study_columns"):
            cols = _parse_csv_list(cp.get("database", "study_columns"))
            if cols:
                inst.study_columns = cols
        if cp.has_option("database", "meta_suffixes"):
            inst.meta_suffixes = _parse_csv_list(
                cp.get("database", "meta_suffixes"), keep_empty=True
            )
            inst.sync_all_meta_json = cp.getboolean(
                "database", "meta_sync_all", fallback=False
            )
        else:
            inst.sync_all_meta_json = cp.getboolean(
                "database", "meta_sync_all", fallback=True
            )
        if cp.has_option("database", "extra_fields"):
            for spec in _parse_csv_list(cp.get("database", "extra_fields")):
                inst.extra_fields.append(_parse_extra_field(spec))
        return inst


class MIResearchDatabase:
    """SQLite mirror of subject META JSON (local use only)."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        db_path: str,
        data_root: str,
        db_config: Optional[DatabaseConfig] = None,
    ) -> None:
        self.db_path = os.path.abspath(db_path)
        self.data_root = os.path.abspath(data_root)
        self.db_config = db_config or DatabaseConfig()
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None  # type: ignore[assignment]

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_info (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "INSERT OR IGNORE INTO schema_info (key, value) VALUES (?, ?)",
            ("version", str(self.SCHEMA_VERSION)),
        )
        study_cols_sql = ",\n    ".join(
            f'"{c}" TEXT' for c in self.db_config.study_columns
        )
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id TEXT PRIMARY KEY,
                subj_n INTEGER,
                data_root TEXT NOT NULL,
                top_dir TEXT,
                dicom_count INTEGER,
                series_count INTEGER,
                {study_cols_sql},
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meta_json (
                subject_id TEXT NOT NULL,
                meta_suffix TEXT NOT NULL,
                file_path TEXT,
                file_mtime REAL,
                json_text TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (subject_id, meta_suffix)
            )
            """
        )
        series_cols_sql = ",\n    ".join(f'"{c}" TEXT' for c in SERIES_COLUMNS)
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id TEXT NOT NULL,
                {series_cols_sql},
                json_text TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_series_subject ON series(subject_id)"
        )
        cur.execute(
            'CREATE INDEX IF NOT EXISTS idx_series_desc ON series("SeriesDescription")'
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS subject_extra (
                subject_id TEXT NOT NULL,
                field_key TEXT NOT NULL,
                meta_suffix TEXT NOT NULL,
                field_value TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (subject_id, field_key)
            )
            """
        )
        cur.execute(
            'CREATE INDEX IF NOT EXISTS idx_subjects_study_date ON subjects("StudyDate")'
        )
        self._conn.commit()
        self._ensure_study_columns()

    def _ensure_study_columns(self) -> None:
        """Add study columns from db config if schema predates config changes."""
        cur = self._conn.cursor()
        cur.execute("PRAGMA table_info(subjects)")
        existing = {row[1] for row in cur.fetchall()}
        for col in self.db_config.study_columns:
            if col not in existing:
                cur.execute(f'ALTER TABLE subjects ADD COLUMN "{col}" TEXT')
        self._conn.commit()

    def remove_subject(self, subject_id: str) -> None:
        cur = self._conn.cursor()
        for table in ("subject_extra", "series", "meta_json", "subjects"):
            cur.execute(f"DELETE FROM {table} WHERE subject_id = ?", (subject_id,))
        self._conn.commit()

    def rename_subject(self, old_id: str, new_id: str) -> None:
        if old_id == new_id:
            return
        cur = self._conn.cursor()
        for table in ("subject_extra", "series", "meta_json", "subjects"):
            cur.execute(
                f"UPDATE {table} SET subject_id = ? WHERE subject_id = ?",
                (new_id, old_id),
            )
        self._conn.commit()

    def get_meta_file_mtime(self, subject_id: str, meta_suffix: str) -> Optional[float]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT file_mtime FROM meta_json WHERE subject_id = ? AND meta_suffix = ?",
            (subject_id, meta_suffix),
        )
        row = cur.fetchone()
        return row["file_mtime"] if row else None

    def sync_subject_from_file(
        self,
        subject_id: str,
        subj_n: Optional[int],
        top_dir: str,
        meta_file: str,
        meta_suffix: str = "",
        meta_dict: Optional[dict] = None,
        dicom_count: Optional[int] = None,
    ) -> None:
        if meta_dict is None:
            if not os.path.isfile(meta_file):
                return
            with open(meta_file, "r", encoding="utf-8") as fh:
                meta_dict = json.load(fh)
        file_mtime = os.path.getmtime(meta_file) if os.path.isfile(meta_file) else None
        self._upsert_meta_json(
            subject_id, meta_suffix, meta_file, file_mtime, meta_dict
        )
        if meta_suffix == "":
            self._upsert_subject_row(
                subject_id,
                subj_n,
                top_dir,
                meta_dict,
                dicom_count=dicom_count,
            )
            self._upsert_series_rows(subject_id, meta_dict.get("Series") or [])
        self._upsert_extra_fields(subject_id, meta_dict, meta_suffix)

    def maybe_sync_from_disk(
        self,
        subject_id: str,
        subj_n: Optional[int],
        top_dir: str,
        meta_file: str,
        meta_suffix: str = "",
        meta_dict: Optional[dict] = None,
        dicom_count: Optional[int] = None,
    ) -> bool:
        """If JSON on disk is newer than DB row, refresh DB. Returns True if synced."""
        if not os.path.isfile(meta_file):
            return False
        disk_mtime = os.path.getmtime(meta_file)
        db_mtime = self.get_meta_file_mtime(subject_id, meta_suffix)
        if db_mtime is not None and disk_mtime <= db_mtime:
            return False
        self.sync_subject_from_file(
            subject_id,
            subj_n,
            top_dir,
            meta_file,
            meta_suffix=meta_suffix,
            meta_dict=meta_dict,
            dicom_count=dicom_count,
        )
        return True

    def _upsert_meta_json(
        self,
        subject_id: str,
        meta_suffix: str,
        meta_file: str,
        file_mtime: Optional[float],
        meta_dict: dict,
    ) -> None:
        now = _utc_now_iso()
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO meta_json (
                subject_id, meta_suffix, file_path, file_mtime, json_text, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(subject_id, meta_suffix) DO UPDATE SET
                file_path = excluded.file_path,
                file_mtime = excluded.file_mtime,
                json_text = excluded.json_text,
                updated_at = excluded.updated_at
            """,
            (
                subject_id,
                meta_suffix,
                meta_file,
                file_mtime,
                _json_dumps(meta_dict),
                now,
            ),
        )
        self._conn.commit()

    def _upsert_subject_row(
        self,
        subject_id: str,
        subj_n: Optional[int],
        top_dir: str,
        meta_dict: dict,
        dicom_count: Optional[int] = None,
    ) -> None:
        now = _utc_now_iso()
        series_list = meta_dict.get("Series") or []
        cols = self.db_config.study_columns
        values = {
            "subject_id": subject_id,
            "subj_n": subj_n if subj_n is not None else meta_dict.get("SubjN"),
            "data_root": self.data_root,
            "top_dir": top_dir,
            "dicom_count": dicom_count,
            "series_count": len(series_list),
            "updated_at": now,
        }
        for col in cols:
            values[col] = _scalar(meta_dict.get(col))

        col_names = list(values.keys())
        placeholders = ", ".join("?" for _ in col_names)
        col_sql = ", ".join(f'"{c}"' for c in col_names)
        update_sql = ", ".join(
            f'"{c}" = excluded."{c}"' for c in col_names if c != "subject_id"
        )
        cur = self._conn.cursor()
        cur.execute(
            f"""
            INSERT INTO subjects ({col_sql}) VALUES ({placeholders})
            ON CONFLICT(subject_id) DO UPDATE SET {update_sql}
            """,
            tuple(values[c] for c in col_names),
        )
        self._conn.commit()

    def _upsert_series_rows(self, subject_id: str, series_list: Sequence[dict]) -> None:
        now = _utc_now_iso()
        cur = self._conn.cursor()
        cur.execute("DELETE FROM series WHERE subject_id = ?", (subject_id,))
        for ser in series_list:
            row = {c: _scalar(ser.get(c)) for c in SERIES_COLUMNS}
            row["subject_id"] = subject_id
            row["json_text"] = _json_dumps(ser)
            row["updated_at"] = now
            col_names = list(row.keys())
            placeholders = ", ".join("?" for _ in col_names)
            col_sql = ", ".join(f'"{c}"' for c in col_names)
            cur.execute(
                f"INSERT INTO series ({col_sql}) VALUES ({placeholders})",
                tuple(row[c] for c in col_names),
            )
        self._conn.commit()

    def _upsert_extra_fields(
        self, subject_id: str, meta_dict: dict, meta_suffix: str
    ) -> None:
        if not self.db_config.extra_fields:
            return
        now = _utc_now_iso()
        cur = self._conn.cursor()
        for suffix, tag in self.db_config.extra_fields:
            if suffix != meta_suffix:
                continue
            key = f"{suffix}:{tag}" if suffix else tag
            val = meta_dict.get(tag)
            cur.execute(
                """
                INSERT INTO subject_extra (
                    subject_id, field_key, meta_suffix, field_value, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(subject_id, field_key) DO UPDATE SET
                    field_value = excluded.field_value,
                    meta_suffix = excluded.meta_suffix,
                    updated_at = excluded.updated_at
                """,
                (subject_id, key, meta_suffix, _scalar(val), now),
            )
        self._conn.commit()

    def query_subjects(
        self,
        where_sql: str = "",
        params: Sequence[Any] = (),
        order_by: str = '"StudyDate", subject_id',
    ) -> List[sqlite3.Row]:
        sql = "SELECT * FROM subjects"
        if where_sql:
            sql += f" WHERE {where_sql}"
        sql += f" ORDER BY {order_by}"
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return list(cur.fetchall())

    def execute(self, sql: str, params: Sequence[Any] = ()) -> List[sqlite3.Row]:
        cur = self._conn.cursor()
        cur.execute(sql, params)
        if sql.strip().upper().startswith("SELECT"):
            return list(cur.fetchall())
        self._conn.commit()
        return []


def _scalar(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return _json_dumps(value)
    return str(value)


def discover_meta_suffixes(meta_dir: str, subject_id: str) -> List[str]:
    prefix = f"{subject_id}Tags"
    suffixes: List[str] = []
    if not os.path.isdir(meta_dir):
        return suffixes
    for fn in os.listdir(meta_dir):
        if fn.startswith(prefix) and fn.endswith(".json"):
            suffixes.append(fn[len(prefix) : -5])
    return sorted(suffixes)


def get_database(force_new: bool = False) -> Optional[MIResearchDatabase]:
    """Return an open database for the current config, or None if disabled."""
    global _DB_INSTANCE
    if not getattr(MIResearch_config, "database_enabled", False):
        return None
    if force_new and _DB_INSTANCE is not None:
        _DB_INSTANCE.close()
        _DB_INSTANCE = None
    if _DB_INSTANCE is not None:
        return _DB_INSTANCE
    db_path = MIResearch_config.database_path
    db_config = getattr(MIResearch_config, "database_field_config", None) or DatabaseConfig()
    _DB_INSTANCE = MIResearchDatabase(
        db_path=db_path,
        data_root=MIResearch_config.data_root_dir,
        db_config=db_config,
    )
    return _DB_INSTANCE


def reset_database_instance() -> None:
    global _DB_INSTANCE
    if _DB_INSTANCE is not None:
        _DB_INSTANCE.close()
        _DB_INSTANCE = None


def sync_subject_to_database(subject, meta_suffix: str = "", meta_dict: Optional[dict] = None) -> None:
    """Push subject META JSON to the database if enabled."""
    db = get_database()
    if db is None:
        return
    try:
        meta_file = subject.getMetaTagsFile(meta_suffix)
        if meta_dict is None and not os.path.isfile(meta_file):
            return
        db.sync_subject_from_file(
            subject.subjID,
            getattr(subject, "_subjN", None),
            subject.getTopDir(),
            meta_file,
            meta_suffix=meta_suffix,
            meta_dict=meta_dict,
            dicom_count=subject.countNumberOfDicoms() if meta_suffix == "" else None,
        )
    except Exception as exc:
        logger.warning("Database sync failed for %s: %s", subject.subjID, exc)


def maybe_refresh_subject_meta_from_database(subject, meta_suffix: str = "") -> None:
    """If JSON on disk changed outside hurahura, update the database."""
    db = get_database()
    if db is None:
        return
    try:
        meta_file = subject.getMetaTagsFile(meta_suffix)
        if not os.path.isfile(meta_file):
            return
        db.maybe_sync_from_disk(
            subject.subjID,
            getattr(subject, "_subjN", None),
            subject.getTopDir(),
            meta_file,
            meta_suffix=meta_suffix,
        )
    except Exception as exc:
        logger.warning("Database refresh check failed for %s: %s", subject.subjID, exc)


def sync_all_subjects_in_data_root(
    data_root: Optional[str] = None,
    subject_prefix: Optional[str] = None,
    SubjClass=None,
) -> int:
    """Rebuild the database from all subjects' META JSON files. Returns subject count."""
    from hurahura.mi_subject import SubjectList, get_configured_subject_class

    db = get_database()
    if db is None:
        raise RuntimeError("Database is not enabled in configuration")

    if SubjClass is None:
        SubjClass = get_configured_subject_class()
    data_root = data_root or MIResearch_config.data_root_dir
    subject_prefix = subject_prefix or MIResearch_config.subject_prefix
    subj_list = SubjectList.setByDirectory(
        data_root, subjectPrefix=subject_prefix, SubjClass=SubjClass
    )
    count = 0
    for subj in subj_list:
        suffixes = db.db_config.meta_suffixes
        if suffixes is None or db.db_config.sync_all_meta_json:
            suffixes = discover_meta_suffixes(subj.getMetaDir(), subj.subjID)
        elif not suffixes:
            suffixes = [""]
        for suffix in suffixes:
            sync_subject_to_database(subj, meta_suffix=suffix)
        count += 1
    return count

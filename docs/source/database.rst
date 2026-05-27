.. _database:

Optional local database
=========================

hurahura stores subject metadata on disk under each subject's ``META`` directory
(``{SubjectID}Tags.json`` and optional suffixed variants). For local projects that
benefit from SQL queries, an **optional SQLite** index can be enabled. The filesystem
remains the source of truth; the database is updated when hurahura writes meta JSON
and when existing JSON files are newer than the stored copy.

Enable in ``miresearch.conf``::

    [database]
    enabled = true
    db_path =
    sync_on_meta_write = true
    study_columns = StudyDate, StudyDescription, PatientID, Modality, ANONYMISED, Age
    meta_suffixes =
    meta_sync_all = true
    extra_fields = ANONYMISED

- **db_path** — SQLite file (default: ``hurahura.db`` in ``data_root_dir``).
- **sync_on_meta_write** — Update the database when ``updateMetaFile`` runs (default true).
- **study_columns** — Comma-separated top-level keys from the main Tags JSON to mirror
  as ``subjects`` table columns.
- **meta_suffixes** — Comma-separated META JSON suffixes to track (empty entry before
  the first comma means the main ``{SubjectID}Tags.json``). If omitted, ``-DBSync``
  discovers every ``*Tags*.json`` under each subject META folder when **meta_sync_all**
  is true (default).
- **meta_sync_all** — When true, full sync includes all discovered Tags JSON files.
- **extra_fields** — Comma-separated ``[suffix:]TagName`` entries promoted to
  ``subject_extra`` for SQL filters.

Rebuild the index from all subjects::

    hurahura -config my.conf -sA -DBSync

Tables (conceptual):

- **subjects** — Study-level tags from the main Tags JSON (configurable columns).
- **series** — One row per DICOM series from the ``Series`` list in that JSON.
- **meta_json** — Full JSON text per meta suffix (for ad hoc inspection).
- **subject_extra** — Key/value pairs from ``[database] extra_fields``.

SQLite is appropriate for single-user, single-machine use. It is not intended for
multi-user or networked deployments; use export or a dedicated server database for those.

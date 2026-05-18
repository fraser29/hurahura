# hurahura — Agent Instructions

Medical imaging research data management: organise studies on a **per-examination** basis, store DICOM in a predictable directory layout, and automate loading, metadata extraction, querying, and anonymisation. Former package name: **miresearch** (still reflected in config filenames and some module names).

Published docs: https://fraser29.github.io/hurahura/

## Domain vocabulary

| Term | Meaning |
|------|---------|
| **Subject** | One examination / case — a directory under `dataRoot`, not a clinical trial “subject” in the epidemiology sense unless your study defines it that way. |
| **Subject ID** | `PREFIX` + zero-padded number + optional suffix, e.g. `BRAIN000001`. |
| **dataRoot** | Root directory containing all subject folders (`-y` or `data_root_dir` in config). |
| **RAW/DICOM** | On-disk DICOM tree for a subject. |
| **META** | Logs, extracted tag JSON, `summary.csv` for querying without opening every DICOM. |
| **AbstractSubject** | Base class in `hurahura/mi_subject.py` — extend for study-specific pipelines. |

There is **no database**; behaviour is defined by the filesystem layout and META files.

## Repository layout

```
hurahura/
  mi_subject.py          # AbstractSubject, SubjectList, loading, meta, anonymisation
  mi_utils.py            # DirectoryStructureTree, DICOM tag lists, helpers
  mi_config.py           # miresearch.conf parsing (MIResearch_config singleton)
  miresearch_main.py     # CLI entry (hurahura), argparse groups, runActions
  miresearch_watchdog.py # Watch-directory auto-load (pairs with AUTORTHANC)
  miresearch.conf        # Default config shipped with package
  miresearchui/          # NiceGUI web UI (-UI)
  tests/                 # unittest suite + TEST_DATA DICOM fixtures
docs/source/             # Sphinx RST (build via make docs)
```

## Setup

```bash
# Editable install for development
pip install -e .

# Optional: inspect effective configuration
hurahura -INFO
```

**Python:** `>=3.9` (see `pyproject.toml`).

**Key dependencies:** [spydcmtk](https://pypi.org/project/spydcmtk/) (DICOM I/O and anonymisation), pandas, numpy, watchdog, nicegui, ngawari.

## Common commands

```bash
# Tests (uses real DICOM under hurahura/tests/TEST_DATA)
python -m pytest hurahura/tests/
# or
python -m hurahura.tests.run_tests

# Documentation
make docs          # build HTML → docs/build/html
make docs-serve    # local preview on :8000
make docs-clean
```

## Configuration

Config file name remains **`miresearch.conf`**. Search order (later overrides earlier):

1. `hurahura/miresearch.conf` (package defaults)
2. `$HOME/miresearch.conf`
3. `$HOME/.miresearch.conf`
4. `$HOME/.config/miresearch.conf`
5. `$MIRESEARCH_CONF`
6. `-config /path/to/file` on CLI

Important `[app]` keys:

- `data_root_dir`, `subject_prefix`, `directories` (JSON list, e.g. `[["RAW", "DICOM"], "META"]`)
- `class_path` — dotted path to custom `AbstractSubject` subclass
- `anon_level` — `NONE` | `SOFT` | `HARD` (see `docs/source/anonymisation.rst`)

String values in `.conf` must **not** use quotes except inside JSON list values (double-quoted).

## Architecture notes for agents

### Central types

- **`AbstractSubject`** (`hurahura/mi_subject.py`): build/load subjects, DICOM ingest, META generation, anonymise, rename, archive, zip.
- **`SubjectList`**: list-like collection; filter by date of scan, series description, etc.
- **`get_configured_subject_class()`**: loads `class_path` from config; falls back to `AbstractSubject` on error.
- **`DirectoryStructureTree`** (`hurahura/mi_utils.py`): declarative per-subject folder layout; subclass constructors can pass a custom tree.

### CLI extension pattern

Studies can subclass and wire custom CLI without forking the package. Canonical example: `hurahura/tests/mi_subject_test.py`:

1. Subclass `AbstractSubject` (override e.g. `runPostLoadPipeLine`).
2. Set `class_path` in config to `your.module.YourSubject`.
3. Pass `extra_runActions` into `miresearch_main.main()` or register argument groups via `getArgGroup()`.

### UI integration

Methods exposed in the web UI use the `@ui_method` decorator on `AbstractSubject` (description, category, order). UI code lives under `hurahura/miresearchui/` (NiceGUI).

### Watch directory

`hurahura -WatchDirectory <path>` uses `miresearch_watchdog.py` to ingest stable new folders; often used with [AUTORTHANC](https://github.com/fraser29/autorthanc).

## Coding conventions

- Match existing style: module docstrings, argparse **groups** in `miresearch_main.py`, `logging` on subjects, minimal drive-by refactors.
- Prefer extending **`AbstractSubject`** / **`SubjectList`** over duplicating DICOM path logic; use **spydcmtk** (`spydcmtk.spydcm`) for DICOM operations already used in `mi_subject.py`.
- New study-specific behaviour belongs in a **subclass** or config-driven `class_path`, not hard-coded into `AbstractSubject` unless it benefits all users.
- Keep changes scoped to the task; update Sphinx docs in `docs/source/` when user-facing behaviour or CLI flags change.
- Do not add markdown files the user did not ask for (except this `AGENTS.md`).

## Testing expectations

- Tests are **`unittest`**-based in `hurahura/tests/run_tests.py` (pytest discovers them too).
- Fixtures live in `hurahura/tests/TEST_DATA/`; tests create temp dirs beside the test module and remove them unless `DEBUG` is true in config.
- After changes to loading, META, anonymisation, or subject ID rules, run the full test module.
- Example subclass/config test: `TestSubjectUseConfFile` + `hurahura/tests/testA.conf`.

## Safety and compliance

- This codebase handles **medical imaging and potentially identifiable patient data**.
- Treat `hurahura/tests/TEST_DATA/` and any user `dataRoot` as sensitive; never commit real patient data or paste PHI into issues/PRs.
- Anonymisation levels (`NONE` / `SOFT` / `HARD`) have different reversibility; see `docs/source/anonymisation.rst` before changing anonymise behaviour.
- Use `-FORCE` only when the user explicitly wants destructive rebuilds (e.g. `-Meta` rebuild).

## Documentation

- User-facing docs: reStructuredText under `docs/source/` (introduction, concept, usage, anonymisation, watch_dog, web_interface).
- CI (`.github/workflows/documentation.yml`) builds Sphinx on push/PR and publishes to `gh-pages`.
- When adding CLI flags, mirror the pattern in `miresearch_main.py` argument groups and document in the appropriate `.rst` file.

## Definition of done

- [ ] Behaviour covered or justified by tests in `hurahura/tests/` when touching core subject logic
- [ ] `python -m pytest hurahura/tests/` passes
- [ ] No accidental changes to default `miresearch.conf` unless intentional
- [ ] User-facing CLI/config changes reflected in `docs/source/` when appropriate
- [ ] No secrets, real patient paths, or PHI in the diff

## Quick reference — CLI surface

Entry point: `hurahura` → `hurahura.miresearch_main:main`.

Representative flags (see `hurahura -h` for full list):

| Area | Flags |
|------|--------|
| Subjects | `-s`, `-sA`, `-sR`, `-y`, `-sPrefix`, `-sSuffix` |
| Load / build | `-Build`, `-Load`, `-LoadOther`, `-LOAD_MULTI` |
| Subject ops | `-RunPost`, `-Meta`, `-SubjInfo`, `-anonName` |
| Group | `-Summary`, `-SummaryCSV` |
| Watch / UI | `-WatchDirectory`, `-UI`, `-UI_port` |
| Debug | `-INFO`, `-DEBUG`, `-QUIET`, `-FORCE` |

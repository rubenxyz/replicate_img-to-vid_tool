# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common commands

- Setup (Python venv + deps)
  - python3 -m venv venv
  - source venv/bin/activate
  - pip install -r requirements.txt
  - pip install pytest
- Auth
  - Default: sign in to 1Password CLI (op signin). The tool auto-discovers any USER-FILES/01.CONFIG/auth*.yml or auth*.yaml (e.g., auth_bites.yaml) and uses replicate.item_name/field_name to fetch the token.
  - Optional fallback: set REPLICATE_API_TOKEN in a .env or environment and run with env fallback (authenticate(use_1password=False))
    - export REPLICATE_API_TOKEN={{REPLICATE_API_TOKEN}}
- Run (standard)
  - python -m src.main
- Run (verbose progress + async polling)
  - python -m src.main_verbose
- Estimate costs only (no generation)
  - python -m src.estimate_costs
- Tests
  - Run all: pytest -q
  - Single test: pytest tests/test_duration_handler.py::TestSecondsDuration::test_seconds_rounding_up -q
- Lint/format
  - No linter is configured in-repo. If installed locally:
    - ruff check .
    - black --check .

## High-level architecture

- Inputs and profiles
  - Triplet inputs live under USER-FILES/04.INPUT/ as three folders: 04.1.IMAGE_URL, 04.2.NUM_FRAMES, 04.3.PROMPT. Files are matched by natural sort order (not by identical filenames). Counts must match across folders.
  - Video profiles live under USER-FILES/03.PROFILES as YAML. Each profile must include:
    - Model: endpoint (e.g., bytedance/seedance-1-lite)
    - pricing: one of cost_per_frame | cost_per_second | cost_per_prediction
    - duration_*: duration_type (frames|seconds), fps, duration_min, duration_max, duration_param_name
    - params: model-specific parameters; optional image_url_param (defaults to "image")
- Processing flows
  - Standard: src/processing/processor.py::process_matrix
    - Discovers inputs (input_discovery), loads profiles (profile_loader + profile_validator)
    - Creates timestamped run dir under USER-FILES/05.OUTPUT/YYMMDD_HHMMSS
    - For each (triplet × profile): prepares parameters (duration_handler), generates via ReplicateClient (api/client.py), downloads video, computes cost, writes documentation
  - Verbose: src/processing/verbose_processor.py::process_matrix_verbose
    - Uses AsyncReplicateClient (api/async_client.py) with progress polling and rich UI
- Replicate integration
  - ReplicateClient wraps client.run with retry/backoff and long timeouts (utils/timeouts + config/constants)
  - AsyncReplicateClient uses predictions.create + polling; extracts progress when available
  - Authentication resolves via 1Password (src/auth/op_auth.py) or .env/.env vars (src/auth/env.py)
- Outputs and reporting
  - Per-run: USER-FILES/05.OUTPUT/YYMMDD_HHMMSS/
  - Per-video subfolder: {prompt_stem}_X_{profile_name}/ with
    - .mp4 video, VIDEO_REPORT.md, generation_payload.json, generation.log, copies of source_*.txt
  - Top-level run reports: SUCCESS.md (summary) and cost_report.md; ADJUSTMENTS.md is generated when any duration was clamped/converted
- Error handling and logging
  - Custom exceptions in src/exceptions.py; fail-fast on generation errors
  - Loguru-based logging to console and logs/ with rotation (utils/logging.py, utils/enhanced_logging.py)

## Rules and constraints (from CLAUDE.md)

- USER-FILES safety
  - Never modify, move, or delete files in USER-FILES/ without explicit permission
  - Only read from USER-FILES/04.INPUT/; only write to USER-FILES/05.OUTPUT/ with YYMMDD_HHMMSS timestamps
- Agent behavior
  - Ask for clarification when requirements are ambiguous; verify changes work; run tests before confirming
- Code standards
  - Use type hints; prefer pathlib.Path for file ops; keep functions small where practical
- Testing
  - Write tests for critical paths and mock external APIs as needed
- API usage
  - Use timeouts, basic retry with backoff, and handle rate limits

## Notes from README.md

- Quick start uses a virtualenv and runs python -m src.main
- The tool batch-generates videos from image URL + motion prompt triplets and produces comprehensive per-video docs plus run-level reports

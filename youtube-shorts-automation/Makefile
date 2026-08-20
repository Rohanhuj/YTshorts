.PHONY: format lint typecheck test secret-scan ffmpeg-smoke verify

UV_CACHE_DIR ?= .uv-cache
export UV_CACHE_DIR

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy src tests

test:
	uv run pytest --cov=shorts_automation --cov-report=term-missing

secret-scan:
	uv run python scripts/check_no_secrets.py

ffmpeg-smoke:
	uv run python scripts/ffmpeg_smoke.py

verify: lint typecheck test secret-scan ffmpeg-smoke

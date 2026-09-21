.PHONY: setup data notebooks test all

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Project standard is Python 3.13; 3.11+ is required.
# Override with `make setup PYTHON_BOOTSTRAP=/path/to/python` if none of the
# auto-detected interpreters below are suitable.
PYTHON_BOOTSTRAP ?=
MIN_PY_MAJOR := 3
MIN_PY_MINOR := 11

# iCloud Drive skips syncing any folder whose name ends in .nosync. When
# ~/Documents is iCloud-synced, a venv placed directly under it gets partially
# uploaded/evicted mid-use and breaks. In that case we create $(VENV).nosync
# instead and symlink $(VENV) -> $(VENV).nosync, so every other target below
# can keep referring to plain $(VENV).
ICLOUD_DOCS := $(HOME)/Library/Mobile Documents/com~apple~CloudDocs/Documents

setup:
	@if [ -d "$(ICLOUD_DOCS)" ]; then \
		target="$(VENV).nosync"; \
		echo "iCloud-synced Documents detected -> will create $$target and symlink $(VENV) to it"; \
	else \
		target="$(VENV)"; \
		echo "Documents is not iCloud-synced -> will create $$target"; \
	fi; \
	if [ -n "$(PYTHON_BOOTSTRAP)" ]; then \
		if ! command -v "$(PYTHON_BOOTSTRAP)" >/dev/null 2>&1; then \
			echo "PYTHON_BOOTSTRAP=$(PYTHON_BOOTSTRAP) not found or not executable." >&2; \
			exit 1; \
		fi; \
		candidates="$(PYTHON_BOOTSTRAP)"; \
	else \
		candidates="python3.13 python3.12 python3.11 python3 /opt/miniconda3/bin/python3 /opt/homebrew/bin/python3"; \
	fi; \
	found=""; \
	for candidate in $$candidates; do \
		if ! command -v "$$candidate" >/dev/null 2>&1; then \
			echo "Skipping $$candidate: not found"; \
			continue; \
		fi; \
		resolved=$$(command -v "$$candidate"); \
		ver=$$("$$candidate" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null); \
		major=$$(printf '%s' "$$ver" | cut -d. -f1); \
		minor=$$(printf '%s' "$$ver" | cut -d. -f2); \
		if [ -z "$$major" ]; then \
			echo "Skipping $$candidate ($$resolved): could not determine Python version"; \
			continue; \
		fi; \
		if [ "$$major" -lt $(MIN_PY_MAJOR) ] || { [ "$$major" -eq $(MIN_PY_MAJOR) ] && [ "$$minor" -lt $(MIN_PY_MINOR) ]; }; then \
			echo "Skipping $$candidate ($$resolved): Python $$ver, need $(MIN_PY_MAJOR).$(MIN_PY_MINOR)+"; \
			continue; \
		fi; \
		if ! "$$candidate" -c "import venv, ensurepip" >/dev/null 2>&1; then \
			echo "Skipping $$candidate ($$resolved): missing venv/ensurepip module"; \
			continue; \
		fi; \
		rm -rf "$$target"; \
		if "$$candidate" -m venv "$$target" >/tmp/retail-analytics-setup-venv.log 2>&1; then \
			echo "Using $$candidate ($$resolved, Python $$ver)"; \
			found="$$candidate"; \
			break; \
		fi; \
		echo "Skipping $$candidate ($$resolved): Python $$ver has venv/ensurepip modules but venv creation failed (broken interpreter install - see /tmp/retail-analytics-setup-venv.log)"; \
		rm -rf "$$target"; \
	done; \
	if [ -z "$$found" ]; then \
		echo "" >&2; \
		echo "ERROR: Python $(MIN_PY_MAJOR).$(MIN_PY_MINOR)+ with venv support required. Tried: $$candidates." >&2; \
		echo "Install a working Python $(MIN_PY_MAJOR).$(MIN_PY_MINOR)+ (project standard: Python 3.13), or point make at one directly:" >&2; \
		echo "    make setup PYTHON_BOOTSTRAP=/path/to/python3.13" >&2; \
		exit 1; \
	fi; \
	if [ "$$target" != "$(VENV)" ]; then ln -sfn "$$target" $(VENV); fi
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt

# Downloads the source .xlsx from UCI (data/raw/, gitignored), combines its
# two sheets, then runs sql/00_clean.sql via DuckDB to write the cleaned
# table to data/processed/ (gitignored). Only runs when the processed file
# is missing, so re-running `make data` after the first time is a no-op.
data:
	PYTHONPATH=src $(PYTHON) -m retail_analytics.download

# Executes every notebook top to bottom so results in reports/figures/
# always come from code that actually ran. Registers a project-local Jupyter
# kernel pointed at .venv first, since nbconvert's default "python3" kernel
# otherwise resolves to whatever Python is registered system-wide.
KERNEL_NAME := retail-customer-analytics
notebooks: data
	$(PYTHON) -m ipykernel install --user --name=$(KERNEL_NAME) --display-name="$(KERNEL_NAME)" >/dev/null
	$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace \
		--ExecutePreprocessor.kernel_name=$(KERNEL_NAME) \
		notebooks/01_data_quality.ipynb notebooks/02_customer_base.ipynb \
		notebooks/03_segmentation.ipynb notebooks/04_clv.ipynb

test:
	$(PYTHON) -m pytest tests/ -v

all: setup data notebooks test

# ============================================================
#  fly-in — Makefile
#  Python needs no compilation; these targets automate the
#  common tasks required by the subject (III.2).
# ============================================================

PYTHON := python3
MAIN   := main.py

MAP    ?= maps/easy/01_linear_path.txt

.PHONY: install run debug clean lint lint-strict help


install:
	$(PYTHON) -m pip install --upgrade flake8 mypy


run:
	$(PYTHON) $(MAIN) $(MAP)

debug:
	$(PYTHON) -m pdb $(MAIN) $(MAP)


clean:
	rm -rf .mypy_cache
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs


lint-strict:
	flake8 .
	mypy . --strict

help:
	@echo "targets:"
	@echo "  make install      install flake8 + mypy"
	@echo "  make run          run on \$$MAP (default: $(MAP))"
	@echo "  make debug        run under pdb"
	@echo "  make lint         flake8 . + mypy (subject flags)"
	@echo "  make lint-strict  flake8 . + mypy --strict"
	@echo "  make clean        remove caches / bytecode"
	@echo "  make run MAP=path/to/map.txt   run a specific map"
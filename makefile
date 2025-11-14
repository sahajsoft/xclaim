VENV = venv
PYTHON = python3
SCRIPT = expense_agent.py

CLAIM_TITLE ?= ""

# 1. Create venv only if missing
$(VENV)/bin/python:
	$(PYTHON) -m venv $(VENV)

# 2. Install dependencies
install: $(VENV)/bin/python
	./$(VENV)/bin/python -m pip install --upgrade pip
	./$(VENV)/bin/python -m pip install -r requirements.txt

# 3. Run the script
run: install
	./$(VENV)/bin/python $(SCRIPT) --claim-title "$(CLAIM_TITLE)"

# 4. Full workflow
all: run

# 5. Cleanup
clean:
	rm -rf $(VENV)

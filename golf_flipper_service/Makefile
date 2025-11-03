PYTHON=python3

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port $$PORT --reload

test:
	$(PYTHON) -m pytest -q

.PHONY: install run test
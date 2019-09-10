clean-pyc:
	find . -name '*.pyc' -exec rm {} +
	find . -name '*.pyo' -exec rm {} +
	find . -name '*~' -exec rm {} +

# This command assumes that you have python3 installed which comes with the venv command
venv:
	python3 -m venv .venv && \
			source .venv/bin/activate && \
			pip install -r ./requirements/main.txt

serve:
	docker-compose up


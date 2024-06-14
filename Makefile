
FORCE:

dev_env:
	pip install -r requirements.txt

black:
	black ai db server transcribe

clear_cache:
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

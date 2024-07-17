
FORCE:

dev_env:
	pip install -r requirements.txt

black:
	black ai db server transcribe read_files

quick_test:
	pytest -m "not (ai or deepgram)"

clear_cache:
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

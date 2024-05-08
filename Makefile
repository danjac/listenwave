install: pyinstall npminstall precommitinstall nltkdownload
update: pyupdate npmupdate precommitupdate

pyinstall:
	uv venv && source .venv/bin/activate
	uv pip install -r requirements-ci.txt

pyupdate:
	uv pip compile pyproject.toml --upgrade -o requirements.txt
	uv pip compile pyproject.toml --upgrade --extra dev -o requirements-ci.txt
	uv pip sync requirements-ci.txt

npminstall:
	npm ci

npmupdate:
	npm run check-updates && npm install npm-update-all

precommitinstall:
	pre-commit install

precommitupdate:
	pre-commit autoupdate

nltkdownload:
	xargs -I{} .venv/bin/python -c "import nltk; nltk.download('{}')" < nltk.txt

clean:
	git clean -Xdf

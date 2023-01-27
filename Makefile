install: install-poetry install-npm install-precommit install-nltk

update: update-poetry update-npm update-precommit

install-poetry:
	poetry install --no-root -vvv

install-npm:
	npm ci

install-precommit:
	pre-commit install

install-nltk:
	xargs python -m nltk.downloader <./nltk.txt

update-poetry:
	poetry update --no-cache -vvv

poetry-export:
	poetry export -o requirements.txt --without-hashes -vvvv
	poetry export -o requirements-ci.txt --with=dev --without-hashes -vvvv

update-npm:
	npm run check-updates && npm install

update-precommit:
	pre-commit autoupdate

test:
	python -m pytest

shell:
	python ./manage.py shell_plus

serve:
	python ./manage.py runserver

db:
	python ./manage.py migrate
	python ./manage.py loaddata ./radiofeed/podcasts/fixtures/categories.json.gz
	python ./manage.py loaddata ./radiofeed/podcasts/fixtures/podcasts.json.gz

watch:
	npm run watch

clean:
	git clean -Xdf

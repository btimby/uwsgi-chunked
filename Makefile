DOCKER_COMPOSE=docker-compose


.venv: Pipfile
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
	touch .venv


deps: .venv


build:
	${DOCKER_COMPOSE} build


run:
	${DOCKER_COMPOSE} up


test: deps
	pipenv run coverage run -m unittest test.py


lint: deps
	pipenv run pylint uwsgi_chunked

curl:
	echo -n 'whom=friend' | curl -T- http://localhost:8000/stream


ci: test lint

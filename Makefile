DOCKER_COMPOSE=docker-compose


.venv: Pipfile
	PIPENV_VENV_IN_PROJECT=1 pipenv install
	touch .venv


deps: .venv


build:
	${DOCKER_COMPOSE} build


run:
	${DOCKER_COMPOSE} up


test: deps
	pipenv run python3 -m unittest test.py


curl:
	echo -n 'whom=friend' | curl -T- http://localhost:8000/stream

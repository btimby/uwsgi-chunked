DOCKER_COMPOSE=docker-compose


build:
	${DOCKER_COMPOSE} build


run:
	${DOCKER_COMPOSE} up


test:
	python3 -m unittest test.py

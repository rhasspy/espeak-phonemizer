SHELL := bash

.PHONY: check clean reformat dist test espeak

all: dist

venv:
	scripts/create-venv.sh

check:
	scripts/check-code.sh

reformat:
	scripts/format-code.sh

test:
	scripts/run-tests.sh

dist:
	python3 setup.py bdist_wheel -p linux_x86_64
	python3 setup.py bdist_wheel -p linux_aarch64

espeak:
	docker buildx build . --platform 'linux/amd64,linux/arm64' --output 'type=local,dest=dist'

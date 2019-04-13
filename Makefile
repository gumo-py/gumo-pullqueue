package_name = gumo-pullqueue

export PATH := venv/bin:$(shell echo ${PATH})

.PHONY: setup
setup:
	[ -d venv ] || python3 -m venv venv
	pip3 install twine wheel pytest
	pip3 install -r requirements.txt

.PHONY: deploy
deploy: clean build
	python3 -m twine upload \
		--repository-url https://upload.pypi.org/legacy/ \
		dist/*

.PHONY: test-deploy
test-deploy: clean build
	python3 -m twine upload \
		--repository-url https://test.pypi.org/legacy/ \
		dist/*

.PHONY: test-install
test-install:
	pip3 --no-cache-dir install --upgrade \
		-i https://test.pypi.org/simple/ \
		${package_name}

.PHONY: build
build: pip-compile
	python3 setup.py sdist bdist_wheel

.PHONY: clean
clean:
	rm -rf $(subst -,_,${package_name}).egg-info dist build

.PHONY: pip-compile
pip-compile:
	pip-compile \
		--upgrade-package gumo-core \
		--upgrade-package gumo-datastore \
		--output-file requirements.txt \
		requirements.in
	pip3 install -r requirements.txt

.PHONY: test
test: build
	pip3 install dist/${package_name}*.tar.gz
	pytest -v tests/config.py tests

.PHONY: datastore-emulator
datastore-emulator:
	docker-compose up

.PHONY: server
server:
	PYTHONPATH=. python sample/server.py

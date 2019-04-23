package_name = gumo-pullqueue
sample_project_name = ${gcp_project_name:-gumo-pullqueue}

.PHONY: test
test:
	docker-compose run --rm server_test

.PHONY: fasttest
fasttest:
	docker-compose run --rm \
		-e PYTEST_OPTIONS="--failed-first" \
		server_test \
		make -f tools/Makefile fasttest

.PHONY: server
server:
	docker-compose run --rm --service-ports server

.PHONY: worker
worker:
	docker-compose run --rm --service-ports worker

.PHONY: build
build:
	docker-compose run --rm server make -f tools/Makefile build

.PHONY: fastbuild
fastbuild:
	docker-compose run --rm server make -f tools/Makefile fastbuild

.PHONY: test-deploy
test-deploy:
	docker-compose run --rm \
		-e TWINE_USERNAME=${TWINE_USERNAME} \
		-e TWINE_PASSWORD=${TWINE_PASSWORD} \
		server \
		make -f tools/Makefile test-deploy

.PHONY: deploy
deploy:
	docker-compose run --rm \
		-e TWINE_USERNAME=${TWINE_USERNAME} \
		-e TWINE_PASSWORD=${TWINE_PASSWORD} \
		server \
		make -f tools/Makefile deploy

.PHONY: sample-deploy
sample-deploy:
	gcloud app deploy sample/app.yaml --project=${sample_project_name}

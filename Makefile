.PHONY: build-all build-auth-service build-inventory-service build-notification-service build-order-service build-search-service build-user-service

IMAGE_REPO ?= werayco
TOPIC ?= inventory
PARTITIONS ?= 3
REPLICATION ?= 1

gen-secret:
	python -c "import secrets; print(secrets.token_urlsafe(64))"

auth:
	docker logs -f auth_service

payment:
	docker logs -f payment_service

inventory:
	docker logs -f inventory_service

notification:
	docker logs -f notification_service

order:
	docker logs -f order_service

search:
	docker logs -f search_service

db:
	docker logs -f cartord-pg

kf:
	docker logs -f cartord-kf

ai:
	docker logs -f ai_service

build-auth-service:
	docker build -t $(IMAGE_REPO)/auth-service:latest ./services/auth_service

build-inventory-service:
	docker build -t $(IMAGE_REPO)/inventory-service:latest ./services/inventory_service

build-notification-service:
	docker build -t $(IMAGE_REPO)/notification-service:latest ./services/notification_service

build-order-service:
	docker build -t $(IMAGE_REPO)/order-service:latest ./services/order_service

build-search-service:
	docker build -t $(IMAGE_REPO)/search-service:latest ./services/search_service

build-payment-service:
	docker build -t $(IMAGE_REPO)/user-service:latest ./services/payment_service

build-ai-service:
	docker build -t $(IMAGE_REPO)/ai-service:latest ./services/ai_service

build-all: build-auth-service build-inventory-service build-notification-service build-order-service build-search-service build-user-service build-payment-service

push-all:
	docker push $(IMAGE_REPO)/auth-service:latest
	docker push $(IMAGE_REPO)/inventory-service:latest
	docker push $(IMAGE_REPO)/notification-service:latest
	docker push $(IMAGE_REPO)/order-service:latest
	docker push $(IMAGE_REPO)/search-service:latest
	docker push $(IMAGE_REPO)/ai-service:latest
	docker push $(IMAGE_REPO)/payment-service:latest

init:
	python -m shared.init_scripts.debezium_setup
	python -m shared.init_scripts.seed
	python -m shared.init_scripts.create_topics

run:
	docker-compose -f shared/compose_files/docker-compose.yml up -d
	docker-compose -f shared/compose_files/services.docker-compose.yml up -d

services-all:
	docker-compose -f shared/compose_files/services.docker-compose.yml up --build -d
rebuild:
	docker-compose -f shared/compose_files/services.docker-compose.yml up --build $(SERVICE_NAME) -d
recreate-services:
	docker-compose -f shared/compose_files/services.docker-compose.yml up --force-recreate -d

stop:
	docker-compose -f shared/compose_files/docker-compose.yml down
	docker-compose -f shared/compose_files/services.docker-compose.yml down
stop-v:
	docker-compose -f shared/compose_files/docker-compose.yml down -v
	docker-compose -f shared/compose_files/services.docker-compose.yml down -v
	
git:
	git add .
	git commit -m "$(filter-out $@,$(MAKECMDGOALS))"
	git push
%:
	@:

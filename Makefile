.PHONY: build-all build-auth-service build-inventory-service build-notification-service build-order-service build-search-service build-user-service

IMAGE_REPO ?= ordering-system
TOPIC ?= inventory
PARTITIONS ?= 3
REPLICATION ?= 1

gen-secret:
	python -c "import secrets; print(secrets.token_urlsafe(64))"
auth:
	docker logs -f auth_service
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
build-auth-service:
	docker build -t $(IMAGE_REPO)-auth-service:latest ./services/auth-service

build-inventory-service:
	docker build -t $(IMAGE_REPO)-inventory-service:latest ./services/inventory-service

build-notification-service:
	docker build -t $(IMAGE_REPO)-notification-service:latest ./services/notification-service

build-order-service:
	docker build -t $(IMAGE_REPO)-order-service:latest ./services/order-service

build-search-service:
	docker build -t $(IMAGE_REPO)-search-service:latest ./services/search-service

build-user-service:
	docker build -t $(IMAGE_REPO)-user-service:latest ./services/user-service

build-all: build-auth-service build-inventory-service build-notification-service build-order-service build-search-service build-user-service

create-topics:
	python -m shared.init_scripts.create_topics --partitions $(PARTITIONS) --replication $(REPLICATION)

run:
	docker-compose -f shared/docker-compose.yml up -d
	docker-compose -f shared/services.docker-compose.yml up -d 
	python -m shared.init_scripts.create_topics --topic inventory --partitions 3 --replication 1
	python -m shared.init_scripts.create_topics --topic order --partitions 1 --replication 1
	python -m shared.init_scripts.seed

services-all:
	docker-compose -f shared/services.docker-compose.yml up --build -d

recreate-services:
	docker-compose -f shared/services.docker-compose.yml up --force-recreate -d

stop-all:
	docker-compose -f shared/docker-compose.yml down
	docker-compose -f shared/services.docker-compose.yml down

stop:
	docker-compose -f shared/services.docker-compose.yml down

stop-v:
	docker-compose -f shared/docker-compose.yml down -v
	docker-compose -f shared/services.docker-compose.yml down -v
git:
	git add .
	git commit -m "$(filter-out $@,$(MAKECMDGOALS))"
	git push
%:
	@:
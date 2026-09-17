.PHONY: build deploy clean all

IMAGES = pokemission-frontend pokemission-mission-service pokemission-subscriber-service

build:
	docker build -t pokemission-frontend:latest ./frontend
	docker build -t pokemission-mission-service:latest ./mission-service
	docker build -t pokemission-subscriber-service:latest ./subscriber-service

load: build
	@if command -v minikube &> /dev/null; then \
		for img in $(IMAGES); do \
			minikube image load $$img:latest; \
		done; \
	elif command -v kind &> /dev/null; then \
		for img in $(IMAGES); do \
			kind load docker-image $$img:latest; \
		done; \
	else \
		echo "Neither minikube nor kind found. Images built locally — ensure your cluster can access them."; \
	fi

deploy:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/rbac.yaml
	kubectl apply -f k8s/networkpolicy.yaml
	kubectl apply -f k8s/mission-service.yaml
	kubectl apply -f k8s/subscriber-service.yaml
	kubectl apply -f k8s/frontend.yaml
	kubectl apply -f k8s/ingress.yaml

all: load deploy

clean:
	kubectl delete namespace pokemission --ignore-not-found
	docker rmi $(addsuffix :latest,$(IMAGES)) 2>/dev/null; true

wait:
	@echo "Waiting for all pods to be ready..."
	@kubectl wait --namespace pokemission --for=condition=ready pod --all --timeout=120s

logs:
	kubectl logs -n pokemission -l app=mission-service --tail=50
	kubectl logs -n pokemission -l app=subscriber-service --tail=50

status:
	kubectl get all -n pokemission
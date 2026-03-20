#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🧪 Running Unit Tests & Generating Report...${NC}"

# Ensure venv is active or python3 is available
source .venv/bin/activate
if python3 generate_report.py; then
    echo -e "${GREEN}✅ Tests passed! Proceeding...${NC}"
else
    echo -e "${RED}❌ Tests failed! Aborting deployment.${NC}"
    exit 1
fi

# Run Security Scan
echo -e "${YELLOW}🛡️  Running Security Scan...${NC}"
if python3 scan_security.py; then
    echo -e "${GREEN}✅ Security scan complete!${NC}"
else
    echo -e "${RED}❌ Security scan failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🐳 Building Docker image...${NC}"
docker build -t chaimcp:latest -f k8s/Dockerfile .

echo -e "${GREEN}🚚 Loading image into higgs-cluster...${NC}"
kind load docker-image chaimcp:latest --name higgs-cluster

echo -e "${GREEN}🚀 Applying Kubernetes manifests...${NC}"
# Infrastructure (Idempotent)
kubectl apply -f k8s/infra/cert-manager.yaml
kubectl apply -f k8s/infra/ingress-nginx.yaml

echo -e "${YELLOW}⏳ Waiting for infrastructure pods to be ready...${NC}"
kubectl wait --namespace cert-manager --for=condition=ready pod --all --timeout=120s
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s

# Application
kubectl delete -f k8s/configmap.yaml --ignore-not-found || true
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/issuer.yaml
kubectl apply -f k8s/ingress.yaml

echo -e "${GREEN}🔄 Restarting deployment...${NC}"
kubectl rollout restart deployment chaimcp

echo -e "${GREEN}🎉 Deployment complete! View reports at testing.html${NC}"

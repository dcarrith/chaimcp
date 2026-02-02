#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
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

# Application
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/issuer.yaml
kubectl apply -f k8s/ingress.yaml

echo -e "${GREEN}🔄 Restarting deployment...${NC}"
kubectl rollout restart deployment chaimcp

echo -e "${GREEN}🎉 Deployment complete! View reports at testing.html${NC}"

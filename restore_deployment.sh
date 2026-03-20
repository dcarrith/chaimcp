#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Restoring ChaiMCP Deployment on higgs-cluster...${NC}"

# Check if higgs-cluster exists
if ! kind get clusters | grep -q "higgs-cluster"; then
    echo -e "${RED}❌ higgs-cluster not found! Please create it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ higgs-cluster found.${NC}"

# Install Cert Manager
echo -e "${BLUE}📦 Installing Cert Manager...${NC}"
kubectl apply -f k8s/infra/cert-manager.yaml

echo -e "${BLUE}⏳ Waiting for Cert Manager to be ready...${NC}"
kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=300s

# Install Ingress NGINX
echo -e "${BLUE}gate Installing Ingress NGINX...${NC}"
kubectl apply -f k8s/infra/ingress-nginx.yaml

echo -e "${BLUE}⏳ Waiting for Ingress NGINX to be ready...${NC}"
# Ingress NGINX controller can take a moment to create the deployment
sleep 5
kubectl wait --for=condition=Available deployment/ingress-nginx-controller -n ingress-nginx --timeout=300s

# Restore TLS Secret
echo -e "${BLUE}qh Restoring chaimcp-tls secret...${NC}"
if [ -f "chaimcp-tls.yaml" ]; then
    kubectl apply -f chaimcp-tls.yaml
    echo -e "${GREEN}✅ Secret restored.${NC}"
else
    echo -e "${RED}❌ chaimcp-tls.yaml not found! Skipping secret restoration.${NC}"
fi

# Run Deploy Local
echo -e "${BLUE}🚀 Running deploy_local.sh...${NC}"
./deploy_local.sh

echo -e "${GREEN}🎉 Restoration complete!${NC}"

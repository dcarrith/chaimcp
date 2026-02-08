#!/bin/bash
echo "Forwarding ports:"
echo "  - HTTP:  8080 -> 80"
echo "  - HTTPS: 4443 -> 443"
echo "Listening on all interfaces (0.0.0.0). Press Ctrl+C to stop."

kubectl port-forward --address 0.0.0.0 -n ingress-nginx service/ingress-nginx-controller 8080:80 4443:443

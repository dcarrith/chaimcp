import subprocess
import time
import pytest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_kubectl(cmd, check=True):
    """Helper to run kubectl commands."""
    full_cmd = f"kubectl {cmd}"
    logger.info(f"Running: {full_cmd}")
    result = subprocess.run(
        full_cmd, 
        shell=True, 
        capture_output=True, 
        text=True
    )
    if check and result.returncode != 0:
        raise Exception(f"Command failed: {result.stderr}")
    return result

@pytest.fixture(scope="module")
def setup_k8s_env():
    """Sets up a mock Chia namespace and service for testing."""
    logger.info("Setting up test environment...")
    
    # 1. Create chia namespace
    run_kubectl("create namespace chia", check=False)
    
    # 2. Deploy mock services in chia namespace
    # We use one pod listening on multiple ports for simplicity, or we could spawn 3 pods.
    # Netcat usually only listens on one port per process. Let's spawn a pod that sets up 3 listeners backgrounded.
    run_kubectl("run mock-chia --image=busybox --namespace=chia --restart=Never -- /bin/sh -c 'nc -lk -p 8555 -e echo \"Node RPC\" & nc -lk -p 9256 -e echo \"Wallet RPC\" & nc -lk -p 8562 -e echo \"DataLayer RPC\" & sleep 3600'")
    
    # Expose them (optional for pod-to-pod via IP, but good for service discovery if we used services)
    # For this test we target the pod IP or a service. Let's create a service for each or one service for all?
    # Network policy egress to namespace selector matches any pod in that namespace usually, unless podSelector is specified.
    # Our policy has:
    # - to: - namespaceSelector: {name: chia}
    # So it allows reaching ANY IP in that namespace on those ports.
    
    run_kubectl("expose pod mock-chia --port=8555 --target-port=8555 --name=chia-node --namespace=chia")
    run_kubectl("expose pod mock-chia --port=9256 --target-port=9256 --name=chia-wallet --namespace=chia")
    run_kubectl("expose pod mock-chia --port=8562 --target-port=8562 --name=chia-datalayer --namespace=chia")
    
    # 3. Wait for pod
    run_kubectl("wait --for=condition=Ready pod/mock-chia --namespace=chia --timeout=60s")
    
    yield
    
    # Teardown
    logger.info("Tearing down test environment...")
    run_kubectl("delete namespace chia", check=False)

def test_egress_allow_chia(setup_k8s_env):
    """Verify chaimcp (or simulated pod) can reach Chia RPC."""
    # We simulate the chaimcp app by running a pod with the same label in default ns
    run_kubectl("run test-client --image=busybox --labels=app=chaimcp --restart=Never -- /bin/sh -c 'sleep 3600'")
    run_kubectl("wait --for=condition=Ready pod/test-client --timeout=60s")
    
    try:
        # Try connection to Node RPC
        logger.info("Testing connectivity to connect to chia-node (8555)...")
        res = run_kubectl("exec test-client -- nc -vz chia-node.chia 8555", check=False)
        assert res.returncode == 0, f"Node RPC (8555) failed: {res.stderr}"
        
        # Try connection to Wallet RPC
        logger.info("Testing connectivity to connect to chia-wallet (9256)...")
        res = run_kubectl("exec test-client -- nc -vz chia-wallet.chia 9256", check=False)
        assert res.returncode == 0, f"Wallet RPC (9256) failed: {res.stderr}"

        # Try connection to DataLayer RPC
        logger.info("Testing connectivity to connect to chia-datalayer (8562)...")
        res = run_kubectl("exec test-client -- nc -vz chia-datalayer.chia 8562", check=False)
        assert res.returncode == 0, f"DataLayer RPC (8562) failed: {res.stderr}"
        
    finally:
        run_kubectl("delete pod test-client", check=False)

def test_egress_deny_check(setup_k8s_env):
    """Verify egress is blocked to other destinations (e.g. external network)."""
    run_kubectl("run test-client-deny --image=busybox --labels=app=chaimcp --restart=Never -- /bin/sh -c 'sleep 3600'")
    run_kubectl("wait --for=condition=Ready pod/test-client-deny --timeout=60s")
    
    try:
        # Try connect to google (IP directly to avoid DNS complexity, though DNS allowed)
        # 8.8.8.8 port 53 is DNS (allowed), so try port 80?
        # But our policy allows port 53 UDP/TCP to kube-system.
        # Let's try 1.1.1.1 port 80
        logger.info("Testing denied connectivity to 1.1.1.1:80...")
        res = run_kubectl("exec test-client-deny -- nc -vz -w 3 1.1.1.1 80", check=False)
        assert res.returncode != 0, "Connection succeeded but should have been blocked"
        
    finally:
        run_kubectl("delete pod test-client-deny", check=False)

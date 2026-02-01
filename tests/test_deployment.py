import unittest
import yaml
import os

class TestKubernetesManifests(unittest.TestCase):
    def setUp(self):
        self.k8s_dir = os.path.join(os.path.dirname(__file__), "..", "k8s")

    def load_yaml(self, filename):
        path = os.path.join(self.k8s_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return list(yaml.safe_load_all(f))

    def test_deployment_manifest(self):
        docs = self.load_yaml("deployment.yaml")
        self.assertIsNotNone(docs, "deployment.yaml not found")
        deployment = docs[0]
        self.assertEqual(deployment['kind'], 'Deployment')
        self.assertEqual(deployment['metadata']['name'], 'chaimcp')
        
        # Check container spec
        containers = deployment['spec']['template']['spec']['containers']
        self.assertTrue(len(containers) > 0)
        chaimcp = containers[0]
        self.assertEqual(chaimcp['image'], 'chaimcp:latest')
        self.assertEqual(chaimcp['ports'][0]['containerPort'], 4443)

    def test_service_manifest(self):
        docs = self.load_yaml("service.yaml")
        self.assertIsNotNone(docs, "service.yaml not found")
        service = docs[0]
        self.assertEqual(service['kind'], 'Service')
        self.assertEqual(service['metadata']['name'], 'chaimcp')
        self.assertEqual(service['spec']['ports'][0]['port'], 443)
        self.assertEqual(service['spec']['ports'][0]['targetPort'], 4443)

    def test_ingress_manifest(self):
        docs = self.load_yaml("ingress.yaml")
        self.assertIsNotNone(docs, "ingress.yaml not found")
        ingress = docs[0]
        self.assertEqual(ingress['kind'], 'Ingress')
        self.assertIn("cert-manager.io/cluster-issuer", ingress['metadata']['annotations'])
        self.assertEqual(ingress['spec']['tls'][0]['secretName'], 'chaimcp-tls')

    def test_issuer_manifest(self):
        docs = self.load_yaml("issuer.yaml")
        self.assertIsNotNone(docs, "issuer.yaml not found")
        issuer = docs[0]
        self.assertEqual(issuer['kind'], 'ClusterIssuer')
        self.assertEqual(issuer['spec']['acme']['privateKeySecretRef']['name'], 'letsencrypt-staging')

    def test_secret_manifest(self):
        docs = self.load_yaml("secret.yaml")
        self.assertIsNotNone(docs, "secret.yaml not found")
        secret = docs[0]
        self.assertEqual(secret['kind'], 'Secret')
        self.assertEqual(secret['metadata']['name'], 'chaimcp-secrets')
        self.assertIn('auth-token', secret['stringData'])

if __name__ == '__main__':
    unittest.main()

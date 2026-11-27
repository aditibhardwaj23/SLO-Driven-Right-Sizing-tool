from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class TestManifestWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifests = {}
        for folder in ("k8s", "monitoring"):
            for path in (ROOT / folder).glob("*.yaml"):
                cls.manifests[path] = yaml.safe_load(path.read_text(encoding="utf-8"))

        cls.by_kind = {
            manifest.get("kind"): manifest
            for manifest in cls.manifests.values()
            if isinstance(manifest, dict) and manifest.get("kind")
        }

    def test_all_yaml_files_parse(self):
        expected = list((ROOT / "k8s").glob("*.yaml")) + list(
            (ROOT / "monitoring").glob("*.yaml")
        )
        self.assertEqual(set(self.manifests), set(expected))

    def test_one_service_and_one_service_monitor(self):
        kinds = [manifest.get("kind") for manifest in self.manifests.values()]
        self.assertEqual(kinds.count("Service"), 1)
        self.assertEqual(kinds.count("ServiceMonitor"), 1)

    def test_service_selector_matches_deployment_pod_labels(self):
        deployment = self.by_kind["Deployment"]
        service = self.by_kind["Service"]
        pod_labels = deployment["spec"]["template"]["metadata"]["labels"]
        selector = service["spec"]["selector"]
        self.assertTrue(all(pod_labels.get(key) == value for key, value in selector.items()))

    def test_service_monitor_matches_service_and_named_port(self):
        service = self.by_kind["Service"]
        service_monitor = self.by_kind["ServiceMonitor"]
        service_labels = service["metadata"].get("labels", {})
        monitor_selector = service_monitor["spec"]["selector"]["matchLabels"]
        self.assertTrue(
            all(service_labels.get(key) == value for key, value in monitor_selector.items())
        )

        service_port_names = {
            port.get("name") for port in service["spec"]["ports"]
        }
        endpoint_ports = {
            endpoint["port"] for endpoint in service_monitor["spec"]["endpoints"]
        }
        self.assertTrue(endpoint_ports.issubset(service_port_names))
        self.assertEqual(service_monitor["spec"]["namespaceSelector"]["matchNames"], ["default"])

    def test_duplicate_kubernetes_directory_is_absent(self):
        self.assertFalse((ROOT / "kubernetes").exists())


if __name__ == "__main__":
    unittest.main()

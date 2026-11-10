"""Ejecutar desde la raiz: python -m unittest discover -s pruebas -v"""
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from cluster import Cluster
from common import call_json


class SpawnTechIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = Cluster(n_workers=2, base=18900).start()

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()

    def test_soporte_y_desarrollo(self):
        for category, queue in [("soporte", "soporte_tecnico"), ("desarrollo", "desarrollo_software")]:
            t = call_json(self.cluster.gateway_url + "/tickets", {"titulo": "Prueba", "categoria": category})
            self.assertEqual(t["cola"], queue)
            self.assertEqual(call_json(self.cluster.gateway_url + "/tickets/" + t["id"])["id"], t["id"])

    def test_observer(self):
        t = call_json(self.cluster.gateway_url + "/tickets", {"titulo": "Evento", "categoria": "soporte"})
        ev = call_json(self.cluster.observer_url + "/events")
        self.assertTrue(any(e["ticket_id"] == t["id"] for e in ev["eventos"]))

    def test_validacion(self):
        with self.assertRaises(HTTPError) as ctx:
            call_json(self.cluster.gateway_url + "/tickets", {"titulo": "", "categoria": "otro"})
        self.assertEqual(ctx.exception.code, 400)

    def test_round_robin(self):
        nodes = {call_json(self.cluster.gateway_url + "/tickets", {"titulo": f"t{i}", "categoria": "soporte"})["nodo"] for i in range(6)}
        self.assertEqual(nodes, {"nodo-A", "nodo-B"})


if __name__ == "__main__":
    unittest.main()

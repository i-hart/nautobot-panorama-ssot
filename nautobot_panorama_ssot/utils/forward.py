import requests
import time
from typing import Dict, Any, List, Optional


class ForwardClient:
    """
    Lightweight Forward Networks API client.

    Supports:
        - Snapshot triggering
        - NQE query execution
        - Blast-radius analysis
        - Change validation
    """

    def __init__(self, base_url: str, token: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )
        self.session.verify = verify_ssl

    # ============================================================
    # Snapshot Management
    # ============================================================

    def trigger_snapshot(self) -> Dict[str, Any]:
        resp = self.session.post(f"{self.base_url}/snapshots")
        resp.raise_for_status()
        return resp.json()

    def wait_for_snapshot(self, snapshot_id: str, timeout: int = 600):
        start = time.time()
        while time.time() - start < timeout:
            resp = self.session.get(f"{self.base_url}/snapshots/{snapshot_id}")
            resp.raise_for_status()
            status = resp.json().get("status")

            if status == "completed":
                return True
            if status == "failed":
                raise RuntimeError("Forward snapshot failed")

            time.sleep(10)

        raise TimeoutError("Forward snapshot timed out")

    # ============================================================
    # NQE Execution
    # ============================================================

    def run_nqe(self, query: str) -> List[Dict[str, Any]]:
        payload = {"query": query}
        resp = self.session.post(f"{self.base_url}/nqe", json=payload)
        resp.raise_for_status()
        return resp.json().get("results", [])

    # ============================================================
    # Blast Radius
    # ============================================================

    def blast_radius(self, object_name: str) -> List[Dict[str, Any]]:
        query = f"""
        flows
        | where policy_rule == "{object_name}"
        """
        return self.run_nqe(query)

    # ============================================================
    # Change Validation
    # ============================================================

    def validate_queries(self, queries: List[str]) -> bool:
        """
        Run validation queries.
        If any query returns unexpected results, fail.
        """
        for q in queries:
            results = self.run_nqe(q)
            if results:
                return False
        return True

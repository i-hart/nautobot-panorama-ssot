"""
Enterprise Panorama REST Client
Supports:
- Load operations
- CRUD operations
- Cross-scope resolution
- Batch execution
- Drift-only mode
- Rule movement
- Commit scoping
"""

import logging
import requests
import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class PanoramaClientError(Exception):
    pass


class PanoramaClient:

    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_version: str = "11.1",
        verify_ssl: bool = True,
        timeout: int = 30,
        max_workers: int = 10,
#        drift_only: bool = False,
#        simulation_mode: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_version = api_version
        self.max_workers = max_workers
#        self.drift_only = drift_only
#        self.simulation_mode = simulation_mode

        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update({
            "X-PAN-KEY": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        self._batch = []

    # ===========================================================
    # REST Core
    # ===========================================================

    def _url(self, path: str) -> str:
        return f"{self.base_url}/restapi/v{self.api_version}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs):

        url = self._url(path)

        response = self.session.request(
            method,
            url,
            timeout=self.timeout,
            **kwargs,
        )

        if response.status_code not in (200, 201):
            raise PanoramaClientError(
                f"{method} {url} -> {response.status_code}: {response.text}"
            )

        return response.json() if response.text else {}

    # ===========================================================
    # Batch Execution (20k+ safe)
    # ===========================================================

    def queue(self, func, *args, **kwargs):
        self._batch.append((func, args, kwargs))

    def execute_batch(self, chunk_size=100):

        while self._batch:
            chunk = self._batch[:chunk_size]
            self._batch = self._batch[chunk_size:]

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(func, *args, **kwargs)
                    for func, args, kwargs in chunk
                ]

                for f in futures:
                    f.result()

    # ===========================================================
    # Cross-Scope Resolution
    # ===========================================================

    def resolve_location(self, logical_group: str) -> Dict[str, str]:

        if logical_group == "shared":
            return {"location": "shared"}

        return {
            "location": "device-group",
            "device-group": logical_group,
        }

    def resolve_write_scope(self, object_type: str, model):
    
        exists = self.object_exists(object_type, model.name, model.logical_group)
    
        if exists == "shared":
            logger.info(f"{model.name} exists in shared — reusing shared scope")
            return {"location": "shared"}
    
        return self.resolve_location(model.logical_group)
    

    # ===========================================================
    # Reference Check
    # ===========================================================

    def is_object_in_use(self, model):

        # Placeholder — implement actual reference endpoint
        # Panorama REST: /Objects/<type>?reference=true
        return False

    def object_exists(self, object_type: str, name: str, logical_group: str) -> Optional[str]:
        """
        Returns location where object exists:
        - 'device-group'
        - 'shared'
        - None
        """
    
        # Check device-group first
        scope = self.resolve_location(logical_group)
    
        path = f"Objects/{object_type}/{name}"
    
        try:
            self._request("GET", path, params=scope)
            return "device-group"
        except Exception:
            pass
    
        # Check shared fallback
        try:
            self._request("GET", path, params={"location": "shared"})
            return "shared"
        except Exception:
            pass
    
        return None



    # ===========================================================
    # CRUD Example (Address)
    # ===========================================================

    def create_address(self, model, scope):

        path = "Objects/Addresses"
        payload = {
            "entry": {
                "@name": model.name,
                model.address_type: model.value,
                "description": model.description,
            }
        }

        self._request("POST", path, params=scope, json=payload)

    def update_address(self, model, diffs):

        scope = self.resolve_location(model.logical_group)
        path = f"Objects/Addresses/{model.name}"

        payload = {"entry": diffs}
        self._request("PUT", path, params=scope, json=payload)

    def delete_address(self, model):

        scope = self.resolve_location(model.logical_group)
        path = f"Objects/Addresses/{model.name}"
        self._request("DELETE", path, params=scope)

    # ===========================================================
    # Rule Ordering
    # ===========================================================

    def get_rule_order(self, logical_group, rulebase):

        rules = self.get_security_rules(logical_group, rulebase)
        return [r.get("@name") for r in rules]

    def move_rule_by_position(self, rule_name, logical_group, rulebase, position):

        path = f"Policies/Security{rulebase.capitalize()}Rules/{rule_name}:move"
        payload = {"where": "before", "destination": position}

        scope = self.resolve_location(logical_group)
        self._request("POST", path, params=scope, json=payload)

    # ===========================================================
    # Commit
    # ===========================================================

    def commit_device_group(self, device_group):

        response = self._request(
            "POST",
            "Commit",
            json={"device-group": device_group}
        )

        job_id = response.get("job")

        if job_id:
            self._wait_for_job(job_id)

        # Previous config
#        path = "Commit"
#        payload = {"device-group": device_group}

#        self._request("POST", path, json=payload)

    def commit_all(self, device_groups):
    
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.commit_device_group, dg)
                for dg in device_groups
            ]
    
            for f in futures:
                f.result()

    # ===========================================================
    # Commit - Rollback
    # ===========================================================

    def snapshot_config(self, device_group):
        return self._request("GET", f"Config/Snapshot/{device_group}")

    def rollback_config(self, snapshot):
        self._request("POST", "Config/Rollback", json=snapshot)


    # ===========================================================
    # Commit - Helpers
    # ===========================================================
    def _wait_for_job(self, job_id, timeout=600, interval=5):
    
        start = time.time()
    
        while time.time() - start < timeout:
    
            result = self._request("GET", f"Jobs/{job_id}")
    
            status = result.get("status")
    
            if status == "FIN":
                if result.get("result") != "OK":
                    raise PanoramaClientError(f"Commit failed: {result}")
                return
    
            time.sleep(interval)
    
        raise PanoramaClientError("Commit job timeout")


    def validate_device_group(self, device_group):
    
        response = self._request(
            "POST",
            "Commit/Validate",
            json={"device-group": device_group}
        )
    
        job_id = response.get("job")
    
        if job_id:
            return self._wait_for_validation(job_id)
    
        return False

    def _wait_for_validation(self, job_id, timeout=600, interval=5):
    
        import time
        start = time.time()
    
        while time.time() - start < timeout:
    
            result = self._request("GET", f"Jobs/{job_id}")
    
            if result.get("status") == "FIN":
                return result.get("result") == "OK"
    
            time.sleep(interval)
    
        raise PanoramaClientError("Validation job timeout")

    def get_rule_hit_counts(self, device_group):
    
        response = self._request(
            "GET",
            f"Policies/HitCount",
            params={"device-group": device_group}
        )
    
        return response.get("result", [])

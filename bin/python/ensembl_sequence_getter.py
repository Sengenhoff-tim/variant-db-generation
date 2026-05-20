import time
import requests
from typing import Dict, Iterable, List

SERVER = "https://rest.ensembl.org"
EXT = "/sequence/id"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

MAX_BATCH_SIZE = 50 # Ensembl limit
MAX_RETRIES = 4
BACKOFF_BASE = 1.0
BACKOFF_MAX = 30.0
TIMEOUT = 30.0

def _post_batch(ids_batch: List[str]) -> Dict[str, str]:
    payload = {"ids": ids_batch}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(SERVER + EXT, headers=HEADERS, json=payload, timeout=TIMEOUT)
        except requests.RequestException:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(min(BACKOFF_MAX, BACKOFF_BASE * (2 ** (attempt - 1))))
            continue

        if r.ok:
            try:
                return r.json()
            except ValueError:
                if attempt == MAX_RETRIES:
                    raise ValueError(f"Invalid JSON response for batch: {r.text}")
                time.sleep(min(BACKOFF_MAX, BACKOFF_BASE * (2 ** (attempt - 1))))
                continue

        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = float(retry_after)
                except ValueError:
                    wait = min(BACKOFF_MAX, BACKOFF_BASE * (2 ** (attempt - 1)))
            else:
                wait = min(BACKOFF_MAX, BACKOFF_BASE * (2 ** (attempt - 1)))
            time.sleep(wait)
            continue

        if 500 <= r.status_code < 600:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Server error {r.status_code} after {MAX_RETRIES} attempts: {r.text}")
            time.sleep(min(BACKOFF_MAX, BACKOFF_BASE * (2 ** (attempt - 1))))
            continue

        raise ValueError(f"HTTP error: {r.status_code} - {r.text}")

    raise RuntimeError("Exhausted retries")

def batches_of(ids: List[str], batch_size: int = MAX_BATCH_SIZE) -> Iterable[List[str]]:
    seen = set()
    unique = []
    for x in ids:
        if x not in seen:
            seen.add(x)
            unique.append(x)
    for i in range(0, len(unique), batch_size):
        yield unique[i : i + batch_size]

def get_sequences_by_batch(ids: List[str]) -> Iterable[Dict[str, str]]:
    """
    Generator: yields one dict (id -> sequence) per batch.
    Caller should process and discard each yielded dict before the next batch is fetched.
    """
    if not ids:
        return
    for batch in batches_of(ids):
        try:
            resp = _post_batch(batch)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve batch starting with {batch[:3]}: {e}")

        # Normalize response into {id: sequence}
        results: Dict[str, str] = {}
        if isinstance(resp, dict):
            for k, v in resp.items():
                if isinstance(v, dict):
                    seq = v.get("seq") or v.get("sequence")
                    if seq:
                        results[k] = seq
                elif isinstance(v, str):
                    results[k] = v
        elif isinstance(resp, list):
            for item in resp:
                if not isinstance(item, dict):
                    continue
                idx = item.get("id")
                seq = item.get("seq") or item.get("sequence")
                if idx and seq:
                    results[idx] = seq
        else:
            raise ValueError(f"Unexpected response shape: {type(resp).__name__}")

        yield results

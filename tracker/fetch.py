import gzip
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

RETRY_DELAY = 2


def raw_path(data_dir, chain, ref):
    return data_dir / "raw" / chain / ref.date.isoformat() / (ref.filename + ".gz")


def download(session, ref, dest, retries=3):
    if dest.exists():
        return False
    for attempt in range(1, retries + 1):
        try:
            r = session.get(ref.url, timeout=60)
            r.raise_for_status()
            break
        except Exception:
            if attempt == retries:
                raise
            time.sleep(RETRY_DELAY * attempt)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    tmp.write_bytes(gzip.compress(r.content))
    tmp.rename(dest)
    return True


def fetch(chain, data_dir, city=None, days=14, workers=4):
    result = {"downloaded": 0, "skipped": 0, "failed": 0}
    refs = []
    for day in chain.available_dates()[-days:]:
        day_refs = [r for r in chain.discover(day) if not city or r.store.city == city]
        print(f"{day}: {len(day_refs)} cjenika")
        refs.extend(day_refs)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = {pool.submit(download, chain.session, r, raw_path(data_dir, chain.name, r)): r
                for r in refs}
        for job in as_completed(jobs):
            try:
                result["downloaded" if job.result() else "skipped"] += 1
            except Exception as e:
                result["failed"] += 1
                print(f"Greška kod {jobs[job].filename}: {e}")
    return result

"""
Run the fetcher in a robust loop aligned to wall-clock minutes.

This script is designed to be run in a long-lived process (Docker, VPS, or cloud VM).
It will survive transient errors and keep fetching every minute.
"""
import time
import logging
from pathlib import Path
from ..services.fetcher import run_once


LOG = Path(__file__).resolve().parent.parent / "logs" / "fetcher.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

def align_to_next_minute():
    now = time.time()
    # seconds to sleep until next whole minute
    return 60 - (now % 60)


def main():
    logging.basicConfig(filename=str(LOG), level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("Starting Trade With Nilay fetcher loop")
    while True:
        try:
            run_once()
        except Exception as e:
            logging.exception("Unhandled error in fetch cycle: %s", e)
        # align to next minute boundary
        s = align_to_next_minute()
        time.sleep(s)


if __name__ == "__main__":
    main()
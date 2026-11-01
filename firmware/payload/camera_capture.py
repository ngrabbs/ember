"""Bounded single-worker adapter to the existing Koenig camera daemon."""
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import time
import urllib.request


class CameraCapture:
    def __init__(self, url):
        if url != 'http://127.0.0.1:8001':
            raise ValueError('capture URL must be http://127.0.0.1:8001')
        self.url = url
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.executor.shutdown(wait=True)

    def submit(self, packet):
        return self.executor.submit(self.capture, packet)

    def capture(self, packet):
        start = time.monotonic_ns()
        logging.info('CAPTURE_START origin=%u request=%u monotonic_ns=%u',
                     packet.origin, packet.request, start)
        # One total budget leaves room inside the IHU's five-second deadline.
        deadline = time.monotonic() + 3.8
        def request(path, post=False):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('capture deadline expired')
            req = urllib.request.Request(self.url + path, data=b'' if post else None)
            with self.opener.open(req, timeout=remaining) as response:
                return json.loads(response.read(65537))
        health = request('/healthz')
        settings = request('/settings')
        if (not health.get('ok') or health.get('timer_active') or
                health.get('focus_port') is not None or settings.get('burst_count') != 1):
            raise RuntimeError('camera daemon must be idle with timer off and burst_count=1')
        captures = request('/capture', post=True)['captures']
        if (len(captures) != 3 or {c['port'] for c in captures} != {0, 1, 2} or
                len({c['id'] for c in captures}) != 3 or any(c['bytes'] <= 0 for c in captures)):
            raise RuntimeError('camera daemon did not confirm three saved images')
        end = time.monotonic_ns()
        logging.info('CAPTURE_SAVED origin=%u request=%u monotonic_ns=%u elapsed_ms=%.3f images=%s',
                     packet.origin, packet.request, end, (end-start)/1e6,
                     json.dumps(captures, separators=(',', ':')))
        return captures

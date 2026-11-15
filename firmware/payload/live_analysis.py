"""Live-image adapter around the unchanged, replaceable detector pipeline."""
import json
import logging
from pathlib import Path
import subprocess
import select
import sys
import time
import uuid


class AnalysisWorker:
    """One preloaded, killable process. Only the single capture thread uses it."""
    def __init__(self, startup_timeout):
        self.process = None
        self.ensure_started(startup_timeout)

    def ensure_started(self, timeout):
        if self.process and self.process.poll() is None:
            return
        self.stop()
        self.process = subprocess.Popen(
            [sys.executable, '-u', str(Path(__file__).resolve()), '--worker'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            if self.read(timeout) != 'READY':
                raise RuntimeError('analysis worker startup')
        except BaseException:
            self.stop()
            raise

    def read(self, timeout):
        if timeout <= 0 or not select.select([self.process.stdout], [], [], timeout)[0]:
            raise TimeoutError('ANALYSIS_DEADLINE')
        line = self.process.stdout.readline().strip()
        if not line:
            raise RuntimeError('analysis worker exited')
        return line

    def run(self, case, timeout):
        try:
            self.process.stdin.write(str(case)+'\n')
            self.process.stdin.flush()
            if self.read(timeout) != 'DONE':
                raise RuntimeError('analysis worker protocol')
        except BaseException:
            self.stop()
            raise

    def stop(self):
        if self.process:
            if self.process.poll() is None:
                self.process.kill()
            self.process.wait()
            self.process.stdin.close()
            self.process.stdout.close()
            self.process = None


def analyze(captures, settings, packet, config, deadline, worker, metadata=None):
    case = Path(config['evidence_directory']) / f'{packet.origin}-{packet.request}-{uuid.uuid4().hex[:12]}'
    case.mkdir(parents=True, exist_ok=False)
    job = dict(captures=captures, settings=settings, origin=packet.origin,
               request=packet.request, config=config)
    if metadata:
        (case/'capture.json').write_text(json.dumps(dict(metadata, images=captures,
            origin=packet.origin, request=packet.request), indent=2)+'\n')
    try:
        (case/'job.json').write_text(json.dumps(job, indent=2)+'\n')
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError('ANALYSIS_DEADLINE')
        if worker:
            worker.run(case, remaining)
            record = json.loads((case/'result.json').read_text())
        else:
            record = dict(result='NO_FIRE', reason='STATIC_STUB', execution_mode='STATIC_STUB')
    except Exception as error:
        record = dict(result='UNKNOWN', reason='ANALYSIS_DEADLINE' if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)) else type(error).__name__+':'+str(error),
                      input_source='LIVE_CAMERA', camera_capture_performed=True,
                      origin=packet.origin, request=packet.request)
        from ember_detector.profiles import profile_name
        from hashlib import sha256
        profile = config['detector_profile']
        encoded = json.dumps(profile, sort_keys=True, separators=(',', ':'), allow_nan=False)
        record.update(profile=profile_name(profile), algorithm=profile['algorithm'],
                      input_format=profile.get('input_format', 'jpeg'),
                      config_sha256=sha256(encoded.encode()).hexdigest(),
                      calibration_sha256=profile['calibration_sha256'])
        (case/'result.json').write_text(json.dumps(record, indent=2)+'\n')
    logging.info('ANALYSIS_RESULT origin=%u request=%u result=%s reason=%s monotonic_ns=%u evidence=%s',
                 packet.origin, packet.request, record['result'], record['reason'],
                 time.monotonic_ns(), case/'result.json')
    if metadata:
        record.update(metadata, images=captures)
    # Internal handoff only: the responder adds the exact generated CAN reply.
    record['_evidence_path'] = str(case/'result.json')
    return record


def process(case):
    import cv2
    from ember_detector.pipeline import load_config, run
    cv2.setNumThreads(1)
    job = json.loads((case/'job.json').read_text())
    settings = job['settings']
    config = job['config']
    if isinstance(config, str):
        # Pre-0.6 evidence already has the source JPEGs in the case directory.
        config = dict(detector_profile=load_config(config), calibration=job['calibration'],
                      camera_image_directory=str(case.resolve()))
    channels = {}
    raw = config['detector_profile'].get('input_format') == 'raw_dng'
    for capture in job['captures']:
        port = str(capture['port'])
        controls = dict(settings['shared'], **settings['per_camera'].get(port, {}))
        if controls.get('AeEnable') is not False:
            raise ValueError('MANUAL_EXPOSURE_REQUIRED')
        name = capture['raw_id' if raw else 'id']
        if Path(name).name != name or name in ('', '.', '..'):
            raise ValueError('IMAGE_PATH')
        rotation = settings['rotations'].get(port, 0)
        if rotation not in (0, 180):
            raise ValueError('ROTATION')
        channels[port] = dict(path=name, port=int(port), bytes=capture['raw_bytes' if raw else 'bytes'],
                              wavelength_nm=settings['wavelengths'][port],
                              exposure_us=controls['ExposureTime'], rotation=rotation,
                              configured_controls=controls)
        if raw and config['detector_profile'].get('raw_matching') == 'paired_jpeg':
            channels[port]['matching_jpeg'] = dict(path=capture['id'], bytes=capture['bytes'])
    manifest = dict(fixtures=[dict(fixture_id='live', channels=channels)])
    path = case/'manifest.json'
    path.write_text(json.dumps(manifest, indent=2)+'\n')
    record, _ = run(path, 'live', config['detector_profile'], config['calibration'],
                    live_image_root=config['camera_image_directory'])
    record.update(input_source='LIVE_CAMERA', camera_capture_performed=True,
                  origin=job['origin'], request=job['request'])
    record['warnings'].append('GAIN_FROM_SETTINGS_NOT_SENSOR_METADATA' if raw
                              else 'EXPOSURE_AND_GAIN_FROM_SETTINGS_NOT_SENSOR_METADATA')
    (case/'result.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    if sys.argv[1] == '--worker':
        import cv2
        from ember_detector import pipeline
        cv2.setNumThreads(1)
        print('READY', flush=True)
        for line in sys.stdin:
            case = Path(line.strip())
            try:
                process(case)
            except Exception as error:
                (case/'result.json').write_text(json.dumps(dict(result='UNKNOWN',
                    reason=type(error).__name__+':'+str(error), input_source='LIVE_CAMERA',
                    camera_capture_performed=True), indent=2)+'\n')
            print('DONE', flush=True)
    else:
        process(Path(sys.argv[1]))

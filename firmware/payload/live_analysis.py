"""Live-image adapter around the unchanged, replaceable detector pipeline."""
import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.parse
import uuid


def analyze(captures, settings, packet, opener, url, config, deadline):
    root = Path(os.environ.get('EMBER_PAYLOAD_ANALYSIS_STORE', '/var/lib/ember-payload'))
    case = root / f'{packet.origin}-{packet.request}-{uuid.uuid4().hex[:12]}'
    case.mkdir(parents=True, exist_ok=False)
    job = dict(captures=captures, settings=settings, origin=packet.origin,
               request=packet.request, config=str(Path(config).resolve()),
               calibration=os.environ.get('EMBER_PAYLOAD_CALIBRATION',
                                          '/opt/ember-payload/correction_20261003.npz'))
    try:
        for capture in captures:
            name = capture['id']
            if Path(name).name != name:
                raise ValueError('IMAGE_PATH')
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise TimeoutError('ANALYSIS_DEADLINE')
            with opener.open(url+'/images/'+urllib.parse.quote(name, safe=''), timeout=remaining) as response:
                data = response.read(1000001)
            if len(data) != capture['bytes'] or len(data) > 1000000:
                raise ValueError('IMAGE_SIZE')
            (case/name).write_bytes(data)
        (case/'job.json').write_text(json.dumps(job, indent=2)+'\n')
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError('ANALYSIS_DEADLINE')
        # A process, rather than a cancellable thread, enforces the compute deadline.
        with (case/'analysis.log').open('w') as log:
            subprocess.run([sys.executable, str(Path(__file__).resolve()), str(case)],
                           stdout=log, stderr=subprocess.STDOUT, timeout=remaining, check=True)
        record = json.loads((case/'result.json').read_text())
    except Exception as error:
        record = dict(result='UNKNOWN', reason='ANALYSIS_DEADLINE' if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)) else type(error).__name__+':'+str(error),
                      input_source='LIVE_CAMERA', camera_capture_performed=True,
                      origin=packet.origin, request=packet.request)
        (case/'result.json').write_text(json.dumps(record, indent=2)+'\n')
    logging.info('ANALYSIS_RESULT origin=%u request=%u result=%s reason=%s monotonic_ns=%u evidence=%s',
                 packet.origin, packet.request, record['result'], record['reason'],
                 time.monotonic_ns(), case/'result.json')
    return record


def process(case):
    import cv2
    from ember_detector.pipeline import load_config, run
    cv2.setNumThreads(1)
    job = json.loads((case/'job.json').read_text())
    settings = job['settings']
    channels = {}
    originals = []
    for capture in job['captures']:
        port = str(capture['port'])
        controls = dict(settings['shared'], **settings['per_camera'].get(port, {}))
        if controls.get('AeEnable') is not False:
            raise ValueError('MANUAL_EXPOSURE_REQUIRED')
        source = case/capture['id']
        data = source.read_bytes()
        image = cv2.imread(str(source), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError('IMAGE_DECODE')
        rotation = settings['rotations'].get(port, 0)
        if rotation not in (0, 180):
            raise ValueError('ROTATION')
        # Gain maps are in sensor coordinates. Undo the daemon's output rotation
        # losslessly in a PNG before the existing calibration/registration stages.
        if rotation == 180:
            image = cv2.rotate(image, cv2.ROTATE_180)
        normalized = case/f'sensor-{port}.png'
        if not cv2.imwrite(str(normalized), image):
            raise OSError('PNG_WRITE')
        channels[port] = dict(path=normalized.name, port=int(port),
                              wavelength_nm=settings['wavelengths'][port],
                              width=image.shape[1], height=image.shape[0],
                              exposure_us=controls['ExposureTime'],
                              sha256=hashlib.sha256(normalized.read_bytes()).hexdigest())
        originals.append(dict(**capture, sha256=hashlib.sha256(data).hexdigest(),
                              output_rotation_undone=rotation, configured_controls=controls))
    manifest = dict(fixtures=[dict(fixture_id='live', channels=channels)])
    path = case/'manifest.json'
    path.write_text(json.dumps(manifest, indent=2)+'\n')
    record, _ = run(path, 'live', load_config(job['config']), job['calibration'])
    record.update(input_source='LIVE_CAMERA', camera_capture_performed=True,
                  origin=job['origin'], request=job['request'], original_inputs=originals)
    record['warnings'].append('EXPOSURE_AND_GAIN_FROM_SETTINGS_NOT_SENSOR_METADATA')
    (case/'result.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    process(Path(sys.argv[1]))

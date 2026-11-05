"""Shared fire-check settings and camera-daemon launcher."""
import json
import math
import os
from pathlib import Path
import sys


def load(path):
    config = json.loads(Path(path).read_text())
    expected = {
        'schema_version', 'camera_url', 'camera_image_directory', 'evidence_directory',
        'camera_request_timeout_s', 'fire_check_deadline_s', 'worker_startup_timeout_s',
        'calibration', 'detector_profile',
    }
    if set(config) != expected or config['schema_version'] != 1:
        raise ValueError('Unsupported fire-check configuration schema')
    if config['camera_url'] != 'http://127.0.0.1:8001':
        raise ValueError('Camera URL must address the local daemon')
    for key in ('camera_image_directory', 'evidence_directory', 'calibration'):
        if not Path(config[key]).is_absolute():
            raise ValueError(f'{key} must be an absolute path')
    for key in ('camera_request_timeout_s', 'fire_check_deadline_s', 'worker_startup_timeout_s'):
        value = config[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError(f'{key} must be a positive finite number')
    if not config['camera_request_timeout_s'] <= config['fire_check_deadline_s'] < 5:
        raise ValueError('Camera timeout must fit within the fire-check deadline and IHU five-second CAN window')
    return config


if __name__ == '__main__':
    config = load(sys.argv[1])
    os.environ['PAYLOAD_STORE'] = config['camera_image_directory']
    os.execv(sys.executable, [sys.executable, '-m', 'pi.daemon.main'])

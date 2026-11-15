"""Named development profiles and stable telemetry IDs."""
from copy import deepcopy
import json
from pathlib import Path

ALGORITHMS = {
    'guarded': 'spectral_guarded_v1',
    'baseline': 'spectral_excess_v1',
    'six-sigma': 'six_sigma_v1',
    'jacob-p': 'jacob_p_v1',
    'jacob-i': 'jacob_i_v1',
    'jacob-gross': 'jacob_gross_v1',
    'koenig': 'koenig_cutoff_v1',
    'jacob-i-native': 'jacob_i_native_v1',
}
PROFILE_IDS = {
    f'{fmt}-{name}': offset + index
    for fmt, offset in (('jpeg', 0), ('raw', 16))
    for index, name in enumerate(ALGORITHMS, 1)
}
DEFAULT = 'jpeg-guarded'


def profile_name(config):
    fmt = 'raw' if config.get('input_format') == 'raw_dng' else 'jpeg'
    name = next((key for key, value in ALGORITHMS.items() if value == config['algorithm']), None)
    return f'{fmt}-{name}' if name else None


def named_profile(name):
    if name not in PROFILE_IDS:
        raise ValueError(f'Unknown detector profile: {name}')
    fmt, method = name.split('-', 1)
    path = Path(__file__).resolve().parents[1] / 'config/fire-check.json'
    config = deepcopy(json.loads(path.read_text())['detector_profile'])
    config['algorithm'] = ALGORITHMS[method]
    if fmt == 'raw':
        config.update(input_format='raw_dng', exploratory_jpeg=False, dark_policy='dng_black_level')
        config['detector'].update(min_area_px=8, min_valid_fraction=.0043)
    if method in ('jacob-p', 'jacob-i'):
        config['registration']['mode'] = 'phase_translation'
    if method == 'baseline':
        config['detector'].pop('alignment_guard_px')
    if method == 'six-sigma':
        config['detector'] = dict(sigma=6.0, denominator_min=0., min_hits=None)
    elif method == 'jacob-p':
        config['detector'] = dict(continuum_min=4., percentile=99., score_threshold=None)
    elif method == 'jacob-i':
        config['detector'] = dict(source=None, background=None, score_threshold=None)
    elif method == 'jacob-i-native':
        config['detector'] = dict(source=None, background=None, score_threshold=None)
    elif method == 'jacob-gross':
        config['detector'] = dict(score_threshold=None)
    elif method == 'koenig':
        config['detector'] = dict(cutoff_dn=16, score_threshold=None)
    return config


def add_profile_arguments(parser):
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--profile', choices=PROFILE_IDS, help=f'Named profile (default {DEFAULT})')
    selection.add_argument('--config', type=Path, help='JSON detector profile')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Print an editable detector profile')
    parser.add_argument('profile', choices=PROFILE_IDS)
    print(json.dumps(named_profile(parser.parse_args().profile), indent=2))

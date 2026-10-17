# Selected October 14 development fixtures

`manifest.json` defines 107 retained triplets: 76 FIRE and 31 NO_FIRE, selected
from `payload_images_20261014.zip` after visual review. All 30 uncertain triplets
are excluded; their IDs and reasons remain in the manifest for traceability.
Labels are user-accepted visual assessments. NO_FIRE means no visible flame
identified, not independently established absence of fire.

The locally prepared `payload-fixtures-selected.zip` contains this manifest and
321 original, byte-verified JPEGs under `images/`. Extract both together when
provisioning fixtures. Raw image files are not committed. Every image is recorded
by SHA-256; the source archive hash is also recorded. No detector has been enabled
by creating this dataset.

The manifest's `channels` entries retain camera port/wavelength, image dimensions,
exposure when known and unknown gain/linearity. Calibration is a candidate until
compatibility is established. Capture `20261014_174904_481` has no bracket exposure
metadata and must not silently inherit another capture's settings.

This is a development selection that excludes difficult cases. Do not claim
held-out detection accuracy or generalize its results to the excluded cases.

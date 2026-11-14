# Payload firmware changelog

## 0.7.1

- Publish a new build identity for the FULL telemetry release. The existing
  read-only CAN identity service supplies the version and source commit.

## 0.7.0

- Record GPS status and fix age with fire check captures and report the tag
  with the payload check ID. Continue checks when a fix is unavailable or stale.

## 0.6.1

- Allow a ten-second capture and detector budget.

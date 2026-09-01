# Mechanical CAD

## Purpose

This directory is for mechanical design artifacts used in the current build:
assembly geometry, exported models, and fabrication-ready mechanical files.

## Source of Truth

- Primary CAD model: [Main 1U Assembly (Onshape)](https://cad.onshape.com/documents/f54077faa9eaef25e1f615dc/w/05a52062e76f7bd3695dddef/e/5aa71494ffb6396194e6798c?renderMode=0&uiState=684049080496457e60637a0b)
- Exported snapshots in this folder should be treated as release artifacts,
  not the authoring source.

## What Belongs Here

- `exports/`: STEP/STL/PDF exports tied to a design review or build revision
- `drawings/`: manufacturing drawings and mechanical interface drawings
- `assembly/`: neutral-format files for integration checks

## What Does Not Belong Here

- Early brainstorming links or speculative concepts
- Vendor discovery notes and unrelated references

Keep exploratory links in research documentation so this folder stays focused on
build-relevant mechanical deliverables.

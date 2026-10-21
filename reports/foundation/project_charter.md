# Foundation Project Charter

## Project

Project 23D — Renal CT 3D Segmentation

## Objective

Build and evaluate a reproducible 3D semantic segmentation system for kidneys,
renal tumors, and renal cysts in contrast-enhanced CT volumes.

## Intended use

Research benchmarking, volumetric delineation, and engineering demonstration.
The system is not a clinical diagnostic or treatment tool.

## Primary data

KiTS23 v0.1.4, using its labeled training allocation for development and a
case-disjoint internal test set.

## Core hypothesis

A properly configured 3D segmentation pipeline can produce reproducible kidney,
tumor, and cyst segmentations on a case-disjoint KiTS23 holdout. Under a budget of
about 15 GPU-hours (D-012), the official nnU-Net v2 trained for 100 epochs is
expected to segment the kidney well, with most of the remaining error in tumor and
cyst.

## Success definition

Success means:

- valid data and geometry contracts;
- no patient/case leakage;
- one reproducible nnU-Net v2 run with its budget recorded;
- KiTS-aligned primary metrics;
- per-case and failure analysis;
- documented limitations;
- reproducible local inference and evidence.

## Boundaries

The project will not claim diagnosis, malignancy classification, treatment benefit,
clinical validity, or performance on the official KiTS23 challenge test set.


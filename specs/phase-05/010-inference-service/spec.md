# SPEC 010 — Inference Service

- **Status:** DRAFT — BLOCKED until the Hugging Face account is 30 days old
- **Phase:** 5 — Public demo
- **Depends on:** SPEC 008, D-019

## 1. Purpose

Let a visitor run the model on their own anonymized scan through a Gradio Space on Hugging Face
ZeroGPU. The browser calls the Space directly.

## 2. Spike first

Nothing else in this spec is built until a small spike answers these questions. Record the answers
in `reports/release/zerogpu_spike.md`.

| Question | Pass condition |
|---|---|
| Does nnU-Net load and predict on ZeroGPU? | A validation case finishes without error |
| How long does a typical scan take? | Within one visitor's daily quota |
| Does nnU-Net's multiprocessing work inside a ZeroGPU call? | In-process prediction works |
| Whose quota is used when the browser calls the Space? | Known and documented |
| Which PyTorch and Python versions are needed? | A pinned, working set |

If a condition fails and can't be fixed by reducing the work per scan, move to fallback B: a
"run on your own scan" notebook that visitors open on their own free Kaggle or Colab account.
Record the outcome in `docs/decisions.md`.

## 3. Deliverables

| File | Content |
|---|---|
| `apps/space/app.py` | Gradio app with a `/segment` endpoint |
| `apps/space/requirements.txt` | Pinned dependencies |
| `apps/space/README.md` | Space configuration, license and disclaimer |
| `notebooks/05_run_on_your_scan.ipynb` | Fallback B |

## 4. Requirements

- `S010-REQ-001`: `/segment` takes one NIfTI file and returns a segmentation and a JSON summary.
- `S010-REQ-002`: The GPU duration requested grows with the scan's voxel count.
- `S010-REQ-003`: File size and voxel limits are enforced before any GPU time is used.
- `S010-REQ-004`: Uploads and results are deleted after processing, with Gradio's `delete_cache`.
- `S010-REQ-005`: Quota and queue errors return a clear message that the frontend can show.
- `S010-REQ-006`: The app has no database access and logs no scan content.
- `S010-REQ-007`: The Space shows "Research demo, not for clinical use".

## 5. Tests

- Input validation runs with no GPU.
- The duration function on small, typical and limit-sized scans.
- The API contract with a fake predictor.

## 6. Acceptance criteria

- [ ] The spike report is written and a decision is recorded.
- [ ] A validation case runs through the public Space from a browser.
- [ ] An oversized file is rejected with no GPU time used.
- [ ] Files are gone from the Space's storage after a run.
- [ ] Fallback B runs from a clean notebook.

## 7. Non-goals

- Paid hardware.
- DICOM upload.
- User accounts.
- Keeping any uploaded scan.

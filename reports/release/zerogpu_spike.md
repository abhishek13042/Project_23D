# ZeroGPU spike

**Status: not run.** On 2026-11-09 Hugging Face refused to create the Space: free accounts can no
longer host ZeroGPU or CPU Gradio Spaces. See D-023 in `docs/decisions.md`.

The app in `apps/space/` doubles as the spike: deploying it runs every check in the table. It was
built first so the spike is one deployment away. Locally, the real Gradio app was run with a fake
model and a stand-in for the `spaces` package. That covers the API, the checks that run before the
GPU and the deletion of uploads. It doesn't cover nnU-Net on ZeroGPU.

## How to run it

```bash
python scripts/space/package_space.py --out-dir build/space
```

Upload `build/space` to a new Space with ZeroGPU hardware, set the `MODEL_REPO` variable, then
upload one validation case through the page. Test cases are not used for timing (D-014).

## Results

| Question | Pass condition | Result |
|---|---|---|
| Does nnU-Net load and predict on ZeroGPU? | A validation case finishes without error | Not measured |
| How long does a typical scan take? | Within one visitor's daily quota | Not measured |
| Does nnU-Net's multiprocessing work inside a ZeroGPU call? | In-process prediction works | Not measured. The app uses in-process prediction only |
| Whose quota is used when the browser calls the Space? | Known and documented | Not measured |
| Which PyTorch and Python versions are needed? | A pinned, working set | Not measured |

## If it fails

Move to fallback B, [`notebooks/05_run_on_your_scan.ipynb`](../../notebooks/05_run_on_your_scan.ipynb),
and record the outcome in `docs/decisions.md`.

"""SPEC 010: the public Gradio app, with one endpoint: /segment.

The browser calls this Space directly, so scans never pass through the website. The app has no
database access. Uploads are removed after each run, and results within DELETE_AFTER seconds.
"""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
import service
import spaces  # must be imported before torch on ZeroGPU
from huggingface_hub import snapshot_download

from project3d.inference.predictor import InvalidInput, NnUNetModel

MODEL_REPO = os.environ.get("MODEL_REPO", "")
DELETE_AFTER = 900
QUEUE_SIZE = 8


def load_model() -> NnUNetModel:
    """Download the released model from Hugging Face and load it."""
    return NnUNetModel(snapshot_download(MODEL_REPO), service.OPTIONS)


MODEL = load_model() if MODEL_REPO else None


def duration(path: str, out_dir: str) -> int:
    """GPU seconds to ask ZeroGPU for, based on the scan size."""
    return service.gpu_seconds(path)


@spaces.GPU(duration=duration)
def run_on_gpu(path: str, out_dir: str) -> tuple[Path, dict]:
    """Segment the scan on the GPU that ZeroGPU lends for this call."""
    return service.segment_file(MODEL, path, out_dir)


def segment(path: str | None) -> tuple[str, dict]:
    """Check the upload with no GPU, then run the model. Returns the labels and a JSON summary."""
    if path is None:
        raise gr.Error(f"{service.INVALID}: Please choose a file.")
    try:
        service.check_upload(path)
        result, summary = run_on_gpu(path, str(Path(path).parent))  # in Gradio's cache, so it gets deleted
        return str(result), summary
    except (InvalidInput, gr.Error, RuntimeError, ValueError, OSError) as exc:
        raise gr.Error(service.error_text(exc), print_exception=False) from None
    finally:
        Path(path).unlink(missing_ok=True)


with gr.Blocks(title="KiTS23 kidney segmentation", delete_cache=(300, DELETE_AFTER)) as demo:
    gr.Markdown(f"# Kidney tumor CT segmentation\n\n**{service.DISCLAIMER}.**\n\n"
                "Upload an anonymized CT scan in NIfTI format. Do not upload data that can identify a "
                "person. The file is deleted after processing and nothing is stored.\n\n"
                "Model: nnU-Net v2 trained on KiTS23. Weights: CC BY-NC-SA 4.0, non-commercial use only.")
    scan = gr.File(label="CT scan (.nii or .nii.gz)", file_types=list(service.SUFFIXES), type="filepath")
    run = gr.Button("Segment", variant="primary")
    labels = gr.File(label="Segmentation: 1 kidney, 2 tumor, 3 cyst")
    summary = gr.JSON(label="Summary")
    run.click(segment, inputs=scan, outputs=[labels, summary], api_name="segment")

demo.queue(default_concurrency_limit=1, max_size=QUEUE_SIZE)

if __name__ == "__main__":
    demo.launch()

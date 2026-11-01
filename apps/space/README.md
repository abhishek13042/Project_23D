---
title: KiTS23 Kidney Segmentation
emoji: 🩻
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 6.31.0
python_version: "3.12"
app_file: app.py
suggested_hardware: zero-a10g
pinned: false
license: cc-by-nc-sa-4.0
short_description: Research demo of kidney and tumor CT segmentation
---

# KiTS23 kidney segmentation

> Research demo, not for clinical use.

Upload one anonymized CT scan in NIfTI format and get back a segmentation of kidney, tumor and
cyst. The model is an nnU-Net v2 network trained on KiTS23. It makes real errors, and it is weakest
on small tumors and on cysts.

- Do not upload data that can identify a person.
- Each upload is deleted after processing. Results are deleted within 15 minutes. Nothing is stored.
- GPU time counts against your daily ZeroGPU quota.

## API

`/segment` takes one `.nii` or `.nii.gz` file and returns the segmentation and a JSON summary with
the shape, spacing, region volumes and settings. Errors start with a code that a client can read:
`INVALID_INPUT`, `QUOTA_EXCEEDED`, `BUSY` or `FAILED`.

## Configuration

Set the Space variable `MODEL_REPO` to the Hugging Face model repository, for example
`your-name/kits23-nnunet`.

## License

The weights are derived from KiTS23 and are shared under CC BY-NC-SA 4.0: non-commercial use only.
Credit: KiTS23 (Heller et al., <https://github.com/neheller/kits23>) and nnU-Net v2 (Isensee et al.,
Nature Methods 2021).

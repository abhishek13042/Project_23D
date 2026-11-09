# data

Only the pinned file lists live here. The KiTS23 scans, labels and anything derived from them are
never committed: they are CC BY-NC-SA 4.0 (see [NOTICE.md](../NOTICE.md)) and `.gitignore` blocks them.

| File | What it is |
|---|---|
| `sources/kits23_v0.1.4_files.tsv` | Every image and label file of KiTS23 v0.1.4, with its size and SHA-256 |
| `sources/kits23_v0.1.4_image_urls.txt` | Download URL of each CT image |
| `sources/kits23_v0.1.4_segmentation_urls.txt` | Download URL of each label file |

[scripts/data/stage_kits23.py](../scripts/data/stage_kits23.py) downloads the files and checks each
one against this list.

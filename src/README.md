# src: the project3d library

The reusable code behind every script. It has no command-line entry points of its own, and it is
tested by the suite in [tests/](../tests/README.md).

| Package | What it does |
|---|---|
| `project3d/data/` | Finds KiTS23 files and checks them against the pinned checksums, measures each case, makes the train/validation/test split, builds the nnU-Net raw dataset and plans the preprocessing shards |
| `project3d/eval/` | Wraps the official KiTS23 evaluator, adds secondary metrics, applies the post-processing rule, computes bootstrap confidence intervals and builds the case analysis and figures |
| `project3d/inference/` | The predictor used by the command line, the benchmark and the live demo |
| `project3d/training/` | The nnU-Net trainer with the project's settings |

The scripts add `src/` to `sys.path` themselves, so they also run on Kaggle without installing
this package.

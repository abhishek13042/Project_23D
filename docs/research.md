# Research Foundation

## Core references

### U-Net

Ronneberger, Fischer, and Brox, “U-Net: Convolutional Networks for Biomedical
Image Segmentation,” MICCAI 2015. <https://arxiv.org/abs/1505.04597>

The encoder-decoder structure and skip connections establish the baseline design
pattern for precise localization with limited labeled data. We use the idea as the
conceptual basis for a compact 3D baseline, not as evidence that a 2D model is
sufficient.

### 3D U-Net

Çiçek et al., “3D U-Net: Learning Dense Volumetric Segmentation from Sparse
Annotation,” MICCAI 2016. <https://arxiv.org/abs/1606.06650>

The paper replaces 2D operations with 3D operations and addresses volumetric
context, memory, and augmentation. It directly justifies the baseline family for
CT volumes and the need to reason about patches and memory.

### V-Net

Milletari, Navab, and Ahmadi, “V-Net: Fully Convolutional Neural Networks for
Volumetric Medical Image Segmentation,” 3DV 2016.
<https://arxiv.org/abs/1606.04797>

V-Net demonstrates volumetric fully convolutional segmentation and a Dice-based
objective for foreground imbalance. We use it to justify overlap-aware loss and
class-imbalance analysis; we do not implement a separate V-Net unless an
experiment specifically needs it.

### nnU-Net

Isensee et al., “nnU-Net: a self-configuring method for deep learning-based
biomedical image segmentation,” Nature Methods 2021.
<https://doi.org/10.1038/s41592-020-01008-z>

nnU-Net shows that preprocessing, architecture configuration, training, and
postprocessing choices are strongly dataset-dependent. It is the project’s strong
reference because it provides a defensible comparison against a self-configuring
pipeline without creating an architecture zoo.

### Medical Segmentation Decathlon

Simpson et al., “A large annotated medical image dataset for the development and
evaluation of segmentation algorithms,” 2019.
<https://arxiv.org/abs/1902.09063>

This work motivates standardized multi-dataset evaluation and careful data/task
definitions. It informs the project’s dataset-card and leakage requirements but is
not the selected dataset.

## Dataset-specific references

### KiTS19 dataset paper

Heller et al., “The KiTS19 Challenge Data: 300 Kidney Tumor Cases with Clinical
Context, CT Semantic Segmentations, and Surgical Outcomes,” 2019.
<https://arxiv.org/abs/1904.00445>

It establishes the renal CT segmentation problem and the relationship between
kidney/tumor masks and downstream morphometry. It supports the clinical relevance
of segmentation while not providing clinical validation for this project.

### KiTS21 challenge report

Heller et al., “The KiTS21 Challenge: Automatic segmentation of kidneys, renal
tumors, and renal cysts in corticomedullary-phase CT,” 2023.
<https://arxiv.org/abs/2307.01984>

It documents the renal label definitions, external-test concerns, annotation
process, and hierarchical evaluation classes. It directly informs the KiTS23
label contract and the decision to report hierarchical regions rather than relying
only on a single averaged foreground score.

### KiTS23 official benchmark

Official homepage: <https://kits-challenge.org/kits23/>
Official repository: <https://github.com/neheller/kits23>

The official implementation defines the HECs:

- kidney and masses: labels `(1, 2, 3)`
- mass: labels `(2, 3)`
- tumor: label `(2,)`

It also defines the official surface-distance tolerance values used by its
evaluator. The project will reproduce these metrics and add complementary metrics
for analysis.

## Modern method decision

Swin UNETR was reviewed as a representative modern transformer-based 3D method:
Hatamizadeh et al., “Swin UNETR: Swin Transformers for Semantic Segmentation of
Brain Tumors in MRI Images,” 2022. <https://arxiv.org/abs/2201.01266>

It is not selected for the initial project because it introduces substantially
higher memory and training complexity without a project-specific hypothesis. It
may be considered only after the nnU-Net reference is understood.

## Architecture conclusion

The initial scientific comparison is:

Under the compute limit (D-012), the project trains one model: the official
nnU-Net v2, which *nnU-Net Revisited* (arXiv 2404.09556) shows to be a strong,
well-validated choice on KiTS23. A hand-built 3D U-Net comparison is future work.

V-Net, transformer models, and ensembles remain literature context rather than
unplanned implementation work.

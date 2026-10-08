# Research Review

## Methods and decisions

| Reference | Main contribution | Project use |
|---|---|---|
| Ronneberger et al., U-Net, 2015 | Encoder-decoder with skip connections and strong augmentation | Conceptual basis for compact baseline |
| Çiçek et al., 3D U-Net, 2016 | Extends U-Net operations to volumetric data | Direct baseline family; motivates patch/memory planning |
| Milletari et al., V-Net, 2016 | Volumetric FCN and Dice-oriented objective | Loss/class-imbalance reference; no separate implementation initially |
| Isensee et al., nnU-Net, 2021 | Self-configuring preprocessing, network, training, and postprocessing | Strong reference and reproducibility model |
| Simpson et al., MSD, 2019 | Standardized benchmark/data-card mindset | Dataset and evaluation discipline |
| Heller et al., KiTS19, 2019 | Renal CT segmentation dataset and clinical context | Renal task background and leakage caution |
| Heller et al., KiTS21, 2023 | Kidney/tumor/cyst labels, external testing, hierarchical evaluation | Label and metric basis for KiTS23 |
| Hatamizadeh et al., Swin UNETR, 2022 | Transformer encoder for 3D segmentation | Modern method reviewed but deferred due compute/scope |

## Architecture conclusion

The project will use a compact 3D U-Net baseline and a single strong nnU-Net-style

## Dataset-specific source links

- KiTS23 challenge: <https://kits-challenge.org/kits23/>
- KiTS23 repository: <https://github.com/neheller/kits23>
- KiTS23 paper: <https://arxiv.org/abs/2307.01984>
- KiTS19 paper: <https://arxiv.org/abs/1904.00445>
- nnU-Net paper: <https://doi.org/10.1038/s41592-020-01008-z>
- 3D U-Net paper: <https://arxiv.org/abs/1606.06650>
- V-Net paper: <https://arxiv.org/abs/1606.04797>

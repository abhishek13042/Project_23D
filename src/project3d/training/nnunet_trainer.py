"""nnU-Net trainer used for SPEC 003 (D-016).

Copied into the installed ``nnunetv2/training/nnUNetTrainer/variants`` folder on
Kaggle, because nnU-Net finds trainers by class name inside its own package. It
imports nothing from this project.
"""

import os

import torch
from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer


class nnUNetTrainer_100epochs_kaggle(nnUNetTrainer):
    """``nnUNetTrainer_100epochs`` with a checkpoint every 5 epochs instead of 50.

    Same schedule, model and augmentation. A Kaggle session ends after 12 hours,
    so at most 5 epochs are lost when a session stops and the next one resumes.
    Final validation resumes too: cases already predicted in ``validation/`` are
    skipped, and the summary still scores every file in that folder.
    """

    def __init__(self, plans: dict, configuration: str, fold: int, dataset_json: dict,
                 device: torch.device = torch.device("cuda")):
        super().__init__(plans, configuration, fold, dataset_json, device)
        self.num_epochs = 100
        self.save_every = 5
        self.skip_predicted = False

    def do_split(self) -> tuple[list[str], list[str]]:
        """nnU-Net's split, minus validation cases already predicted when resuming."""
        tr_keys, val_keys = super().do_split()
        if self.skip_predicted:
            folder = os.path.join(self.output_folder, "validation")
            val_keys = [k for k in val_keys if not os.path.exists(os.path.join(folder, f"{k}.nii.gz"))]
            print(f"final validation: {len(val_keys)} cases left to predict", flush=True)
        return tr_keys, val_keys

    def perform_actual_validation(self, save_probabilities: bool = False) -> None:
        """Final validation that skips cases a previous session already predicted."""
        self.skip_predicted = True
        super().perform_actual_validation(save_probabilities)

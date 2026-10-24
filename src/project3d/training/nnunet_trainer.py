"""nnU-Net trainer used for SPEC 003 (D-016).

Copied into the installed ``nnunetv2/training/nnUNetTrainer/variants`` folder on
Kaggle, because nnU-Net finds trainers by class name inside its own package. It
imports nothing from this project.
"""

import torch

from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer


class nnUNetTrainer_100epochs_kaggle(nnUNetTrainer):
    """``nnUNetTrainer_100epochs`` with a checkpoint every 5 epochs instead of 50.

    Same schedule, model and augmentation. A Kaggle session ends after 12 hours,
    so at most 5 epochs are lost when a session stops and the next one resumes.
    """

    def __init__(self, plans: dict, configuration: str, fold: int, dataset_json: dict,
                 device: torch.device = torch.device("cuda")):
        super().__init__(plans, configuration, fold, dataset_json, device)
        self.num_epochs = 100
        self.save_every = 5

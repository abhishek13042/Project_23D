export const DISCLAIMER = "Research demo, not for clinical use";

// Optional settings. Each page explains what is missing when one of them is unset.
export const GALLERY_BASE_URL = process.env.NEXT_PUBLIC_GALLERY_BASE_URL?.replace(/\/$/, "") || null;
export const SPACE_ID = process.env.NEXT_PUBLIC_SPACE_ID || null;
export const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL?.replace(/\/$/, "") || null;

export const NOTEBOOK_PATH = "notebooks/05_run_on_your_scan.ipynb";

export const LINKS = {
  kits23: "https://kits-challenge.org/kits23/",
  kits23Data: "https://github.com/neheller/kits23",
  nnunet: "https://github.com/MIC-DKFZ/nnUNet",
  niivue: "https://github.com/niivue/niivue",
  license: "https://creativecommons.org/licenses/by-nc-sa/4.0/",
};

// Colors follow the anatomy everywhere: viewer, legends and chips
export const LABELS = [
  { id: "kidney", name: "Kidney", rgb: [15, 165, 150] },
  { id: "tumor", name: "Tumor", rgb: [226, 86, 47] },
  { id: "cyst", name: "Cyst", rgb: [154, 124, 240] },
] as const;

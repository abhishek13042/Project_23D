// SPEC 010 and 011: read the answers of the /segment endpoint on the Hugging Face Space.

export type SpaceCode = "INVALID_INPUT" | "QUOTA_EXCEEDED" | "BUSY" | "FAILED";
export type SpaceFailure = { code: SpaceCode; message: string };

export type SpaceSummary = {
  voxel_count: number;
  volumes_ml: { kidney_ml: number; tumor_ml: number; cyst_ml: number };
};

const GENERIC = "The model could not process this scan.";
const CODED = /(INVALID_INPUT|QUOTA_EXCEEDED|BUSY|FAILED):\s*(.+)/;

// The Gradio client rejects with either an Error or a status object, both holding a message
export function parseSpaceError(error: unknown): SpaceFailure {
  const text =
    typeof error === "string" ? error : ((error as { message?: unknown } | null)?.message ?? "");
  const match = typeof text === "string" ? text.match(CODED) : null;
  if (match) return { code: match[1] as SpaceCode, message: match[2] };
  return { code: "FAILED", message: GENERIC };
}

export function checkFileName(name: string): string | null {
  const lower = name.toLowerCase();
  return lower.endsWith(".nii") || lower.endsWith(".nii.gz") ? null : "Please choose a NIfTI file (.nii or .nii.gz).";
}

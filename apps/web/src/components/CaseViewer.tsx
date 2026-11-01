import { Viewer } from "./Viewer";
import { GALLERY_BASE_URL } from "@/lib/site";

const NOT_PUBLISHED = "The sample scans are not published yet, so the 3D view is unavailable. The scores on this site are real.";

export function CaseViewer({ id, sizeMb, autoLoad }: { id: string; sizeMb: number; autoLoad?: boolean }) {
  const file = (name: string) => ({ url: `${GALLERY_BASE_URL}/${id}/${name}`, name });
  return (
    <Viewer
      ct={file("ct.nii.gz")}
      layers={[
        { id: "model", label: "Model", ...file("pred.nii.gz") },
        { id: "expert", label: "Expert", ...file("gt.nii.gz") },
      ]}
      sizeMb={sizeMb}
      autoLoad={autoLoad}
      blocked={GALLERY_BASE_URL ? undefined : NOT_PUBLISHED}
    />
  );
}

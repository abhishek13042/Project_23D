import generated from "@/data/results.json";

export const results = generated;
export type GalleryCase = (typeof generated.gallery)[number];

export const GROUPS = [
  { id: "worst", title: "Where it failed", note: "The lowest scores on the test set. They come first on purpose." },
  { id: "best", title: "Where it worked best", note: "The highest scores on the test set." },
  { id: "median", title: "A typical result", note: "Scores close to the middle of the test set." },
  { id: "small_tumor", title: "Small tumors", note: "The hardest size group: a few wrong voxels change the score a lot." },
  { id: "with_cyst", title: "Scans with cysts", note: "The model rarely tells cysts apart from tumors." },
] as const;

export const groupOf = (id: string) => GROUPS.find((group) => group.id === id) ?? GROUPS[2];
export const casesIn = (group: string) => results.gallery.filter((c) => c.group === group);
export const findCase = (id: string) => results.gallery.find((c) => c.case_id === id);

export const speedOf = (setting: string) => results.speed.find((s) => s.setting === setting);

export const score = (value: number) => value.toFixed(3);
export const interval = (s: { low: number; high: number }) => `${s.low.toFixed(3)}–${s.high.toFixed(3)}`;
export const ml = (value: number) => (value < 10 ? value.toFixed(1) : value.toFixed(0));
export const caseLabel = (id: string) => id.replace("case_", "Case ");

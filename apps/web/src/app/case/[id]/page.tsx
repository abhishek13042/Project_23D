import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CaseViewer } from "@/components/CaseViewer";
import { caseLabel, findCase, groupOf, ml, results, score } from "@/lib/results";

type Props = { params: Promise<{ id: string }> };

export const dynamicParams = false;

export function generateStaticParams() {
  return results.gallery.map((item) => ({ id: item.case_id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: caseLabel((await params).id) };
}

const REGIONS = [
  ["kidney_and_mass", "Kidney + masses"],
  ["mass", "Masses"],
  ["tumor", "Tumor"],
  ["kidney", "Kidney"],
  ["cyst", "Cyst"],
] as const;

const VOLUMES = [
  ["kidney", "Kidney"],
  ["tumor", "Tumor"],
  ["cyst", "Cyst"],
] as const;

export default async function CasePage({ params }: Props) {
  const item = findCase((await params).id);
  if (!item) notFound();
  const group = groupOf(item.group);

  return (
    <>
      <p><Link href="/gallery">Back to the gallery</Link></p>
      <h1 style={{ marginTop: 12 }}>{caseLabel(item.case_id)}</h1>
      <p className="lede">
        {group.title}. Mean Dice <span className="num">{score(item.scores.mean_dice)}</span>, mean surface Dice{" "}
        <span className="num">{score(item.scores.mean_sd)}</span>.
      </p>
      <div className="case-grid">
        <CaseViewer id={item.case_id} sizeMb={item.size_mb} autoLoad />
        <aside>
          <div>
            <h2>Dice by region</h2>
            <table className="ledger">
              <tbody>
                {REGIONS.map(([id, label]) => (
                  <tr key={id}>
                    <th scope="row">{label}</th>
                    <td className="num">{id === "cyst" && item.volumes_ml.cyst.reference === 0 ? "no cyst" : score(item.regions[id].dice)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <h2>Volume, mL</h2>
            <table className="ledger">
              <thead>
                <tr>
                  <th scope="col">Region</th>
                  <th scope="col">Expert</th>
                  <th scope="col">Model</th>
                </tr>
              </thead>
              <tbody>
                {VOLUMES.map(([id, label]) => (
                  <tr key={id}>
                    <th scope="row">{label}</th>
                    <td className="num">{ml(item.volumes_ml[id].reference)}</td>
                    <td className="num">{ml(item.volumes_ml[id].predicted)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </aside>
      </div>
    </>
  );
}

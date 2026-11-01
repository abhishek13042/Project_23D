import Link from "next/link";
import { CaseViewer } from "@/components/CaseViewer";
import { Ruler, RulerScale } from "@/components/Ruler";
import { caseLabel, casesIn, interval, results, score } from "@/lib/results";

export default function Home() {
  const example = casesIn("median")[0];
  const best = casesIn("best")[0];
  const worst = casesIn("worst")[0];
  const kidney = results.regions.find((region) => region.id === "kidney_and_mass")!;
  const tumor = results.regions.find((region) => region.id === "tumor")!;
  const rows = [
    { label: "Mean Dice", stat: results.meanDice },
    { label: "Mean surface Dice", stat: results.surfaceDice },
    { label: "Kidney + masses, Dice", stat: kidney.dice },
    { label: "Tumor, Dice", stat: tumor.dice },
  ];

  return (
    <>
      <div className="hero">
        <div>
          <h1>Outlining kidneys and tumors in 3D CT, failures included.</h1>
          <p className="lede">
            A segmentation model trained on public KiTS23 scans and scored once on {results.nCases} scans it had
            never seen.
          </p>
          <div className="actions">
            <Link className="button" href="/gallery">Explore the cases</Link>
            <Link href="/results">Read the results</Link>
          </div>
        </div>
        <CaseViewer id={example.case_id} sizeMb={example.size_mb} />
      </div>

      <section>
        <h2>How well it works</h2>
        <p className="soft" style={{ marginTop: 10 }}>
          Dice measures overlap with an expert&apos;s outline: 0 is none, 1 is perfect. Good on whole kidneys,
          weak on tumors, and not clinical grade.
        </p>
        <table className="ledger">
          <thead>
            <tr>
              <th scope="col">Internal test set, {results.nCases} scans</th>
              <th scope="col">Mean</th>
              <th scope="col">95% interval</th>
              <th scope="col" className="ruler-cell"><RulerScale /></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                <td className="num">{score(row.stat.mean)}</td>
                <td className="num">{interval(row.stat)}</td>
                <td className="ruler-cell">
                  <Ruler value={row.stat.mean} low={row.stat.low} high={row.stat.high} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Its best scan and its worst</h2>
        <div className="pair">
          <Link href={`/case/${best.case_id}`}>
            <h3>{caseLabel(best.case_id)}: the best</h3>
            <span className="figure">{score(best.scores.mean_dice)}</span>
            <p>Almost the same outline as the expert.</p>
          </Link>
          <Link href={`/case/${worst.case_id}`}>
            <h3>{caseLabel(worst.case_id)}: the worst</h3>
            <span className="figure">{score(worst.scores.mean_dice)}</span>
            <p>The model outlined the wrong structure, so nothing overlaps the expert.</p>
          </Link>
        </div>
      </section>

      <section className="prose">
        <h2>How it was built</h2>
        <p>
          The scans come from the KiTS23 challenge. They were split by case into training, validation and test
          sets before any training started, and the test set stayed locked until the final run.
        </p>
        <p>
          The model is the official nnU-Net v2 3D network, trained on a free Kaggle GPU. One clean-up step was
          chosen on validation data only. <Link href="/about">Read the method</Link>.
        </p>
      </section>
    </>
  );
}

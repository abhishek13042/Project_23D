import Link from "next/link";
import { CaseViewer } from "@/components/CaseViewer";
import { Ruler, RulerScale } from "@/components/Ruler";
import { ScoreTerrain, TerrainKey } from "@/components/ScoreTerrain";
import { TerrainReadout } from "@/components/TerrainReadout";
import { caseLabel, casesIn, findCase, interval, ml, results, score } from "@/lib/results";

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
  const scans = [...results.scans].sort((a, b) => a.mean_dice - b.mean_dice);
  const lowest = scans[0];
  const labelled = [worst.case_id, casesIn("worst")[1].case_id, best.case_id, example.case_id];

  return (
    <>
      <div className="survey">
        <div className="frame">
          <div className="survey-title">
            <h1>Outlining kidneys and tumors in 3D CT, failures included.</h1>
            <div>
              <p className="lede">
                A segmentation model trained on public KiTS23 scans and scored once on {results.nCases} scans it had
                never seen.
              </p>
              <div className="actions">
                <Link className="button" href="/gallery">Explore the cases</Link>
                <Link href="/results">Read the results</Link>
              </div>
            </div>
          </div>
          <TerrainReadout
            start={{
              id: lowest.case_id,
              score: score(lowest.mean_dice),
              tumor: String(lowest.tumor_ml),
              kidney: String(lowest.kidney_ml),
              open: Boolean(findCase(lowest.case_id)),
            }}
            side={<TerrainKey />}
          >
            <ScoreTerrain id="wide" className="terrain-wide" width={1000} height={440} labelled={labelled} leftLabels={[labelled[1]]} survey />
            <ScoreTerrain id="tall" className="terrain-tall" width={358} height={420} labelled={labelled.slice(0, 1)} dot={6} survey />
          </TerrainReadout>
          <div className="survey-axes">
            <p>Across: tumor size, small to large. Up: kidney size. Both from the expert&apos;s outline, on log scales.</p>
            <p>Each spot is a real scan. The contours between them are smoothed.</p>
          </div>
        </div>
      </div>

      <div className="frame page">
        <section>
          <h2>How well it works</h2>
          <p className="note">
            Dice measures overlap with an expert&apos;s outline: 0 is none, 1 is perfect. Good on whole kidneys,
            weak on tumors, and not clinical grade.
          </p>
          <table className="ledger ruled">
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
          <details className="all-scans">
            <summary>All {results.nCases} scans, lowest first</summary>
            <div className="scroll" tabIndex={0} role="region" aria-label={`All ${results.nCases} test scans`}>
              <table className="ledger">
                <thead>
                  <tr>
                    <th scope="col">Scan</th>
                    <th scope="col">Mean Dice</th>
                    <th scope="col">Tumor</th>
                    <th scope="col">Kidney</th>
                  </tr>
                </thead>
                <tbody>
                  {scans.map((scan) => (
                    <tr key={scan.case_id}>
                      <th scope="row">
                        {findCase(scan.case_id) ? (
                          <Link href={`/case/${scan.case_id}`}>{caseLabel(scan.case_id)}</Link>
                        ) : (
                          caseLabel(scan.case_id)
                        )}
                      </th>
                      <td className="num">{score(scan.mean_dice)}</td>
                      <td className="num">{ml(scan.tumor_ml)} mL</td>
                      <td className="num">{ml(scan.kidney_ml)} mL</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
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
      </div>

      <div className="open-scan">
        <div className="frame open-scan-grid">
          <div>
            <h2>Open a typical scan</h2>
            <p className="note">
              {caseLabel(example.case_id)} scores {score(example.scores.mean_dice)}, close to the middle of the test
              set. Switch between the model&apos;s outline and the expert&apos;s.
            </p>
          </div>
          <CaseViewer id={example.case_id} sizeMb={example.size_mb} />
        </div>
      </div>

      <div className="frame page prose">
        <h2>How it was built</h2>
        <p>
          The scans come from the KiTS23 challenge. They were split by case into training, validation and test
          sets before any training started, and the test set stayed locked until the final run.
        </p>
        <p>
          The model is the official nnU-Net v2 3D network, trained on a free Kaggle GPU. One clean-up step was
          chosen on validation data only. <Link href="/about">Read the method</Link>.
        </p>
      </div>
    </>
  );
}

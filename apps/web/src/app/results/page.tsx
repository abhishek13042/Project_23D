import type { Metadata } from "next";
import Link from "next/link";
import { Ruler, RulerScale } from "@/components/Ruler";
import { RunStats } from "@/components/RunStats";
import { caseLabel, findCase, interval, results, score } from "@/lib/results";

export const metadata: Metadata = { title: "Results" };

type Row = { label: string; n?: number; mean: number; low: number; high: number };

function Table({ title, rows }: { title: string; rows: Row[] }) {
  return (
    <table className="ledger">
      <thead>
        <tr>
          <th scope="col">{title}</th>
          <th scope="col">Mean</th>
          <th scope="col">95% interval</th>
          <th scope="col" className="ruler-cell"><RulerScale /></th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.label}>
            <th scope="row">
              {row.label}
              {row.n !== undefined && <span className="soft"> ({row.n})</span>}
            </th>
            <td className="num">{score(row.mean)}</td>
            <td className="num">{interval(row)}</td>
            <td className="ruler-cell"><Ruler value={row.mean} low={row.low} high={row.high} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const SIZES: Record<string, string> = { small: "Small tumors", medium: "Medium tumors", large: "Large tumors" };

export default function Results() {
  const { meanDice, surfaceDice, raw, validation, regions, bySize, byCyst, volumeCorrelation, worstCases } = results;
  const cyst = regions.find((region) => region.id === "cyst")!;
  const hasCyst = byCyst.find((row) => row.group === "True")!;
  const small = bySize.find((row) => row.group === "small")!;
  const large = bySize.find((row) => row.group === "large")!;

  return (
    <>
      <h1>Results</h1>
      <p className="lede">
        On {results.nCases} locked test scans the mean Dice is <span className="num">{score(meanDice.mean)}</span>{" "}
        and the mean surface Dice is <span className="num">{score(surfaceDice.mean)}</span>. Half of the scans
        score above <span className="num">{score(meanDice.median)}</span>, so a few bad scans pull the mean down.
      </p>

      <section>
        <h2>By region</h2>
        <Table
          title="Region"
          rows={regions.map((region) => ({ label: region.label, ...region.dice }))}
        />
      </section>

      <section>
        <h2>By tumor size</h2>
        <p className="soft" style={{ marginTop: 10 }}>
          Tumor Dice. Scans per group in brackets. Larger tumors score higher (Spearman rho{" "}
          <span className="num">{volumeCorrelation.rho.toFixed(2)}</span>).
        </p>
        <Table title="Group" rows={bySize.map((row) => ({ ...row, label: SIZES[row.group] }))} />
      </section>

      <section>
        <h2>Effect of the clean-up step</h2>
        <p className="soft" style={{ marginTop: 10 }}>
          The raw model marks false regions away from the kidneys. Keeping the two largest regions removes most
          of them. The step was chosen on validation data, before the test run.
        </p>
        <Table
          title="Mean Dice"
          rows={[
            { label: "Test, raw output", ...raw.meanDice },
            { label: "Test, after clean-up", ...meanDice },
            { label: "Validation, after clean-up", ...validation.meanDice },
          ]}
        />
      </section>

      <section className="prose">
        <h2>What worked and what failed</h2>
        <ul>
          <li>
            Kidneys and masses are found well: <span className="num">{score(regions[0].dice.mean)}</span> Dice for
            the two together.
          </li>
          <li>
            Small tumors are weak: <span className="num">{score(small.mean)}</span> tumor Dice, against{" "}
            <span className="num">{score(large.mean)}</span> for large ones.
          </li>
          <li>
            Cysts are effectively not separated from tumors. Median cyst Dice is{" "}
            <span className="num">{score(cyst.dice.median)}</span> across the {hasCyst.n} test scans that have cysts.
          </li>
          <li>
            The clean-up step fails when a false region is bigger than a real kidney. In the worst scan every
            region scored zero.
          </li>
        </ul>
      </section>

      <section>
        <h2>The lowest scores</h2>
        <table className="ledger">
          <thead>
            <tr>
              <th scope="col">Scan</th>
              <th scope="col">Mean Dice</th>
              <th scope="col">Tumor Dice</th>
              <th scope="col">Tumor size</th>
            </tr>
          </thead>
          <tbody>
            {worstCases.map((item) => (
              <tr key={item.case_id}>
                <th scope="row">
                  {findCase(item.case_id) ? (
                    <Link href={`/case/${item.case_id}`}>{caseLabel(item.case_id)}</Link>
                  ) : (
                    caseLabel(item.case_id)
                  )}
                </th>
                <td className="num">{score(item.mean_dice)}</td>
                <td className="num">{score(item.tumor_dice)}</td>
                <td>{item.size_bin}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="prose">
        <h2>How to read these numbers</h2>
        <p>
          The intervals are bootstrap 95% confidence intervals over scans. Group results are descriptive, because
          the groups are small. Scans with and without cysts differ little in mean Dice (
          <span className="num">{score(hasCyst.mean)}</span> and{" "}
          <span className="num">{score(byCyst.find((row) => row.group === "False")!.mean)}</span>).
        </p>
        <p>
          The test scans come from the public KiTS23 training cases, not the hidden challenge test set, so these
          scores can&apos;t be compared with the leaderboard. Training used one fold and 100 epochs, far less than
          the full nnU-Net recipe. This is a research result, not clinical performance.
        </p>
      </section>

      <RunStats />
    </>
  );
}

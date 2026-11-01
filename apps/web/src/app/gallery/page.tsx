import type { Metadata } from "next";
import Link from "next/link";
import { Ruler, RulerScale } from "@/components/Ruler";
import { caseLabel, casesIn, GROUPS, score } from "@/lib/results";

export const metadata: Metadata = { title: "Gallery" };

export default function Gallery() {
  return (
    <>
      <h1>Gallery</h1>
      <p className="lede">
        Eleven test scans, chosen by rule rather than to flatter the model. Open any scan and compare its
        outline with the expert&apos;s.
      </p>
      <div className="after">
        {GROUPS.map((group) => (
          <section className="group" key={group.id}>
            <h2>{group.title}</h2>
            <p>{group.note}</p>
            <table className="ledger">
              <thead>
                <tr>
                  <th scope="col">Scan</th>
                  <th scope="col">Mean Dice</th>
                  <th scope="col">Tumor Dice</th>
                  <th scope="col" className="ruler-cell"><RulerScale /></th>
                  <th scope="col">Download</th>
                </tr>
              </thead>
              <tbody>
                {casesIn(group.id).map((item) => (
                  <tr key={item.case_id}>
                    <th scope="row">
                      <Link href={`/case/${item.case_id}`}>{caseLabel(item.case_id)}</Link>
                    </th>
                    <td className="num">{score(item.scores.mean_dice)}</td>
                    <td className="num">{score(item.scores.tumor_dice_official)}</td>
                    <td className="ruler-cell"><Ruler value={item.scores.mean_dice} /></td>
                    <td className="num">{item.size_mb.toFixed(1)} MB</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ))}
      </div>
    </>
  );
}

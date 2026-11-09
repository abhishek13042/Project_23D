import type { Metadata } from "next";
import { PageHead } from "@/components/PageHead";
import { TryForm } from "@/components/TryForm";
import { NOTEBOOK_PATH, REPO_URL, SPACE_ID } from "@/lib/site";

export const metadata: Metadata = { title: "Try a scan" };

function Fallback() {
  const notebook = REPO_URL ? (
    <a href={`${REPO_URL}/blob/main/${NOTEBOOK_PATH}`}>the run-it-yourself notebook</a>
  ) : (
    <>
      the run-it-yourself notebook, <code>{NOTEBOOK_PATH}</code>
    </>
  );
  return (
    <>
      <h2>Live upload is unavailable right now</h2>
      <p>
        You can still run the model on your own scan with {notebook} on a free Kaggle GPU. The gallery and results
        work as usual.
      </p>
    </>
  );
}

export default function Try() {
  return (
    <>
      <PageHead title="Try a scan">
        <p className="lede">Run the model on your own abdominal CT, in NIfTI format.</p>
      </PageHead>
      <div className="frame page">
      <div className="warning">
        <p>
          <strong>Do not upload scans that can identify a person.</strong> Remove names, dates and hospital details
          first. If you are not sure the scan is anonymized, don&apos;t upload it.
        </p>
        <p>
          The result is for research only and must not guide any medical decision.{" "}
          {SPACE_ID
            ? "Your file goes directly to the model on Hugging Face and is deleted after processing."
            : "If you use the notebook, your scan stays in your own notebook session and never reaches this website."}
        </p>
      </div>
      <TryForm fallback={<Fallback />} />
      </div>
    </>
  );
}

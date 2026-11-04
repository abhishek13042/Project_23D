"use client";

import { useEffect, useMemo, useState } from "react";
import { Viewer } from "./Viewer";
import { ml } from "@/lib/results";
import { LABELS, SPACE_ID } from "@/lib/site";
import { checkFileName, parseSpaceError, type SpaceFailure, type SpaceSummary } from "@/lib/space";

type Result = { url: string; summary: SpaceSummary };
const RESULT_NAME = "segmentation.nii.gz";

async function segment(spaceId: string, file: File): Promise<Result> {
  const { Client, handle_file } = await import("@gradio/client");
  const client = await Client.connect(spaceId);
  const { data } = await client.predict("/segment", [handle_file(file)]);
  const [labels, summary] = data as [{ url: string }, SpaceSummary];
  return { url: labels.url, summary };
}

async function recordRun(status: "success" | "failed", seconds: number, summary?: SpaceSummary) {
  const volumes = summary?.volumes_ml;
  const body = {
    status,
    durationSeconds: Math.round(seconds * 10) / 10,
    voxelCount: summary?.voxel_count ?? null,
    kidneyMl: volumes?.kidney_ml ?? null,
    tumorMl: volumes?.tumor_ml ?? null,
    cystMl: volumes?.cyst_ml ?? null,
  };
  // Statistics are optional: a database failure must never disturb the visitor's result
  try {
    const response = await fetch("/api/runs", { method: "POST", body: JSON.stringify(body) });
    return response.ok ? ((await response.json()).id as string) : null;
  } catch {
    return null;
  }
}

function Feedback({ runId }: { runId: string | null }) {
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [state, setState] = useState<"open" | "sent" | "failed">("open");

  async function send() {
    const response = await fetch("/api/feedback", {
      method: "POST",
      body: JSON.stringify({ runId, rating, comment: comment.trim() || null }),
    }).catch(() => null);
    setState(response?.ok ? "sent" : "failed");
  }

  if (state === "sent") return <p className="status">Thank you.</p>;
  return (
    <div className="after">
      <h2>Was this useful?</h2>
      <div className="stars" role="group" aria-label="Rating from 1 to 5">
        {[1, 2, 3, 4, 5].map((value) => (
          <button key={value} type="button" aria-pressed={rating === value} onClick={() => setRating(value)}>
            {value}
          </button>
        ))}
      </div>
      <label className="field">
        <span>Comment (optional). Please don&apos;t include personal details.</span>
        <textarea rows={3} maxLength={1000} value={comment} onChange={(event) => setComment(event.target.value)} />
      </label>
      <div className="actions">
        <button className="button" type="button" disabled={rating === null} onClick={send}>
          Send feedback
        </button>
      </div>
      {state === "failed" && <p className="status bad">Feedback could not be saved right now.</p>}
    </div>
  );
}

export function TryForm({ fallback }: { fallback: React.ReactNode }) {
  const [agreed, setAgreed] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [running, setRunning] = useState(false);
  const [problem, setProblem] = useState<SpaceFailure | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const localUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);

  useEffect(() => () => void (localUrl && URL.revokeObjectURL(localUrl)), [localUrl]);

  function choose(chosen: File | null) {
    setResult(null);
    setRunId(null);
    const invalid = chosen && checkFileName(chosen.name);
    setProblem(invalid ? { code: "INVALID_INPUT", message: invalid } : null);
    setFile(invalid ? null : chosen);
  }

  async function run() {
    if (!file || !SPACE_ID) return;
    setRunning(true);
    setProblem(null);
    setResult(null);
    const started = performance.now();
    const seconds = () => (performance.now() - started) / 1000;
    try {
      const output = await segment(SPACE_ID, file);
      setResult(output);
      setRunId(await recordRun("success", seconds(), output.summary));
    } catch (error) {
      setProblem(parseSpaceError(error));
      await recordRun("failed", seconds());
    } finally {
      setRunning(false);
    }
  }

  if (!SPACE_ID) return <div className="after prose">{fallback}</div>;

  return (
    <>
      <label className="check">
        <input type="checkbox" checked={agreed} onChange={(event) => setAgreed(event.target.checked)} />
        <span>My scan is anonymized and I have the right to use it.</span>
      </label>
      <label className={`drop ${!agreed || running ? "locked" : ""}`}>
        <span className="drop-title">{file ? file.name : "Drop a CT scan here, or choose a file"}</span>
        <span className="drop-hint">{agreed ? "A .nii or .nii.gz file" : "Tick the box above first"}</span>
        <input
          type="file"
          accept=".nii,.gz"
          disabled={!agreed || running}
          onChange={(event) => choose(event.target.files?.[0] ?? null)}
        />
      </label>
      <div className="actions">
        <button className="button" type="button" disabled={!agreed || !file || running} onClick={run}>
          {running ? "Running the model…" : "Run the model"}
        </button>
      </div>
      <div aria-live="polite">
        {running && <p className="status">This can take a few minutes, and a sleeping Space has to wake first.</p>}
        {problem && (
          <div className="status bad">
            <p>{problem.message}</p>
            {problem.code !== "INVALID_INPUT" && <div className="prose soft">{fallback}</div>}
          </div>
        )}
      </div>
      {result && localUrl && file && (
        <div className="after">
          <h2>Your result</h2>
          <div className="case-grid">
            <Viewer
              key={result.url}
              ct={{ url: localUrl, name: file.name }}
              layers={[{ id: "model", label: "Model", url: result.url, name: RESULT_NAME }]}
              autoLoad
            />
            <aside>
              <table className="ledger">
                <caption>Measured volume</caption>
                <tbody>
                  {LABELS.map((label) => (
                    <tr key={label.id}>
                      <th scope="row">{label.name}</th>
                      <td className="num">{ml(result.summary.volumes_ml[`${label.id}_ml`])} mL</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="status">
                <a href={result.url} download={RESULT_NAME}>Download the segmentation</a>
              </p>
            </aside>
          </div>
          <Feedback runId={runId} />
        </div>
      )}
    </>
  );
}

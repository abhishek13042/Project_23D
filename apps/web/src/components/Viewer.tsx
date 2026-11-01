"use client";

import { useEffect, useRef, useState } from "react";
import { DISCLAIMER, LABELS } from "@/lib/site";

export type Volume = { url: string; name: string };
export type Layer = Volume & { id: string; label: string };

type Phase = "idle" | "loading" | "ready" | "failed" | "no-webgl";
type Controller = { setLayer: (index: number, opacity: number) => void; stop: () => void };

const CT_WINDOW = { cal_min: -160, cal_max: 240 }; // soft-tissue window, in Hounsfield units
const NONE = "none";

const labelMap = () => ({
  R: [0, ...LABELS.map((label) => label.rgb[0])],
  G: [0, ...LABELS.map((label) => label.rgb[1])],
  B: [0, ...LABELS.map((label) => label.rgb[2])],
  A: [0, 255, 255, 255],
  I: [0, 1, 2, 3],
  labels: ["Background", ...LABELS.map((label) => label.name)],
});

function hasWebGL2() {
  return Boolean(document.createElement("canvas").getContext("webgl2"));
}

async function startViewer(canvas: HTMLCanvasElement, ct: Volume, layers: Layer[]): Promise<Controller> {
  const { Niivue, SHOW_RENDER, SLICE_TYPE } = await import("@niivue/niivue");
  const nv = new Niivue({
    backColor: [0.055, 0.063, 0.071, 1],
    crosshairColor: [1, 1, 1, 0.45],
    multiplanarShowRender: SHOW_RENDER.ALWAYS,
    logLevel: "error",
    loadingText: "",
  });
  await nv.attachToCanvas(canvas);
  nv.setSliceType(SLICE_TYPE.MULTIPLANAR);
  await nv.loadVolumes([
    { url: ct.url, name: ct.name, colormap: "gray", ...CT_WINDOW, trustCalMinMax: true },
    ...layers.map((layer) => ({ url: layer.url, name: layer.name, opacity: 0 })),
  ]);
  nv.volumes.slice(1).forEach((volume) => volume.setColormapLabel(labelMap()));
  nv.updateGLVolume();
  return {
    setLayer: (index, opacity) => nv.setOpacity(index, opacity),
    stop: () => {
      nv.cleanup();
      nv.gl?.getExtension("WEBGL_lose_context")?.loseContext();
    },
  };
}

export function Viewer({
  ct,
  layers,
  sizeMb,
  autoLoad = false,
  blocked,
}: {
  ct: Volume;
  layers: Layer[];
  sizeMb?: number;
  autoLoad?: boolean;
  blocked?: string;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const viewer = useRef<Controller | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [shown, setShown] = useState(layers[0]?.id ?? NONE);
  const [opacity, setOpacity] = useState(0.6);
  const canStart = !blocked;

  useEffect(() => {
    if (autoLoad && canStart) setPhase("loading");
  }, [autoLoad, canStart]);

  useEffect(() => {
    if (phase !== "loading" || !canvas.current) return;
    if (!hasWebGL2()) {
      setPhase("no-webgl");
      return;
    }
    let cancelled = false;
    // A timer, so React's strict-mode rehearsal never attaches two viewers to one canvas
    const element = canvas.current;
    const timer = setTimeout(() => {
      startViewer(element, ct, layers).then(
        (controller) => {
          if (cancelled) controller.stop();
          else {
            viewer.current = controller;
            setPhase("ready");
          }
        },
        () => !cancelled && setPhase("failed"),
      );
    });
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // `layers` is rebuilt on each render; the URLs below identify the scan
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase === "loading", ct.url]);

  useEffect(() => {
    if (phase !== "ready") return;
    layers.forEach((layer, index) => viewer.current?.setLayer(index + 1, layer.id === shown ? opacity : 0));
  }, [phase, shown, opacity, layers]);

  useEffect(
    () => () => {
      viewer.current?.stop();
      viewer.current = null;
    },
    [],
  );

  const message = blocked
    ? blocked
    : phase === "no-webgl"
      ? "This browser has no WebGL2, which the 3D viewer needs. Try a recent version of Chrome, Edge, Firefox or Safari."
      : phase === "failed"
        ? "The scan files could not be loaded. Check your connection and reload the page."
        : null;

  return (
    <figure className="viewer" style={{ margin: 0 }}>
      <div className="viewer-stage">
        <canvas ref={canvas} aria-label="3D CT viewer. Drag to move through the scan." />
        {phase !== "ready" && (
          <div className="viewer-blank">
            <span className="axis-mark" style={{ top: 10, left: 12 }}>A</span>
            <span className="axis-mark" style={{ top: 10, right: 12 }}>L</span>
            <span className="axis-mark" style={{ bottom: 10, left: 12 }}>S</span>
            <span className="axis-mark" style={{ bottom: 10, right: 12 }}>3D</span>
            <div>
              {message ? (
                <p role="status" style={{ marginTop: 0 }}>{message}</p>
              ) : phase === "loading" ? (
                <p role="status" style={{ marginTop: 0 }}>Loading the scan…</p>
              ) : (
                <>
                  <button className="button" type="button" onClick={() => setPhase("loading")}>
                    Open this scan in 3D
                  </button>
                  {sizeMb !== undefined && <p>{sizeMb.toFixed(1)} MB download. Works best on a laptop.</p>}
                </>
              )}
            </div>
          </div>
        )}
      </div>
      <figcaption>
        <div className="viewer-bar">
          <div className="seg" role="group" aria-label="Choose the overlay">
            {[...layers, { id: NONE, label: "CT only" }].map((layer) => (
              <button key={layer.id} type="button" aria-pressed={shown === layer.id} onClick={() => setShown(layer.id)}>
                {layer.label}
              </button>
            ))}
          </div>
          <label className="opacity">
            Opacity
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.05"
              value={opacity}
              onChange={(event) => setOpacity(Number(event.target.value))}
            />
          </label>
          <ul className="legend">
            {LABELS.map((label) => (
              <li key={label.id}>
                <span className="swatch" style={{ background: `rgb(${label.rgb.join(",")})` }} />
                {label.name}
              </li>
            ))}
          </ul>
        </div>
        <div className="viewer-note">{DISCLAIMER}. Drag to move through the slices; drag the 3D panel to rotate it.</div>
      </figcaption>
    </figure>
  );
}

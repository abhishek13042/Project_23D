# Phase 5: Public demo

Turns the trained model into something people can use, for $0 (D-018, D-019). The design and its
limits are in [docs/deployment.md](../../docs/deployment.md).

## Order of work

```text
008 Model release ──► 009 Gallery ──► 011 Web app ──► 012 Launch
       │                                   ▲
       └──────────► 010 Inference service ─┘  (optional for launch)
```

SPEC 010 may finish after launch. The site can launch with the gallery alone and add live upload
later, because the Hugging Face account must be 30 days old before a ZeroGPU Space can be hosted.

## Entry conditions

- SPEC 004 has run and `reports/evaluation/results.md` has real numbers.
- SPEC 009 needs the case analysis from SPEC 005 to choose its cases.

## Rules for every spec in this phase

- Nothing here touches the locked test set for tuning. Test cases appear only as the
  already-scored gallery samples (D-014, D-018).
- Published metrics are read from `reports/`, never typed by hand.
- Weights and sample cases carry CC BY-NC-SA 4.0 and attribution.
- No secrets in git.

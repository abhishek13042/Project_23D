# Deployment plan: a public demo for $0

Nothing here is deployed yet. This is the design that [phase 5](../specs/phase-05/README.md)
builds. The reasoning is in D-019.

Free tiers change often, so every limit below is dated. All were checked on **2026-10-30** and rechecked unchanged on **2026-11-04**.
Check them again before relying on them.

## The stack

```text
Browser
  │  loads pages from              Vercel (Next.js + NiiVue viewer)
  │  reads sample cases from       Hugging Face dataset (public files)
  │  uploads a scan directly to    Hugging Face ZeroGPU Space (Gradio + nnU-Net)
  │
  └─ after a run, the app stores   Neon Postgres (run statistics only, no images)
```

| Part | Service | Why this one |
|---|---|---|
| Website and small API | Vercel Hobby | Free, deploys from git |
| 3D viewer | NiiVue, in the browser | Renders on the visitor's GPU, so it costs no server |
| Sample cases and weights | Hugging Face repos | Free for public repos |
| Live inference | Hugging Face ZeroGPU Space | The only free GPU found with no card |
| Database | Neon Postgres Free, only with live upload | Not used at launch (D-023) |

## Three levels, so it never goes fully dark

1. **Gallery (always on).** Pre-computed results for about 10 test cases, shown in the 3D viewer.
   It needs no backend, so it keeps working if everything else runs out.
2. **Live upload (when ZeroGPU is available).** A visitor uploads a NIfTI scan and gets a
   segmentation back.
3. **Run it yourself (fallback).** If ZeroGPU can't run the model, the site links to a free
   notebook that does the same job on the visitor's own Kaggle or Colab account.

## Verified free limits

| Service | Limit on 2026-11-04 | What it means here |
|---|---|---|
| Vercel Hobby | Non-commercial personal use; 100 GB data transfer, 1M function calls, 4 CPU-hours per month; functions up to 300 s | Fine for a portfolio. Scans must not pass through Vercel functions |
| Neon Free | 100 CU-hours per project, 1 GB storage, scale to zero after 5 min, no card | Fine for small rows of statistics |
| HF ZeroGPU hosting | Refused for this free account on 2026-11-09: needs PRO or a community grant (D-023) | No live upload at launch |
| HF ZeroGPU visitors | Daily GPU time: 2 min without an account, 5 min with a free account, 40 min with PRO | One scan may use most of a visitor's quota. Measured in SPEC 010 |
| HF public repos | Best-effort free storage; large datasets need a dataset card | Fine for weights and about 10 cropped cases |
| GitHub Actions | Free on public repos | CI only |

Vercel functions accept request and response bodies of at most 4.5 MB (checked 2026-11-04). The
design avoids this limit, because uploads go directly to the Space.

## Options rejected

| Option | Why not |
|---|---|
| HF Docker or CPU Space | Docs now say Gradio and Docker Spaces on compute need a paid plan to create; ZeroGPU is the exception |
| GitHub Actions as the inference server | Its terms forbid use unrelated to the software project's build, test and release, or as a serverless backend |
| Render free | 512 MB RAM; nnU-Net needs several GB |
| Oracle Cloud, Google Cloud Run, Koyeb, Railway | Each needs a card on file, so they aren't safely $0 |

## What only the owner can do

These need the owner's own accounts. Tokens go into each service's secret settings and never
into chat or git.

| Task | When |
|---|---|
| **Create and verify a Hugging Face account** | **Now**: the 30-day clock starts at account creation |
| Create an empty public GitHub repository and send its URL | Before SPEC 012, ideally now |
| Create a Vercel account (Neon only with live upload) | At SPEC 011 |

## Rules for the public demo

- Show "Research demo, not for clinical use" on every page that shows a result.
- Accept anonymized NIfTI files only, and warn people not to upload identifiable data.
- Delete uploads after processing. Store no images and no IP addresses.
- Credit KiTS23 and nnU-Net, and keep the CC BY-NC-SA 4.0 terms on weights and sample cases.
- No ads, no payments: the Vercel plan and the data license both require non-commercial use.

## Sources

- Hugging Face: [Spaces overview](https://huggingface.co/docs/hub/spaces-overview), [ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu), [storage limits](https://huggingface.co/docs/hub/storage-limits), [forum report on CPU Spaces](https://discuss.huggingface.co/t/official-community-complaint-revert-free-cpu-basic-spaces-and-remove-anti-developer-sdk-restrictions/177703)
- [Neon pricing](https://neon.com/pricing)
- Vercel: [Hobby plan](https://vercel.com/docs/plans/hobby), [function limits](https://vercel.com/docs/functions/limitations)
- GitHub: [hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions), [terms for additional products](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features)

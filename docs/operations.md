# Operations

How to launch the public demo, keep it healthy and react when a free limit runs out. The design and
the limits are in [deployment.md](deployment.md).

Tokens go only into each service's secret settings. Never paste one into a file, a commit or a chat.

## First launch

Do these in order. Each one leaves the site working.

1. **GitHub.** Create an empty public repository, then run:

   ```bash
   python scripts/ops/scan_history.py
   git remote add origin <repository URL>
   git push -u origin main
   ```

2. **Hugging Face model and gallery.** Done 2026-11-09: [model](https://huggingface.co/abhishek1402/project23d-kits23-nnunet), [gallery](https://huggingface.co/datasets/abhishek1402/project23d-kits23-gallery). Create public repositories for the model and the sample
   cases. Upload the `model_package` output of `kits23-release` and the `gallery` output of
   `kits23-gallery`. Keep the model card and dataset card that come with them, because they state
   the license. Then replace the model repository's `README.md` with
   [model_card.md](../reports/release/model_card.md). It adds the benchmark, which didn't exist when
   the package was built, so `checksums.json` lists the older README. The other files are unchanged.
3. **Neon.** Create a project without a card and run `apps/web/src/db/schema.sql` once in its SQL
   editor.
4. **Vercel.** Import the repository on the Hobby plan with these settings:
   - Root directory: `apps/web`.
   - Include files outside the root directory: **on**. The build reads `../../reports`.
   - Environment variables: see [apps/web/.env.example](../apps/web/.env.example).
     `NEXT_PUBLIC_GALLERY_BASE_URL` is the gallery repository's
     `https://huggingface.co/datasets/<owner>/<name>/resolve/main` address.
5. **GitHub Actions.** Under Settings → Secrets and variables → Actions, add the variables
   `SITE_URL` and `GALLERY_BASE_URL`. The health check starts once `SITE_URL` exists.
6. **Live upload, later.** With Hugging Face PRO or a community grant (D-023), run the ZeroGPU test in
   [zerogpu_spike.md](../reports/release/zerogpu_spike.md). If it passes, add the secret `HF_TOKEN`
   and the variables `HF_SPACE_ID` (GitHub) and `NEXT_PUBLIC_SPACE_ID` (Vercel), then redeploy.

## Launch checklist

- [ ] Results and model card are final and match `reports/`.
- [ ] Limits in `deployment.md` are rechecked and re-dated.
- [ ] The not-for-clinical-use notice shows on every result page.
- [ ] KiTS23 and nnU-Net are credited, and their licenses are stated.
- [ ] README has the live link and a short demo GIF.
- [ ] The site is opened from a phone and from a fresh browser with no accounts.
- [ ] `/try` shows a useful message when live inference is unavailable.

## Routine checks

| Check | Where | When |
|---|---|---|
| Health check is green | GitHub Actions, "Health check" | Weekly |
| Schedule still enabled | Same page. GitHub pauses it after 60 days without commits | Every 2 months |
| Neon storage below 800 MB of its 1 GB | Neon dashboard | Monthly |
| Vercel usage below its limits | Vercel dashboard | Monthly |

## When something runs out

| What happened | What visitors see | What to do |
|---|---|---|
| The Space is out of quota or asleep | `/try` offers the notebook instead | Nothing. Quotas renew by themselves |
| ZeroGPU rules change or the account loses access | Same | Remove `NEXT_PUBLIC_SPACE_ID` and redeploy |
| Neon is down or over quota | Everything works; statistics are hidden and not saved | Wait for it, or clean up below |
| Vercel's Hobby limit is reached | The site may go offline until the period renews | Lower traffic, or move the static build to another free host |
| Gallery files are missing | The viewer says the scan can't be loaded; scores still show | Re-upload them, or fix `NEXT_PUBLIC_GALLERY_BASE_URL` |

## Neon cleanup

Run statistics are small: about 100 bytes per run, so 800 MB holds millions of runs. If storage
does approach the limit, run this in the Neon SQL editor. Feedback stays, and its link to a deleted
run is cleared automatically.

```sql
DELETE FROM inference_run WHERE created_at < now() - interval '180 days';
VACUUM FULL inference_run;
```

The headline run counts on `/results` drop by the number of rows removed.

## Rotating a leaked token

1. Revoke it at the service first.
2. Create a new one and store it in that service's secret settings.
3. Run `python scripts/ops/scan_history.py`. If the token reached a commit, revoking it is what
   protects you; rewriting public history does not.

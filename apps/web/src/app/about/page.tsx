import type { Metadata } from "next";
import { LINKS, REPO_URL } from "@/lib/site";

export const metadata: Metadata = { title: "About" };

export default function About() {
  return (
    <div className="prose">
      <h1>About</h1>
      <p className="lede">
        A learning project that builds a 3D medical segmentation workflow from raw data to a public demo, and
        measures it properly.
      </p>

      <section>
        <h2>Method</h2>
        <div className="prose" style={{ marginTop: 12 }}>
          <p>
            The task is 3D semantic segmentation of contrast-enhanced abdominal CT, with labels for kidney, tumor
            and cyst. The model is the official nnU-Net v2 (2.8.1) in its 3d_fullres configuration, trained on the
            KiTS regions: kidney plus masses, masses, and tumor.
          </p>
          <p>
            The 489 labeled KiTS23 v0.1.4 cases were split at case level into 343 training, 73 validation and 73
            locked test cases. Two oversized whole-body scans were left out of training. Training ran for 100
            epochs on one fold on a free Kaggle GPU.
          </p>
          <p>
            Post-processing keeps the two largest connected foreground regions. It was chosen on validation data.
            The test set was then scored once with the official KiTS evaluator.
          </p>
        </div>
      </section>

      <section>
        <h2>Limitations</h2>
        <ul>
          <li>One fold and 100 epochs, against nnU-Net&apos;s standard five folds and 1000 epochs.</li>
          <li>Cysts are effectively not separated from tumors, and small tumors are often missed.</li>
          <li>The test set is internal, so scores can&apos;t be compared with the challenge leaderboard.</li>
          <li>There is no external hospital validation, and biases in KiTS23 are inherited.</li>
          <li>The contrast phase of each scan is unknown, so its effect can&apos;t be measured.</li>
        </ul>
      </section>

      <section>
        <h2>Not a medical device</h2>
        <p style={{ marginTop: 12 }}>
          The model must not be used for diagnosis, treatment planning or any decision about a patient. It has no
          regulatory clearance and no clinical validation.
        </p>
      </section>

      <section>
        <h2>Privacy</h2>
        <p style={{ marginTop: 12 }}>
          Uploaded scans go straight from your browser to the model on Hugging Face and never touch this website.
          They are deleted after processing. The database keeps run statistics and feedback only: no images, file
          names or IP addresses.
        </p>
      </section>

      <section>
        <h2>Credits and license</h2>
        <ul>
          <li>
            Data: <a href={LINKS.kits23}>the KiTS23 challenge</a> (<a href={LINKS.kits23Data}>dataset repository</a>),
            CC BY-NC-SA 4.0.
          </li>
          <li>Model framework: <a href={LINKS.nnunet}>nnU-Net</a>, by Isensee and colleagues.</li>
          <li>Viewer: <a href={LINKS.niivue}>NiiVue</a>.</li>
          <li>
            The model weights derive from the data, so they carry the same{" "}
            <a href={LINKS.license}>non-commercial license</a>.
          </li>
          {REPO_URL && <li>Source code: <a href={REPO_URL}>GitHub repository</a>.</li>}
        </ul>
      </section>
    </div>
  );
}

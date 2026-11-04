import type { Metadata } from "next";
import { Archivo, Source_Serif_4 } from "next/font/google";
import Link from "next/link";
import type { ReactNode } from "react";
import { SiteNav } from "@/components/SiteNav";
import { DISCLAIMER, LINKS } from "@/lib/site";
import "./globals.css";

const sans = Archivo({ subsets: ["latin"], axes: ["wdth"], variable: "--font-sans" });
const note = Source_Serif_4({ subsets: ["latin"], style: "italic", weight: "400", variable: "--font-note" });

export const metadata: Metadata = {
  title: { default: "Project 23D: kidney tumor segmentation in 3D CT", template: "%s · Project 23D" },
  description:
    "A nnU-Net model for kidney, tumor and cyst segmentation, trained on KiTS23. Explore real 3D results, including the failures.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${note.variable}`}>
      <body>
        <header className="masthead">
          <div className="frame">
            <Link className="wordmark" href="/">
              Project 23D
            </Link>
            <SiteNav />
          </div>
        </header>
        <div className="disclaimer">
          <div className="frame">{DISCLAIMER}.</div>
        </div>
        <main>{children}</main>
        <footer className="title-block">
          <div className="frame">
            <dl>
              <div>
                <dt>Data</dt>
                <dd><a href={LINKS.kits23}>KiTS23</a> challenge</dd>
              </div>
              <div>
                <dt>Model</dt>
                <dd><a href={LINKS.nnunet}>nnU-Net</a></dd>
              </div>
              <div>
                <dt>Viewer</dt>
                <dd><a href={LINKS.niivue}>NiiVue</a></dd>
              </div>
              <div>
                <dt>License</dt>
                <dd>Data and model weights: <a href={LINKS.license}>CC BY-NC-SA 4.0</a>, non-commercial use only</dd>
              </div>
            </dl>
          </div>
        </footer>
      </body>
    </html>
  );
}

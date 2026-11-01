import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from "next/font/google";
import Link from "next/link";
import type { ReactNode } from "react";
import { DISCLAIMER, LINKS } from "@/lib/site";
import "./globals.css";

const serif = Newsreader({ subsets: ["latin"], variable: "--font-serif" });
const sans = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-sans" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: { default: "Project 23D: kidney tumor segmentation in 3D CT", template: "%s · Project 23D" },
  description:
    "A nnU-Net model for kidney, tumor and cyst segmentation, trained on KiTS23. Explore real 3D results, including the failures.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${serif.variable} ${sans.variable} ${mono.variable}`}>
      <body>
        <header className="masthead">
          <div className="frame">
            <Link className="wordmark" href="/">
              Project 23D
            </Link>
            <nav aria-label="Main">
              <Link href="/gallery">Gallery</Link>
              <Link href="/results">Results</Link>
              <Link href="/try">Try a scan</Link>
              <Link href="/about">About</Link>
            </nav>
          </div>
        </header>
        <div className="disclaimer">
          <div className="frame">{DISCLAIMER}.</div>
        </div>
        <main className="frame">{children}</main>
        <footer className="colophon">
          <div className="frame">
            <p>
              Built on the <a href={LINKS.kits23}>KiTS23</a> challenge data and{" "}
              <a href={LINKS.nnunet}>nnU-Net</a>. Viewer by <a href={LINKS.niivue}>NiiVue</a>.
            </p>
            <p>
              Data and model weights: <a href={LINKS.license}>CC BY-NC-SA 4.0</a>, non-commercial use only.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

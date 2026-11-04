"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const PAGES = [
  { href: "/gallery", label: "Gallery" },
  { href: "/results", label: "Results" },
  { href: "/try", label: "Try a scan" },
  { href: "/about", label: "About" },
];

export function SiteNav() {
  const path = usePathname();
  const current = path.startsWith("/case/") ? "/gallery" : path;
  return (
    <nav aria-label="Main">
      {PAGES.map((page) => (
        <Link key={page.href} href={page.href} aria-current={current === page.href ? "page" : undefined}>
          {page.label}
        </Link>
      ))}
    </nav>
  );
}

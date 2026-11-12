// STATIC_EXPORT=1 builds plain HTML files for GitHub Pages, served under BASE_PATH (for example /Project_23D).
// That build has no server, so the database API routes are left out and the headers below don't apply.
const staticExport = process.env.STATIC_EXPORT === "1";

/** @type {import('next').NextConfig} */
const nextConfig = staticExport
  ? {
      output: "export",
      basePath: process.env.BASE_PATH || "",
      env: { NEXT_PUBLIC_BASE_PATH: process.env.BASE_PATH || "" },
      trailingSlash: true,
      images: { unoptimized: true },
    }
  : {
      poweredByHeader: false,
      async headers() {
        return [
          {
            source: "/:path*",
            headers: [
              { key: "X-Content-Type-Options", value: "nosniff" },
              { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
              { key: "X-Frame-Options", value: "DENY" },
            ],
          },
        ];
      },
    };

export default nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: all data fetching is client-side, against the API's own
  // origin (NEXT_PUBLIC_API_URL). See docs/PHASE1_PLAN.md section 3.1.
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;

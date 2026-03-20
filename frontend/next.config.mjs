/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // API calls go through src/app/api/[...path]/route.ts so BACKEND_URL / NEXT_PUBLIC_API_URL
  // are read at runtime (needed for DigitalOcean without rebuild).
};

export default nextConfig;

import type { NextConfig } from 'next';
// Runtime route handler keeps the private API hostname and bearer token out of browser bundles.
const nextConfig:NextConfig={distDir:process.env.NEXT_DIST_DIR||'.next'};
export default nextConfig;

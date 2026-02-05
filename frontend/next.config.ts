import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy API calls to the MCP server during development
  async rewrites() {
    return [
      {
        source: "/api/mcp/:path*",
        destination: "http://localhost:8420/:path*",
      },
    ];
  },
};

export default nextConfig;

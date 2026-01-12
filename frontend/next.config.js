const webpack = require("webpack");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "polymarket-upload.s3.us-east-2.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "**.polymarket.com",
      },
    ],
  },
  webpack: (config) => {
    // Fix for WalletConnect/MetaMask SDK SSR issues
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
      encoding: false,
      lokijs: false,
    };

    // Handle pino-pretty optional dependency
    config.resolve.alias = {
      ...config.resolve.alias,
      "pino-pretty": false,
    };

    // Ignore React Native async storage (MetaMask SDK optional dep)
    config.plugins.push(
      new webpack.IgnorePlugin({
        resourceRegExp: /^@react-native-async-storage\/async-storage$/,
      })
    );

    return config;
  },
};

module.exports = nextConfig;

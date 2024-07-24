/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (
    config,
    { buildId, dev, isServer, defaultLoaders, nextRuntime, webpack }
  ) => {
    // Important: return the modified config
    config.externals.unshift(
      {
        sqlite3: 'sqlite3',
        crypto: 'crypto',
        ws: 'ws',
        'indexeddb-js': 'indexeddb-js'
      })
    return config
  },
}

module.exports = nextConfig

import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

const TAILSCALE_IP = process.env.TAILSCALE_IP || '100.114.249.118'

function tailscaleNetwork(): Plugin {
  return {
    name: 'tailscale-network',
    configureServer(server) {
      const print = server.printUrls
      server.printUrls = () => {
        if (server.resolvedUrls) {
          server.resolvedUrls.network = server.resolvedUrls.network.map(
            url => url.replace(/\/\/[^:]+:/, `//${TAILSCALE_IP}:`)
          )
        }
        print()
      }
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailscaleNetwork()],
  server: {
    host: '0.0.0.0',
    port: 3300,
  },
})

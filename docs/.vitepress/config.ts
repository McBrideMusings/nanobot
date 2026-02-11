import { defineConfig } from 'vitepress'
import type { Plugin } from 'vite'

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

export default defineConfig({
  title: 'Nanobot Docs',
  description: 'A lightweight personal AI assistant framework',

  themeConfig: {
    nav: [
      { text: 'Guide', link: '/guide/getting-started' },
      { text: 'Architecture', link: '/architecture/overview' },
      { text: 'Development', link: '/development/setup' },
      { text: 'Features', link: '/features/mcp-support' },
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Guide',
          items: [
            { text: 'Getting Started', link: '/guide/getting-started' },
            { text: 'Channels', link: '/guide/channels' },
            { text: 'Skills', link: '/guide/skills' },
            { text: 'Providers', link: '/guide/providers' },
          ],
        },
      ],
      '/architecture/': [
        {
          text: 'Architecture',
          items: [
            { text: 'Overview', link: '/architecture/overview' },
            { text: 'Agent Loop', link: '/architecture/agent-loop' },
            { text: 'Workspace', link: '/architecture/workspace' },
          ],
        },
      ],
      '/development/': [
        {
          text: 'Development',
          items: [
            { text: 'Setup', link: '/development/setup' },
            { text: 'Testing', link: '/development/testing' },
            { text: 'Code Style', link: '/development/code-style' },
            { text: 'Deployment', link: '/development/deployment' },
            { text: 'Troubleshooting', link: '/development/troubleshooting' },
          ],
        },
      ],
      '/features/': [
        {
          text: 'Planned Features',
          items: [
            { text: 'MCP Support', link: '/features/mcp-support' },
            { text: 'Memory Search', link: '/features/memory-search' },
            { text: 'Background Process Tool', link: '/features/background-process-tool' },
            { text: 'Heartbeat Enhancements', link: '/features/heartbeat-enhancements' },
          ],
        },
        {
          text: 'Skills',
          items: [
            { text: 'ErsatzTV', link: '/features/ersatztv-skill' },
            { text: 'Tautulli + Plex', link: '/features/tautulli-plex-skill' },
            { text: 'Kometa', link: '/features/kometa-skill' },
          ],
        },
      ],
    },

    search: { provider: 'local' },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/McBrideMusings/nanobot' },
    ],

    editLink: {
      pattern: 'https://github.com/McBrideMusings/nanobot/edit/feature-apple-app/docs/:path',
    },
  },

  vite: {
    plugins: [tailscaleNetwork()],
    server: {
      host: '0.0.0.0',
      port: 3301,
    },
  },
})

import { defineConfig } from 'vitepress'
import type { Plugin } from 'vite'
import { markdownWriterPlugin } from 'vitepress-theme-pm/plugin'

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
      { text: 'Board', link: '/board' },
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
      '/tickets/': [
        {
          text: 'Chat App',
          items: [
            { text: 'NB-1: Agent Observability', link: '/tickets/1' },
            { text: 'NB-2: Core Chat Polish', link: '/tickets/2' },
            { text: 'NB-3: Replies & Reactions', link: '/tickets/3' },
            { text: 'NB-4: Inline Media', link: '/tickets/4' },
            { text: 'NB-5: Chat Search', link: '/tickets/5' },
            { text: 'NB-6: Workspace Inspector', link: '/tickets/6' },
            { text: 'NB-7: Bot Profile', link: '/tickets/7' },
            { text: 'NB-8: Notification Tuning', link: '/tickets/8' },
            { text: 'NB-9: Voice Messages', link: '/tickets/9' },
            { text: 'NB-10: Deferred Research', link: '/tickets/10' },
          ],
        },
        {
          text: 'Tools',
          items: [
            { text: 'NB-11: MCP Support', link: '/tickets/11' },
            { text: 'NB-12: Memory Search', link: '/tickets/12' },
            { text: 'NB-13: Background Process', link: '/tickets/13' },
            { text: 'NB-14: Heartbeat Enhancements', link: '/tickets/14' },
          ],
        },
        {
          text: 'Skills',
          items: [
            { text: 'NB-15: ErsatzTV', link: '/tickets/15' },
            { text: 'NB-16: Tautulli + Plex', link: '/tickets/16' },
            { text: 'NB-17: Kometa', link: '/tickets/17' },
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
    plugins: [tailscaleNetwork(), markdownWriterPlugin()],
    server: {
      host: '0.0.0.0',
      port: 3301,
    },
  },
})

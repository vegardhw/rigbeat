import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Rigbeat',
  description: 'Windows Hardware Monitoring for Prometheus & Grafana',
  base: '/rigbeat/',

  // Temporarily disable dead link checking
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', href: '/rigbeat/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#3c82f6' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:locale', content: 'en' }],
    ['meta', { property: 'og:title', content: 'Rigbeat | Windows Hardware Monitoring' }],
    ['meta', { property: 'og:site_name', content: 'Rigbeat' }],
    ['meta', { property: 'og:image', content: 'https://rigbeat.dev/og-image.png' }],
    ['meta', { property: 'og:url', content: 'https://rigbeat.dev/' }],
  ],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Home', link: '/' },
      { text: 'Get Started', link: '/getting-started/installation' },
      { text: 'Guide', link: '/guide/overview' },
      { text: 'Troubleshooting', link: '/troubleshooting/common-issues' },
      { text: 'Reference', link: '/reference/metrics' },
      {
        text: 'v0.1.1',
        items: [
          { text: 'GitHub', link: 'https://github.com/vegardhw/rigbeat' }
        ]
      }
    ],

    sidebar: {
      '/getting-started/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Installation', link: '/getting-started/installation' },
            { text: 'Requirements', link: '/getting-started/requirements' }
          ]
        }
      ],

      '/guide/': [
        {
          text: 'User Guide',
          items: [
            { text: 'Overview', link: '/guide/overview' },
            { text: 'Fan Detection', link: '/guide/fan-detection' },
            { text: 'Prometheus & Grafana', link: '/guide/prometheus-grafana' }
          ]
        }
      ],

      '/troubleshooting/': [
        {
          text: 'Troubleshooting',
          items: [
            { text: 'Common Issues', link: '/troubleshooting/common-issues' },
            { text: 'Fan Issues', link: '/troubleshooting/fan-issues' }
          ]
        }
      ],

      '/reference/': [
        {
          text: 'Reference',
          items: [
            { text: 'Metrics API', link: '/reference/metrics' },
            { text: 'Fan Metrics', link: '/reference/fan-metrics' }
          ]
        }
      ]
    },

    editLink: {
      pattern: 'https://github.com/vegardhw/rigbeat/edit/main/docs/:path'
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/vegardhw/rigbeat' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2025 Vegard Hoff Walmsness'
    },

    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: {
                buttonText: 'Search docs',
                buttonAriaLabel: 'Search docs'
              },
              modal: {
                noResultsText: 'No results for',
                resetButtonTitle: 'Clear search',
                footer: {
                  selectText: 'to select',
                  navigateText: 'to navigate'
                }
              }
            }
          }
        }
      }
    }
  }
})
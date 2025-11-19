import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Rigbeat',
  description: 'Windows Hardware Monitoring for Prometheus & Grafana',
  base: '/rigbeat/',
  
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
      { text: 'Reference', link: '/reference/metrics' },
      {
        text: 'v1.0.1',
        items: [
          { text: 'Changelog', link: '/changelog' },
          { text: 'Contributing', link: '/development/contributing' }
        ]
      }
    ],

    sidebar: {
      '/getting-started/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Installation', link: '/getting-started/installation' },
            { text: 'Requirements', link: '/getting-started/requirements' },
            { text: 'First Run', link: '/getting-started/first-run' },
            { text: 'Quick Start', link: '/getting-started/quick-start' }
          ]
        }
      ],
      
      '/guide/': [
        {
          text: 'User Guide',
          items: [
            { text: 'Overview', link: '/guide/overview' },
            { text: 'Hardware Setup', link: '/guide/hardware-setup' },
            { text: 'Windows Service', link: '/guide/service' },
            { text: 'Prometheus Config', link: '/guide/prometheus' },
            { text: 'Grafana Dashboard', link: '/guide/grafana' },
            { text: 'Docker Setup', link: '/guide/docker' }
          ]
        },
        {
          text: 'Monitoring',
          items: [
            { text: 'Fan Detection', link: '/guide/fans' },
            { text: 'Alerting', link: '/guide/alerting' },
            { text: 'Best Practices', link: '/guide/best-practices' }
          ]
        }
      ],

      '/troubleshooting/': [
        {
          text: 'Troubleshooting',
          items: [
            { text: 'Common Issues', link: '/troubleshooting/common-issues' },
            { text: 'Fan Detection', link: '/troubleshooting/fans' },
            { text: 'Service Problems', link: '/troubleshooting/service' },
            { text: 'Hardware Compatibility', link: '/troubleshooting/hardware' }
          ]
        }
      ],

      '/reference/': [
        {
          text: 'Reference',
          items: [
            { text: 'Metrics API', link: '/reference/metrics' },
            { text: 'Configuration', link: '/reference/configuration' },
            { text: 'Command Line', link: '/reference/cli' },
            { text: 'Windows Service', link: '/reference/service' }
          ]
        }
      ],

      '/development/': [
        {
          text: 'Development',
          items: [
            { text: 'Contributing', link: '/development/contributing' },
            { text: 'Building', link: '/development/building' },
            { text: 'Architecture', link: '/development/architecture' },
            { text: 'Testing', link: '/development/testing' }
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
      copyright: 'Copyright © 2025 Vegard H. Westereng'
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
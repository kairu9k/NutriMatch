export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  srcDir: 'app/',
  modules: ['@nuxtjs/tailwindcss', '@pinia/nuxt'],
  css: ['~/assets/css/main.css', '~/assets/css/portal.css'],
  // Login state lives in localStorage, which the server can't read — so a
  // logged-in page rendered on the server always comes out as the logged-out
  // version ("Good Day, RND."), then gets replaced in the browser ("Hydration
  // completed but contains mismatches"). The app pages are therefore rendered
  // in the browser only; the public marketing/auth pages keep server rendering.
  routeRules: {
    '/**': { ssr: false },
    '/': { ssr: true },
    '/about': { ssr: true },
    '/contact': { ssr: true },
    '/terms': { ssr: true },
    '/privacy-policy': { ssr: true },
    '/login': { ssr: true },
    '/register': { ssr: true },
    '/forgot-password': { ssr: true },
    '/reset-password': { ssr: true },
    '/admin/login': { ssr: true },
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api',
    },
  },
  app: {
    head: {
      title: 'NutriMatch',
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'icon', type: 'image/png', sizes: '192x192', href: '/icon-192.png' },
        { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' },
      ],
      style: [
        { children: 'html { scroll-behavior: smooth; }' }
      ]
    }
  }
})
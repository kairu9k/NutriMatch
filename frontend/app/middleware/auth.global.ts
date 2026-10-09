// Sends logged-out visitors to sign in instead of showing a page that just
// fails to load ("Could not load this patient"). Login lives in
// localStorage, so this only runs in the browser — the server can't see it.
// Admin pages (layout: 'admin') go to the admin sign-in page.
// Access control itself is the API's job (JWT + role permissions); this is
// only about sending people to the right place.
import { useAuthStore } from '~/stores/auth'

const PUBLIC_PATHS = new Set([
  '/', '/about', '/contact', '/privacy-policy', '/terms',
  '/login', '/register', '/forgot-password', '/reset-password', '/admin/login',
])

export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return

  const path = to.path.toLowerCase().replace(/\/+$/, '') || '/'
  if (PUBLIC_PATHS.has(path)) return

  const auth = useAuthStore()
  auth.hydrate() // no-op once app.vue has already restored the session
  if (auth.isAuthenticated) return

  return navigateTo(to.meta.layout === 'admin' ? '/admin/login' : '/login')
})

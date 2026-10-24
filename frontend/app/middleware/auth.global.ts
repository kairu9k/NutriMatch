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

const SIGNED_OUT_ONLY = new Set(['/login', '/register', '/admin/login'])
const DASHBOARDS: Record<string, string> = { client: '/client-dashboard', rnd: '/rnd-dashboard', admin: '/admin-dashboard' }

export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return

  const path = to.path.toLowerCase().replace(/\/+$/, '') || '/'

  // Already signed in: the sign-in and sign-up forms send you to your own
  // dashboard instead, so nobody signs in over an open session by mistake
  // (signing in as someone else means signing out first).
  if (SIGNED_OUT_ONLY.has(path)) {
    const auth = useAuthStore()
    auth.hydrate()
    if (auth.isAuthenticated && auth.user) return navigateTo(DASHBOARDS[auth.user.role] || '/')
    return
  }
  if (PUBLIC_PATHS.has(path)) return

  const auth = useAuthStore()
  auth.hydrate() // no-op once app.vue has already restored the session
  const isAdminPage = to.meta.layout === 'admin' || to.meta.admin === true
  if (!auth.isAuthenticated) {
    return navigateTo(isAdminPage ? '/admin/login' : '/login')
  }
  if (isAdminPage && auth.user?.role !== 'admin') {
    return navigateTo(auth.user?.role === 'rnd' ? '/rnd-dashboard' : '/client-dashboard')
  }

  // Strict client onboarding: until it's finished, a client is sent to
  // /onboarding (Profile Settings stays reachable). A session saved before
  // onboarding existed has no `onboarding_completed_at` key at all — those
  // accounts were marked onboarded, so only an explicit null redirects.
  const user = auth.user
  const needsOnboarding = user?.role === 'client'
    && Object.prototype.hasOwnProperty.call(user, 'onboarding_completed_at')
    && !user.onboarding_completed_at
  if (needsOnboarding && !['/onboarding', '/profile-settings'].includes(path)) {
    return navigateTo('/onboarding')
  }
  if (path === '/onboarding' && !needsOnboarding) {
    return navigateTo(user?.role === 'rnd' ? '/rnd-dashboard' : user?.role === 'admin' ? '/admin-dashboard' : '/client-dashboard')
  }
})

// v-click-outside was referenced in NotificationDropdown.vue/ProfileDropdown.vue
// but never actually registered anywhere. Vue silently warned and no-opped
// it client-side, but an unregistered directive crashes Nuxt's SSR render
// (@vue/server-renderer's ssrGetDirectiveProps assumes `dir` exists) —
// previously masked because these components' always-empty mock data kept
// them from ever rendering past the branch that uses it during SSR.
// Must be registered universally (not .client.ts) so SSR has a directive
// object to find; the actual outside-click listener only attaches
// client-side, since there's nothing to click during SSR anyway.
export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.directive('click-outside', {
    mounted(el, binding) {
      if (import.meta.server) return
      el.__clickOutsideHandler__ = (event: MouseEvent) => {
        if (!(el === event.target || el.contains(event.target as Node))) {
          binding.value(event)
        }
      }
      document.addEventListener('click', el.__clickOutsideHandler__, true)
    },
    unmounted(el) {
      if (import.meta.server) return
      document.removeEventListener('click', el.__clickOutsideHandler__, true)
      delete el.__clickOutsideHandler__
    },
  })
})

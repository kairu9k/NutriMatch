import { ref } from 'vue'
import { notificationLink } from '~/utils/notificationLink'

// Clicking a notification (bell list and Notifications page): look up what
// it's about, then go to that page. `opening` holds the id being looked up so
// the row can say "Opening…". Returns true when it navigated.
export function useOpenNotification() {
  const { get } = useApi()
  const auth = useAuthStore()
  const route = useRoute()
  const opening = ref(null)

  async function openNotification(n) {
    if (opening.value) return false
    opening.value = n.id
    let related = null
    try {
      related = (await get(`/notifications/${n.id}/`)).related
    } catch {
      // still go to the main page for this kind of notification
    }
    const to = notificationLink(n, related, auth.user?.role, route)
    opening.value = null
    if (!to) return false
    await navigateTo(to)
    return true
  }

  return { opening, openNotification }
}

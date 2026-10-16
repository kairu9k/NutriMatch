// Unread chat messages — the dot on the top-bar Messages icon and on each
// conversation on the Messages page — plus each chat's latest message (the
// list previews, before a conversation is opened). Chat isn't in the bell
// (backend communication/views.py MessageUnreadView / MessageMarkReadView).
export function useUnreadMessages() {
  const unread = useState('unread-messages', () => ({ total: 0, byRelationship: {}, latest: {} }))
  const { get, post } = useApi()

  async function refresh() {
    try {
      const data = await get('/messages/unread/')
      unread.value = { total: data.total, byRelationship: data.by_relationship || {}, latest: data.latest || {} }
    } catch { /* keep the last count */ }
  }

  // Marks the other person's messages in this chat read; the badge drops
  // right away, before the request finishes.
  async function markRead(relationshipId) {
    const by = { ...unread.value.byRelationship }
    if (by[relationshipId]) {
      unread.value = { ...unread.value, total: Math.max(0, unread.value.total - by[relationshipId]), byRelationship: { ...by, [relationshipId]: 0 } }
    }
    try {
      await post(`/relationships/${relationshipId}/messages/read/`)
    } catch { /* the next refresh corrects it */ }
  }

  return { unread, refresh, markRead }
}

// Pages a list that's already loaded, 20 at a time (same as the server-paged
// lists). `resetOn` (a getter) sends it back to page 1 when a filter or search
// changes; a shorter list never leaves it on a page that no longer exists.
export function usePager(list, { perPage = 20, resetOn } = {}) {
  const page = ref(1)
  const pages = computed(() => Math.max(1, Math.ceil(list.value.length / perPage)))
  const paged = computed(() => list.value.slice((page.value - 1) * perPage, page.value * perPage))
  if (resetOn) watch(resetOn, () => { page.value = 1 })
  watch(pages, n => { if (page.value > n) page.value = n })
  return { page, pages, paged }
}

// Pay an invoice through PayMongo — shared by the Billing page and My
// Appointments (pay before the consultation).
//
// Opens the checkout in a popup (opened synchronously in the click handler,
// or browsers block it), then asks PayMongo via our sync endpoint every few
// seconds whether the invoice is paid. Payment Links can't redirect after
// paying, so once it's paid we close the popup ourselves — allowed because
// this page opened it. Stops if the client closes the popup, or after 30
// minutes (the QR code's lifetime).
import { onBeforeUnmount, ref } from 'vue'

const CHECK_EVERY_MS = 4000
const MAX_WATCH_MS = 30 * 60 * 1000

export function usePayInvoice() {
  const { get, post } = useApi()
  const payingId = ref(null)
  const payError = ref('')
  let watcher = null

  function stop() {
    if (watcher) clearInterval(watcher)
    watcher = null
  }

  function watch(popup, invoiceId, { onPaid, onClosed }) {
    stop()
    const startedAt = Date.now()
    let checking = false
    watcher = setInterval(async () => {
      if (popup.closed || Date.now() - startedAt > MAX_WATCH_MS) {
        stop()
        onClosed?.()
        return
      }
      if (checking) return
      checking = true
      try {
        // Check the invoice's real status, not just whether this sync call
        // flipped it — the webhook may have marked it paid first.
        await post('/client/invoices/sync/').catch(() => null)
        const latest = await get('/client/invoices/')
        if (latest.find(i => i.id === invoiceId)?.status === 'paid') {
          stop()
          popup.close()
          onPaid?.(latest)
        }
      } catch {
        // Transient — try again on the next tick.
      } finally {
        checking = false
      }
    }, CHECK_EVERY_MS)
  }

  async function pay(invoiceId, { onPaid, onClosed } = {}) {
    payingId.value = invoiceId
    payError.value = ''
    const width = 480
    const height = 720
    const left = window.screenX + (window.outerWidth - width) / 2
    const top = window.screenY + (window.outerHeight - height) / 2
    const popup = window.open(
      '',
      'paymongo-checkout',
      `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
    )
    try {
      const result = await post(`/client/invoices/${invoiceId}/pay/`)
      if (result.payment_url) {
        if (popup) {
          popup.location.href = result.payment_url
          watch(popup, invoiceId, { onPaid, onClosed })
        } else {
          window.location.href = result.payment_url
        }
      } else if (popup) {
        popup.close()
      }
    } catch (error) {
      payError.value = error?.data?.detail || 'Could not start payment. Please try again.'
      if (popup) popup.close()
    } finally {
      payingId.value = null
    }
  }

  onBeforeUnmount(stop)
  return { pay, payingId, payError }
}

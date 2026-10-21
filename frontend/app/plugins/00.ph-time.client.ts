// Philippine time and the server's clock, app-wide (user's call, 2026-10-22).
//
// 1. Every date/time shown with toLocale*String() is in Asia/Manila unless a
//    caller asks for another time zone — whatever the device is set to.
// 2. "Now" (new Date(), Date.now()) follows the server's clock: every API
//    reply carries X-Server-Time (backend core/server_time.py; useApi ->
//    syncServerClock), and the difference to the device clock is applied.
//    Changing the phone's date or time therefore changes nothing in the app.
//    The server enforces every rule anyway (booking times, join window,
//    meal-log day…) — this keeps what people see in step with it.
//
// Named 00.* so it runs before the other plugins.
const TZ = 'Asia/Manila'
const OFFSET_KEY = 'nm_clock_offset'
const IGNORE_BELOW_MS = 5000 // network delay noise

export default defineNuxtPlugin(() => {
  const proto = Date.prototype as any
  for (const name of ['toLocaleString', 'toLocaleDateString', 'toLocaleTimeString']) {
    const original = proto[name]
    proto[name] = function (locales?: any, options?: Intl.DateTimeFormatOptions) {
      return original.call(this, locales, { ...(options || {}), timeZone: options?.timeZone || TZ })
    }
  }

  const RealDate = Date
  let offset = 0
  try { offset = Number(sessionStorage.getItem(OFFSET_KEY)) || 0 } catch { /* private mode */ }

  class ServerDate extends RealDate {
    constructor(...args: any[]) {
      if (args.length === 0) super(RealDate.now() + offset)
      else super(...(args as [any]))
    }

    static now() {
      return RealDate.now() + offset
    }
  }
  ;(window as any).Date = ServerDate

  return {
    provide: {
      // `header` = X-Server-Time, the server's time in epoch milliseconds.
      syncServerClock(header: string | null) {
        const server = header ? Number(header) : NaN
        if (!Number.isFinite(server) || server <= 0) return
        const diff = server - RealDate.now()
        offset = Math.abs(diff) < IGNORE_BELOW_MS ? 0 : diff
        try { sessionStorage.setItem(OFFSET_KEY, String(offset)) } catch { /* private mode */ }
      },
    },
  }
})

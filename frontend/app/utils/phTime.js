// Philippine calendar values for "today" logic. new Date() already follows
// the server's clock (plugins/00.ph-time.client.ts); these read it in
// Asia/Manila instead of the device's own time zone.
const PH = { timeZone: 'Asia/Manila' }

// 'YYYY-MM-DD' in Philippine time.
export function phIso(d = new Date()) {
  return d.toLocaleDateString('en-CA', PH)
}

// 0 = Sunday … 6 = Saturday, in Philippine time.
export function phWeekday(d = new Date()) {
  return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(d.toLocaleDateString('en-US', { ...PH, weekday: 'short' }))
}

// 0–23 in Philippine time.
export function phHour(d = new Date()) {
  return Number(d.toLocaleString('en-US', { ...PH, hour: 'numeric', hourCycle: 'h23' }))
}

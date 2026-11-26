// Whether the server runs in demo mode (backend scheduling/demo.py, GET /api/public/config/):
// Pay is instant without PayMongo, bookings can start soon, the room opens once paid.
// Asked once per page load and shared; false until the answer arrives or if it fails.
export function useDemoMode() {
  const demoMode = useState('demo-mode', () => false)
  const asked = useState('demo-mode-asked', () => false)
  if (!asked.value && import.meta.client) {
    asked.value = true
    const { get } = useApi()
    get('/public/config/').then((cfg) => { demoMode.value = !!cfg?.demo_mode }).catch(() => {})
  }
  return demoMode
}

// The server's answer right now, for code that must not guess (the Pay click).
export async function fetchDemoMode() {
  const demoMode = useState('demo-mode', () => false)
  try {
    const { get } = useApi()
    demoMode.value = !!(await get('/public/config/'))?.demo_mode
  } catch {
    // keep the last answer
  }
  return demoMode.value
}

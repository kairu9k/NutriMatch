// Lab results (clinical/labs.py). File rules mirror the API's
// ALLOWED_EXTENSIONS / MAX_FILE_BYTES / MAX_FILES_PER_UPLOAD.

// The file picker's filter: MIME types + extensions, so Windows, macOS and
// phones all open it showing only PDFs and images. The OS still shows folders
// and lets the user switch to "All files", so splitLabFiles() checks every
// pick, and the API checks the file contents again (clinical/labs.py).
export const LAB_ACCEPT = 'image/jpeg,image/png,application/pdf,.jpg,.jpeg,.png,.pdf'
export const LAB_MAX_MB = 10
export const LAB_MAX_FILES = 5
const KINDS = { pdf: 'pdf', jpg: 'jpg', jpeg: 'jpg', png: 'png' }

// What the file really is, from its first bytes (a renamed .docx isn't a PDF).
async function sniff(file) {
  try {
    const b = new Uint8Array(await file.slice(0, 8).arrayBuffer())
    if (b[0] === 0x25 && b[1] === 0x50 && b[2] === 0x44 && b[3] === 0x46) return 'pdf' // %PDF
    if (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) return 'png'
    if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return 'jpg'
  } catch { /* unreadable → rejected below */ }
  return null
}

// Keeps the files that can be uploaded and explains the ones left out:
// { ok: File[], error: '' | 'Left out: …' }. `room` = how many more fit.
export async function splitLabFiles(files, room = LAB_MAX_FILES) {
  const ok = []
  const out = []
  for (const f of files) {
    const kind = KINDS[(f.name.split('.').pop() || '').toLowerCase()]
    if (!kind || (await sniff(f)) !== kind) out.push(`${f.name} (only PDF, JPG or PNG files)`)
    else if (f.size > LAB_MAX_MB * 1024 * 1024) out.push(`${f.name} (larger than ${LAB_MAX_MB} MB)`)
    else if (ok.length >= room) out.push(`${f.name} (up to ${LAB_MAX_FILES} files at a time)`)
    else ok.push(f)
  }
  return { ok, error: out.length ? `Left out: ${out.join('; ')}.` : '' }
}

// Final check before sending (count + empty), or '' when fine.
export function labFilesError(files) {
  if (!files.length) return 'Choose a file to upload.'
  if (files.length > LAB_MAX_FILES) return `Upload up to ${LAB_MAX_FILES} files at a time.`
  return ''
}

export const fileSize = b => (b >= 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`)

const PH = { timeZone: 'Asia/Manila' }
export const labDate = iso => new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
export const labDayTime = iso => new Date(iso).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
export const labDay = iso => new Date(iso).toLocaleDateString('en-PH', { ...PH, month: 'short', day: 'numeric' })

export function neededBefore(req) {
  return req.needed_before ? `Needed before ${labDay(req.needed_before)} (your next consultation)` : 'Needed before your next consultation'
}

// "3 days before the consultation" / "On the consultation day"
export function consultGap(r) {
  const d = r.days_before_consultation
  if (d == null) return ''
  if (d === 0) return 'On the consultation day'
  return `${d} day${d === 1 ? '' : 's'} before the consultation`
}

export const FASTED_LABEL = { yes: 'Fasted 8+ hours', no: 'Not fasting', na: '' }

// Opens a lab file through the API (it's never a public link). The tab is
// opened first, synchronously, so pop-up blockers allow it.
// The private file is fetched through the API (it can take a few seconds), so
// the new tab says so straight away instead of sitting blank, and says so
// plainly if the file can't be opened.
function tabMessage(win, title, text) {
  if (!win) return
  win.document.title = title
  win.document.body.innerHTML = `<p style="font-family: Inter, system-ui, sans-serif; color: #1a3a1a; margin: 40px auto; max-width: 420px; text-align: center; line-height: 1.5">${text}</p>`
}
export async function openLabFile(get, path) {
  const win = window.open('', '_blank')
  tabMessage(win, 'Opening your lab result', 'Opening your lab result. This can take a few seconds.')
  try {
    const blob = await get(path, { responseType: 'blob' })
    const url = URL.createObjectURL(blob)
    if (win) win.location.href = url
    else window.location.href = url
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
    return true
  } catch {
    tabMessage(win, 'Could not open the file', 'This file could not be opened. Close this tab and try again, or upload it again if the problem stays.')
    return false
  }
}

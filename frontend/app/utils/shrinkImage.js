// Make a photo small enough to upload quickly on a phone connection before it
// is sent (2026-10-26: a 4-5 MB license photo timed out at sign-up with no
// clear message). Long side at most `maxSide` px, saved as JPEG; still sharp
// enough to read a PRC license. Returns the original if shrinking fails or
// wouldn't make it smaller.
export async function shrinkImage(file, { maxSide = 2000, quality = 0.85 } = {}) {
  try {
    const bitmap = await createImageBitmap(file)
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height))
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(bitmap.width * scale)
    canvas.height = Math.round(bitmap.height * scale)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#fff' // a transparent PNG gets a white background, not black
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
    bitmap.close?.()
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', quality))
    if (!blob || blob.size >= file.size) return file
    const name = file.name.replace(/\.[^.]+$/, '') + '.jpg'
    return new File([blob], name, { type: 'image/jpeg', lastModified: Date.now() })
  } catch {
    return file
  }
}

// Mobile numbers from any country, checked by that country's own rules.
// The rules (lengths, valid prefixes, mobile vs landline) come from Google's
// libphonenumber data — the same data the API checks with
// (core/validators.py validate_phone), so the form and the server agree.
// Numbers are saved in E.164 (+639171234567); a number without a + is read
// as Philippine. The field is optional: '' means not given.
import { AsYouType, getCountries, getCountryCallingCode, getExampleNumber, parsePhoneNumberFromString } from 'libphonenumber-js/max'
import { Metadata } from 'libphonenumber-js/core'
import metadata from 'libphonenumber-js/max/metadata'
import examples from 'libphonenumber-js/mobile/examples'

export const DEFAULT_PHONE_COUNTRY = 'PH'
const MOBILE_TYPES = ['MOBILE', 'FIXED_LINE_OR_MOBILE']

const regionNames = new Intl.DisplayNames(['en'], { type: 'region' })
export const countryName = (code) => regionNames.of(code) || code

// Every country, Philippines first, then A–Z: { code, name, dial }.
export const PHONE_COUNTRIES = getCountries()
  .map((code) => ({ code, name: countryName(code), dial: getCountryCallingCode(code) }))
  .sort((a, b) => (a.code === DEFAULT_PHONE_COUNTRY ? -1 : b.code === DEFAULT_PHONE_COUNTRY ? 1 : a.name.localeCompare(b.name)))

const plans = new Metadata(metadata)

// The most digits a mobile number can have in this country, not counting
// the national prefix (the 0 in 0917…). Used to stop typing past it.
export function maxMobileDigits(country) {
  plans.selectNumberingPlan(country)
  const lengths = plans.numberingPlan.type('MOBILE')?.possibleLengths() || plans.numberingPlan.possibleLengths()
  return Math.max(...lengths)
}

export function nationalPrefix(country) {
  plans.selectNumberingPlan(country)
  return plans.numberingPlan.nationalPrefix() || ''
}

// A sample mobile number in international form: +63 905 123 4567.
export function exampleMobile(country) {
  return getExampleNumber(country, examples)?.formatInternational() || ''
}

// The same sample without the country code (905 123 4567), for the number
// box, which shows the code beside it.
export function exampleLocal(country) {
  return localPart(exampleMobile(country), country)
}

function localPart(international, country) {
  return international.replace(`+${getCountryCallingCode(country)}`, '').trim()
}

// The digits after the country code, grouped the international way:
// 9171234567 → 917 123 4567 (shown after +63).
export function formatLocal(digits, country) {
  if (!digits) return ''
  return localPart(new AsYouType().input(`+${getCountryCallingCode(country)}${digits}`), country)
}

// The digits after the country code (for the chosen country) → the value to
// save: '' when empty, otherwise E.164. An invalid number is still returned
// as +<code><digits> so phoneError() can say what's wrong.
export function toE164(digits, country) {
  if (!digits) return ''
  const full = `+${getCountryCallingCode(country)}${digits}`
  return parsePhoneNumberFromString(full)?.number || full
}

// A saved value → { country, digits } for the field.
export function splitPhone(value) {
  if (!value) return { country: DEFAULT_PHONE_COUNTRY, digits: '' }
  const parsed = parsePhoneNumberFromString(value, DEFAULT_PHONE_COUNTRY)
  if (!parsed) return { country: DEFAULT_PHONE_COUNTRY, digits: String(value).replace(/\D/g, '') }
  return { country: parsed.country || countryForCode(parsed.countryCallingCode), digits: parsed.nationalNumber }
}

// The main country for a calling code (+1 → US, +44 → GB, +63 → PH).
export function countryForCode(dial) {
  return plans.getCountryCodesForCallingCode(dial)?.[0] || DEFAULT_PHONE_COUNTRY
}

// '' when the value is fine (or blank), otherwise the message to show.
export function phoneError(value) {
  if (!value) return ''
  const parsed = parsePhoneNumberFromString(value, DEFAULT_PHONE_COUNTRY)
  if (!parsed) return 'Enter a mobile number, e.g. +63 917 123 4567.'
  if (parsed.isValid() && MOBILE_TYPES.includes(parsed.getType())) return ''
  const country = parsed.country || countryForCode(parsed.countryCallingCode)
  const example = exampleMobile(country)
  return `Enter a valid ${countryName(country)} mobile number${example ? `, e.g. ${example}` : ''}.`
}

// For showing a saved number: +63 917 123 4567.
export function formatPhone(value) {
  if (!value) return ''
  const parsed = parsePhoneNumberFromString(value, DEFAULT_PHONE_COUNTRY)
  return parsed?.isValid() ? parsed.formatInternational() : value
}

<template>
  <div class="nm-modal-overlay" @click.self="emit('close')">
    <div class="sum" role="dialog" aria-modal="true" aria-labelledby="sum-title">
      <header class="sum-head">
        <img class="sum-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="sum-fade" aria-hidden="true"></span>
        <img v-if="row.patient.profile_photo" :src="row.patient.profile_photo" alt="" class="sum-av photo" />
        <span v-else class="sum-av" aria-hidden="true">{{ initials }}</span>
        <div class="sum-head-txt">
          <p class="kind">{{ row.is_follow_up ? `Follow-up #${row.follow_up_no}` : 'Initial record' }}, {{ shortDate(row.encounter_date) }}</p>
          <h2 id="sum-title" class="sum-title">{{ row.patient.name }}</h2>
          <p class="sub">{{ patientLine }}</p>
        </div>
        <div class="head-right">
          <span class="nm-pill status-pill" :class="row.status === 'completed' ? 'green' : 'gold'"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect v-if="row.status === 'completed'" x="4" y="10" width="16" height="11" rx="2" /><path v-if="row.status === 'completed'" d="M8 10V7a4 4 0 0 1 8 0v3" /><path v-else d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" /></svg>{{ row.status === 'completed' ? 'Finalized' : 'Draft' }}</span>
          <button type="button" class="icon-x" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
        </div>
      </header>

      <div class="sum-body">
        <p v-if="loading" class="nm-muted sum-loading"><span class="sum-spin" aria-hidden="true"></span> Loading record…</p>
        <p v-else-if="error" class="nm-error">{{ error }}</p>
        <template v-else-if="r">
          <p v-if="row.appointment" class="linked"><CalendarCheck :size="14" /> Written for the {{ row.appointment.type_label.toLowerCase() }} consultation on {{ longWhen(row.appointment.scheduled_at) }}</p>
          <p v-if="row.status === 'draft'" class="draft-note"><PenLine :size="14" aria-hidden="true" /> Unfinished. It still needs {{ row.missing.join(', ') || 'a final check' }}.</p>

          <section class="s-assess">
            <h3><span class="h-num">1</span>Assessment</h3>
            <dl class="facts">
              <div v-for="[k, v] in assessment" :key="k"><dt>{{ k }}</dt><dd :class="{ empty: v === '—' }">{{ v }}</dd></div>
            </dl>
            <p v-if="r.lab_notes" class="txt"><span class="k">Lab notes</span>{{ r.lab_notes }}</p>
            <p v-if="r.assessment_notes" class="txt"><span class="k">Assessment notes</span>{{ r.assessment_notes }}</p>
          </section>

          <section class="s-diag">
            <h3><span class="h-num">2</span>Diagnosis</h3>
            <p v-if="pes" class="pes"><mark>{{ r.pes_problem }}</mark>{{ pes.slice(r.pes_problem.length) }}</p>
            <p v-else class="pes empty">Not written yet.</p>
          </section>

          <section class="s-int">
            <h3><span class="h-num">3</span>Intervention</h3>
            <dl class="facts">
              <div v-for="[k, v] in intervention" :key="k"><dt>{{ k }}</dt><dd :class="{ empty: v === '—' }">{{ v }}</dd></div>
            </dl>
            <p v-if="r.diet_prescription" class="txt"><span class="k">Diet prescription</span>{{ r.diet_prescription }}</p>
            <p v-if="r.intervention_notes" class="txt"><span class="k">Intervention notes</span>{{ r.intervention_notes }}</p>
          </section>

          <section v-if="row.is_follow_up || r.goal_status || r.monitoring_notes" class="s-mon">
            <h3><span class="h-num">4</span>Monitoring &amp; evaluation</h3>
            <dl class="facts">
              <div><dt>Goal status</dt><dd>{{ GOALS[r.goal_status] || '—' }}</dd></div>
            </dl>
            <p v-if="r.monitoring_notes" class="txt"><span class="k">Monitoring notes</span>{{ r.monitoring_notes }}</p>
          </section>

          <p class="sig"><span class="sig-ico"><PenLine :size="16" aria-hidden="true" /></span><span>By {{ rnd.name }}{{ rnd.prc_license_number ? `, RND, PRC No. ${rnd.prc_license_number}` : '' }}. {{ row.status === 'completed' ? `Finalized ${dateTime(r.updated_at)}` : `Last edited ${dateTime(r.updated_at)}` }}.</span></p>
        </template>
      </div>

      <footer class="sum-foot">
        <NuxtLink :to="`/client-detail/${row.relationship_id}?tab=ncp`" class="nm-btn-outline" @click="emit('close')"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg> Open patient chart</NuxtLink>
        <div class="foot-right">
          <NuxtLink v-if="row.status === 'draft' && row.relationship_status === 'active'" :to="`/client-detail/${row.relationship_id}?tab=ncp&open=draft`" class="nm-btn-dark" @click="emit('close')">Continue in chart</NuxtLink>
          <button v-if="row.status === 'completed' && r" type="button" class="nm-btn-dark" @click="print"><Printer :size="15" /> Print / PDF</button>
        </div>
      </footer>
      <p v-if="printError" class="nm-field-error pad">{{ printError }}</p>
    </div>
  </div>
</template>

<script setup>
// Read-only summary of one NCP record (NCP Records page). Records are
// written on the patient chart, never here; finalized ones can be printed.
import { CalendarCheck, PenLine, Printer, X } from 'lucide-vue-next'
import { TER_ACTIVITY, bmiClass, bpLabel, glucoseCategory, hba1cCategory } from '~/utils/ncp'

const withCat = (text, cat) => (cat ? `${text}, ${cat.label}` : text)
const withPct = (text, pct) => (pct != null && text !== '—' ? `${text} (${pct}% of TER)` : text)

const props = defineProps({
  row: { type: Object, required: true }, // a record row from /rnd/ncp/overview/
  rnd: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close'])
const { get } = useApi()

const r = ref(null)
const loading = ref(true)
const error = ref('')
const printError = ref('')
onMounted(async () => {
  try {
    r.value = await get(`/rnd/ncp/${props.row.id}/`)
  } catch {
    error.value = 'Could not load this record.'
  } finally {
    loading.value = false
  }
})

const GOALS = { met: 'Met', partially_met: 'Partially met', not_met: 'Not met', ongoing: 'Ongoing' }
const SEX = { male: 'Male', female: 'Female' }
const PH = { timeZone: 'Asia/Manila' }
const longWhen = v => new Date(v).toLocaleString('en-PH', { ...PH, month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
const num = (v, unit, dp = 1) => (v == null || v === '' ? '—' : `${Number(v).toFixed(dp).replace(/\.0+$/, '')}${unit ? ` ${unit}` : ''}`)
const patientLine = computed(() => [props.row.patient.age != null ? `${props.row.patient.age} y/o` : null, SEX[props.row.patient.sex]].filter(Boolean).join(', '))

const assessment = computed(() => {
  const x = r.value
  const rows = [
    ['Height', num(x.height_cm, 'cm')], ['Weight', num(x.weight_kg, 'kg')],
    ['BMI', x.bmi ? `${Number(x.bmi).toFixed(1)}, ${bmiClass(Number(x.bmi))}` : '—'],
    ['Blood pressure', bpLabel(x.blood_pressure) || '—'],
    ['Fasting glucose', withCat(num(x.blood_glucose, 'mg/dL', 0), glucoseCategory(x.blood_glucose))],
    ['HbA1c', withCat(num(x.hba1c, '%'), hba1cCategory(x.hba1c))],
  ]
  for (const e of x.assessment_extra || []) rows.push([e.label, `${e.value}${e.unit ? ` ${e.unit}` : ''}`])
  return rows
})
const intervention = computed(() => {
  const x = r.value
  const rows = [
    ['TER (Total Energy Requirement)', x.target_kcal
      ? `${Math.round(x.target_kcal).toLocaleString('en-PH')} kcal/day${x.ter_activity ? `, ${TER_ACTIVITY.find(t => t.value === x.ter_activity)?.label.toLowerCase()} activity` : ''}`
      : '—'],
    ['Carbohydrate', withPct(num(x.target_carb_g, 'g', 0), x.carb_pct)], ['Protein', withPct(num(x.target_protein_g, 'g', 0), x.protein_pct)],
    ['Fat', withPct(num(x.target_fat_g, 'g', 0), x.fat_pct)],
  ]
  for (const e of x.intervention_extra || []) rows.push([e.label, `${e.value}${e.unit ? ` ${e.unit}` : ''}`])
  return rows
})
const pes = computed(() => {
  const x = r.value
  if (!x?.pes_problem) return ''
  return `${x.pes_problem}${x.pes_etiology ? ` related to ${x.pes_etiology}` : ''}${x.pes_signs ? `, as evidenced by ${x.pes_signs}` : ''}.`
})

function print() {
  const x = r.value
  const sections = [
    { heading: '1. Nutrition assessment', rows: assessment.value, text: [x.lab_notes && `Lab notes: ${x.lab_notes}`, x.assessment_notes && `Notes: ${x.assessment_notes}`].filter(Boolean).join('\n') },
    { heading: '2. Nutrition diagnosis (PES)', text: pes.value || '—' },
    { heading: '3. Nutrition intervention', rows: intervention.value, text: [x.diet_prescription && `Diet prescription: ${x.diet_prescription}`, x.intervention_notes && `Notes: ${x.intervention_notes}`].filter(Boolean).join('\n') },
  ]
  if (props.row.is_follow_up || x.goal_status || x.monitoring_notes) {
    sections.push({ heading: '4. Monitoring & evaluation', rows: [['Goal status', GOALS[x.goal_status] || '—']], text: x.monitoring_notes || '' })
  }
  const ok = printDocument({
    title: 'Nutrition Care Process record',
    number: `NCP-${String(x.id).padStart(4, '0')}, ${props.row.is_follow_up ? `Follow-up #${props.row.follow_up_no}` : 'Initial'}`,
    rows: [
      ['Patient', props.row.patient.name], ['Age and sex', patientLine.value || '—'],
      ['Encounter date', shortDate(props.row.encounter_date)],
      ['Registered Nutritionist-Dietitian', `${props.rnd.name || ''}${props.rnd.prc_license_number ? ` (PRC No. ${props.rnd.prc_license_number})` : ''}`],
      ['Finalized', dateTime(x.updated_at)],
    ],
    sections,
    foot: 'Confidential health information. Handle according to the Data Privacy Act of 2012 (RA 10173). Generated by NutriMatch.',
  })
  printError.value = ok ? '' : 'Your browser blocked the print window. Allow pop-ups for this site and try again.'
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// first and last name, e.g. Ivy Hope Alba → IA
const initials = computed(() => {
  const w = String(props.row.patient.name || '?').split(' ').filter(Boolean)
  return (w.length > 1 ? w[0][0] + w[w.length - 1][0] : (w[0] || '?')[0]).toUpperCase()
})
</script>
<style scoped>
.sum {
  --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12);
  display: flex; flex-direction: column; width: 100%; max-width: 900px; max-height: 92dvh; overflow: hidden;
  background: #fff; border-radius: 22px; font-family: 'DM Sans', sans-serif; color: #22362c; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.5);
}
.ic { flex-shrink: 0; }

/* ---------- green header with the plate ---------- */
.sum-head {
  position: relative; overflow: hidden; flex-shrink: 0; display: flex; align-items: center; gap: 16px; padding: 24px 28px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%);
}
.sum-head > *:not(.sum-plate):not(.sum-fade) { position: relative; z-index: 1; }
.sum-plate { position: absolute; right: -10px; top: 50%; width: 270px; height: 270px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.sum-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.82) 66%, rgba(0, 77, 58, 0.6) 82%, rgba(0, 77, 58, 0.55) 100%); }
.sum-av {
  flex-shrink: 0; width: 56px; height: 56px; border-radius: 50%; box-sizing: border-box; object-fit: cover;
  display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a;
  font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; border: 3px solid rgba(255, 255, 255, 0.9); box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.14);
}
.sum-head-txt { flex: 1; min-width: 0; }
.kind { margin: 0 0 4px; font-size: 12px; font-weight: 800; color: #efbf04; }
.sum-title { margin: 0; font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; line-height: 1.25; letter-spacing: 0.015em; color: #fff; overflow-wrap: anywhere; }
.sub { margin: 4px 0 0; font-size: 14px; color: rgba(255, 255, 255, 0.85); }
.head-right { display: flex; align-items: center; gap: 10px; }
.status-pill { display: inline-flex; align-items: center; gap: 5px; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 800; box-shadow: 0 6px 14px -8px rgba(0, 0, 0, 0.5); }
.status-pill.green { background: #e3f4ea; color: #1f7a4d; }
.status-pill.gold { background: #fff4d6; color: #8a6500; }
.icon-x {
  width: 40px; height: 40px; display: inline-flex; align-items: center; justify-content: center; border-radius: 12px; cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.3); background: rgba(0, 56, 42, 0.55); color: #fff; backdrop-filter: blur(6px);
}
.icon-x:hover { background: rgba(0, 56, 42, 0.8); }
.icon-x:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }

/* ---------- body ---------- */
.sum-body { flex: 1; min-height: 0; overflow-y: auto; padding: 18px 28px 22px; }
.sum-loading { display: flex; align-items: center; gap: 10px; margin: 0; padding: 30px 0; justify-content: center; }
.sum-spin { width: 20px; height: 20px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: sum-spin 0.8s linear infinite; }
@keyframes sum-spin { to { transform: rotate(360deg); } }
.linked, .draft-note { display: flex; align-items: center; gap: 8px; margin: 0 0 8px; padding: 10px 14px; border-radius: 12px; font-size: 13.5px; font-weight: 600; }
.linked { background: #e3f4ea; color: #1f5c45; }
.linked svg { flex-shrink: 0; color: #1f7a4d; }
.draft-note { background: #fffdf5; border: 1.5px dashed #e7c65a; color: #6b5a1e; }
.draft-note svg { flex-shrink: 0; color: #9a7300; }
section { padding: 20px 0; border-top: 1px solid #eef2ef; }
section:first-of-type { border-top: none; }
h3 { display: flex; align-items: center; gap: 10px; margin: 0 0 14px; font-size: 13px; font-weight: 800; color: #0e3a2c; }
.h-num { width: 24px; height: 24px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; background: #004d3a; color: #efbf04; font-size: 12.5px; letter-spacing: 0; }
.s-diag .h-num { background: #b4384a; color: #fff; }
.s-int .h-num { background: #c49102; color: #fff; }
.s-mon .h-num { background: #3b5ba5; color: #fff; }
.facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px 20px; margin: 0; }
.s-int .facts { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.facts dt { margin: 0 0 3px; font-size: 12.5px; color: #7a8a80; }
.facts dd { margin: 0; font-size: 15px; font-weight: 700; line-height: 1.4; color: #0e3a2c; overflow-wrap: anywhere; }
.facts dd.empty { color: #3e5046; }
.txt { margin: 16px 0 0; padding: 12px 14px; border-radius: 14px; background: #f7faf8; border-left: 3px solid #1f9d55; font-size: 14.5px; line-height: 1.6; color: #22362c; overflow-wrap: anywhere; white-space: pre-line; }
.k { display: block; margin-bottom: 3px; font-size: 12.5px; font-weight: 500; color: #7a8a80; }
.pes { margin: 0; font-size: 15px; line-height: 1.75; color: #22362c; }
.pes mark { padding: 2px 8px; border-radius: 8px; background: #fdedef; color: #8c1d2c; font-weight: 800; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
.pes.empty { color: #8a9a91; font-style: italic; }
.sig { display: flex; align-items: center; gap: 12px; margin: 6px 0 0; padding: 12px 14px; border-radius: 14px; background: #fffbea; border: 1px solid #f3e2a0; font-size: 13px; line-height: 1.5; color: #6b5a1e; }
.sig-ico { flex-shrink: 0; width: 36px; height: 36px; border-radius: 11px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }

/* ---------- footer ---------- */
.sum-foot { flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; padding: 14px 28px; border-top: 1px solid #eef2ef; background: #f7faf8; }
.foot-right { display: flex; gap: 8px; flex-wrap: wrap; }
.sum-foot .nm-btn-outline, .sum-foot .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 0 18px; border-radius: 12px; font-size: 14px; font-weight: 800; text-decoration: none; }
.sum-foot .nm-btn-outline { background: #fff; border: 1px solid #dce8e0; color: #004d3a; }
.sum-foot .nm-btn-outline:hover { background: #f1f6f2; }
.sum-foot .nm-btn-dark { background: #004d3a; border: 1px solid #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.sum-foot .nm-btn-dark:hover { background: #00382a; }
.pad { padding: 0 28px 12px; }

@media (max-width: 760px) {
  .s-int .facts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .sum { max-height: 100vh; height: 100%; border-radius: 0; }
  .sum-head { padding: 18px 16px; flex-wrap: wrap; gap: 12px; }
  .sum-av { width: 46px; height: 46px; font-size: 16px; }
  .sum-plate { width: 180px; height: 180px; right: -50px; }
  .sum-title { font-size: 21px; }
  .head-right { position: absolute; top: 16px; right: 16px; }
  .sum-head-txt { padding-right: 0; flex-basis: 100%; }
  .sum-body { padding: 14px 16px 18px; }
  .facts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sum-foot { padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); flex-direction: column-reverse; }
  .pad { padding: 0 16px 12px; }
  .sum-foot > *, .foot-right, .foot-right > * { width: 100%; justify-content: center; text-align: center; }
}
</style>
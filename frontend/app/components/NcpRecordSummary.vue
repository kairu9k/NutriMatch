<template>
  <div class="nm-modal-overlay" @click.self="emit('close')">
    <div class="sum" role="dialog" aria-modal="true" aria-labelledby="sum-title">
      <header class="sum-head">
        <div>
          <p class="kind">{{ row.is_follow_up ? `Follow-up #${row.follow_up_no}` : 'Initial record' }}, {{ shortDate(row.encounter_date) }}</p>
          <h2 id="sum-title" class="sum-title">{{ row.patient.name }}</h2>
          <p class="sub">{{ patientLine }}</p>
        </div>
        <div class="head-right">
          <span class="nm-pill" :class="row.status === 'completed' ? 'green' : 'gold'">{{ row.status === 'completed' ? 'Finalized' : 'Draft' }}</span>
          <button type="button" class="icon-x" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
        </div>
      </header>

      <div class="sum-body">
        <p v-if="loading" class="nm-muted">Loading record…</p>
        <p v-else-if="error" class="nm-error">{{ error }}</p>
        <template v-else-if="r">
          <p v-if="row.appointment" class="linked"><CalendarCheck :size="14" /> Written for the {{ row.appointment.type_label.toLowerCase() }} consultation on {{ longWhen(row.appointment.scheduled_at) }}</p>
          <p v-if="row.status === 'draft'" class="draft-note"><PenLine :size="14" aria-hidden="true" /> Unfinished. It still needs {{ row.missing.join(', ') || 'a final check' }}.</p>

          <section>
            <h3>1. Assessment</h3>
            <dl class="facts">
              <div v-for="[k, v] in assessment" :key="k"><dt>{{ k }}</dt><dd>{{ v }}</dd></div>
            </dl>
            <p v-if="r.lab_notes" class="txt"><span class="k">Lab notes</span>{{ r.lab_notes }}</p>
            <p v-if="r.assessment_notes" class="txt"><span class="k">Assessment notes</span>{{ r.assessment_notes }}</p>
          </section>

          <section>
            <h3>2. Diagnosis</h3>
            <p class="pes">{{ pes || 'Not written yet.' }}</p>
          </section>

          <section>
            <h3>3. Intervention</h3>
            <dl class="facts">
              <div v-for="[k, v] in intervention" :key="k"><dt>{{ k }}</dt><dd>{{ v }}</dd></div>
            </dl>
            <p v-if="r.diet_prescription" class="txt"><span class="k">Diet prescription</span>{{ r.diet_prescription }}</p>
            <p v-if="r.intervention_notes" class="txt"><span class="k">Intervention notes</span>{{ r.intervention_notes }}</p>
          </section>

          <section v-if="row.is_follow_up || r.goal_status || r.monitoring_notes">
            <h3>4. Monitoring &amp; evaluation</h3>
            <dl class="facts">
              <div><dt>Goal status</dt><dd>{{ GOALS[r.goal_status] || '—' }}</dd></div>
            </dl>
            <p v-if="r.monitoring_notes" class="txt"><span class="k">Monitoring notes</span>{{ r.monitoring_notes }}</p>
          </section>

          <p class="sig">By {{ rnd.name }}{{ rnd.prc_license_number ? `, RND, PRC No. ${rnd.prc_license_number}` : '' }}. {{ row.status === 'completed' ? `Finalized ${dateTime(r.updated_at)}` : `Last edited ${dateTime(r.updated_at)}` }}.</p>
        </template>
      </div>

      <footer class="sum-foot">
        <NuxtLink :to="`/client-detail/${row.relationship_id}?tab=ncp`" class="nm-btn-outline" @click="emit('close')">Open patient chart</NuxtLink>
        <div class="foot-right">
          <NuxtLink v-if="row.status === 'draft' && row.relationship_status === 'active'" :to="`/client-detail/${row.relationship_id}?tab=ncp&open=draft`" class="nm-btn-dark" @click="emit('close')">Continue in chart</NuxtLink>
          <button v-if="row.status === 'completed' && r" type="button" class="nm-btn-dark" @click="print"><Printer :size="14" /> Print / PDF</button>
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
</script>

<style scoped>
.sum { background: #fff; border-radius: 18px; width: 100%; max-width: 720px; max-height: 92dvh; display: flex; flex-direction: column; font-family: 'Inter', sans-serif; color: #1a3a1a; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22); overflow: hidden; }
.sum-head { display: flex; justify-content: space-between; gap: 12px; padding: 24px 26px 16px; border-bottom: 1px solid #d9e3dc; }
.kind { font-size: 0.82rem; font-weight: 700; color: #a07400; margin: 0 0 2px; }
.sum-title { font-family: 'Playfair Display', serif; font-size: 1.35rem; margin: 0; font-weight: 700; line-height: 1.2; }
.sub { font-size: 0.8rem; color: #8a9a8a; margin: 2px 0 0; }
.head-right { display: flex; align-items: flex-start; gap: 8px; }
.icon-x { border: none; background: none; color: #6a7a6a; cursor: pointer; border-radius: 6px; display: flex; }
.icon-x:hover { background: #f2f5f2; }
.sum-body { padding: 16px 22px 20px; overflow-y: auto; }
.linked, .draft-note { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; margin: 0 0 12px; padding: 8px 10px; border-radius: 8px; }
.linked { background: #f3f8f4; color: #2f5f3f; }
.draft-note { background: #fff; border: 1.5px dashed #3f9a6b; border-radius: 10px; color: #1f4a30; }
.draft-note svg { flex-shrink: 0; color: #3f9a6b; }
section { padding: 12px 0; border-top: 1px solid #f0f2f0; }
section:first-of-type { border-top: none; }
h3 { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0 0 8px; }
.facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px 14px; margin: 0; }
.facts dt { font-size: 0.7rem; color: #8a9a8a; margin: 0; }
.facts dd { margin: 0; font-size: 0.86rem; font-weight: 600; overflow-wrap: anywhere; }
.txt { font-size: 0.84rem; line-height: 1.55; margin: 10px 0 0; overflow-wrap: anywhere; white-space: pre-line; }
.k { display: block; font-size: 0.76rem; font-weight: 500; color: #7a8a7a; margin-bottom: 2px; }
.pes { font-size: 0.9rem; line-height: 1.55; margin: 0; }
.sig { font-size: 0.76rem; color: #8a9a8a; margin: 12px 0 0; border-top: 1px solid #f0f2f0; padding-top: 10px; }
.sum-foot { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; padding: 14px 26px; border-top: 1px solid #d9e3dc; background: #f7faf8; }
.foot-right { display: flex; gap: 8px; flex-wrap: wrap; }
.foot-right .nm-btn-dark { display: inline-flex; align-items: center; gap: 6px; }
.pad { padding: 0 26px 12px; }
@media (max-width: 560px) {
  .sum-head { padding: 18px 16px 14px; }
  .sum-title { font-size: 1.15rem; }
  .sum-foot { padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); }
  .pad { padding: 0 16px 12px; }
  .sum { max-height: 100vh; height: 100%; border-radius: 0; }
  .facts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sum-foot { flex-direction: column-reverse; }
  .sum-foot > *, .foot-right, .foot-right > * { width: 100%; justify-content: center; text-align: center; }
}
</style>

<template>
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="emit('close')">
      <div class="cs" role="dialog" aria-modal="true" aria-labelledby="cs-title">
        <header class="cs-head">
          <div>
            <p class="kind">Consultation summary</p>
            <h2 id="cs-title" class="cs-title">{{ s ? longWhen(s.appointment.scheduled_at) : 'Loading…' }}</h2>
            <p v-if="s" class="sub">{{ s.appointment.type_label }} · {{ s.appointment.duration_minutes }} min · {{ role === 'client' ? `with ${s.rnd.name}, RND` : s.client.name }}</p>
          </div>
          <button type="button" class="icon-x" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
        </header>

        <div class="cs-body">
          <p v-if="error" class="nm-error">{{ error }}</p>
          <p v-else-if="!s" class="nm-muted">Loading summary…</p>
          <template v-else>
            <p v-if="s.ncp_pending" class="note"><Clock :size="14" /> {{ s.rnd.name.split(' ')[0] }} is still finishing your care plan from this visit — it will show here once it's finalized.</p>
            <p v-else-if="role === 'rnd' && s.care_plan?.status === 'draft'" class="note"><AlertTriangle :size="14" /> This visit's NCP record is still a draft — the client won't see the diagnosis or plan until you finalize it.</p>
            <p v-else-if="role === 'rnd' && s.no_ncp" class="note"><AlertTriangle :size="14" /> No NCP record is linked to this visit, so only the measurements show.</p>

            <section>
              <h3>Measurements</h3>
              <template v-if="s.measurements">
                <div class="stats">
                  <div v-if="s.measurements.weight_kg != null"><span>Weight</span><strong>{{ fmt(s.measurements.weight_kg) }} kg</strong>
                    <small v-if="s.weight_change">{{ signed(s.weight_change.kg) }} kg since {{ shortDate(s.weight_change.since) }}</small></div>
                  <div v-if="s.measurements.bmi != null"><span>BMI</span><strong>{{ fmt(s.measurements.bmi) }}</strong><small>{{ s.measurements.bmi_class }}</small></div>
                  <div v-if="s.measurements.blood_pressure"><span>Blood pressure</span><strong>{{ s.measurements.blood_pressure }}</strong><small>mmHg</small></div>
                  <div v-if="s.measurements.blood_glucose != null"><span>Fasting glucose</span><strong>{{ Math.round(s.measurements.blood_glucose) }}</strong><small>mg/dL</small></div>
                  <div v-if="s.measurements.hba1c != null"><span>HbA1c</span><strong>{{ fmt(s.measurements.hba1c) }}%</strong></div>
                  <div v-for="o in s.measurements.other" :key="o.label"><span>{{ o.label }}</span><strong>{{ o.value }}</strong><small>{{ o.unit }}</small></div>
                </div>
                <p class="src">From {{ s.measurements_source }}.</p>
              </template>
              <p v-else class="nm-muted">No measurements were recorded for this visit.</p>
            </section>

            <template v-if="s.care_plan">
              <section v-if="s.care_plan.pes_problem">
                <h3>What we found</h3>
                <p class="txt"><strong>{{ s.care_plan.pes_problem }}</strong><template v-if="s.care_plan.pes_etiology"> related to {{ s.care_plan.pes_etiology }}</template><template v-if="s.care_plan.pes_signs">, as shown by {{ s.care_plan.pes_signs }}</template>.</p>
              </section>
              <section>
                <h3>Your plan</h3>
                <p v-if="s.care_plan.diet_prescription" class="txt">{{ s.care_plan.diet_prescription }}</p>
                <div v-if="s.care_plan.target_kcal" class="targets">
                  <div><strong>{{ whole(s.care_plan.target_kcal) }}</strong><span>kcal a day</span></div>
                  <div v-if="s.care_plan.target_carb_g"><strong>{{ whole(s.care_plan.target_carb_g) }} g</strong><span>carbs</span></div>
                  <div v-if="s.care_plan.target_protein_g"><strong>{{ whole(s.care_plan.target_protein_g) }} g</strong><span>protein</span></div>
                  <div v-if="s.care_plan.target_fat_g"><strong>{{ whole(s.care_plan.target_fat_g) }} g</strong><span>fat</span></div>
                </div>
                <ul v-if="s.care_plan.other_targets.length" class="list">
                  <li v-for="t in s.care_plan.other_targets" :key="t.label">{{ t.label }}: {{ t.value }} {{ t.unit }}</li>
                </ul>
                <p v-if="s.care_plan.advice" class="txt advice"><span class="k">Advice</span>{{ s.care_plan.advice }}</p>
                <p v-if="s.care_plan.goal_status" class="txt"><span class="k">Goals from your last visit</span>{{ s.care_plan.goal_status }}</p>
              </section>
              <section v-if="role === 'rnd' && (s.care_plan.assessment_notes || s.care_plan.lab_notes || s.care_plan.monitoring_notes)" class="private">
                <h3><Lock :size="12" /> Clinical notes (only you see these)</h3>
                <p v-if="s.care_plan.assessment_notes" class="txt"><span class="k">Assessment</span>{{ s.care_plan.assessment_notes }}</p>
                <p v-if="s.care_plan.lab_notes" class="txt"><span class="k">Labs</span>{{ s.care_plan.lab_notes }}</p>
                <p v-if="s.care_plan.monitoring_notes" class="txt"><span class="k">Monitoring</span>{{ s.care_plan.monitoring_notes }}</p>
              </section>
            </template>

            <section>
              <h3>Next steps</h3>
              <ul class="list">
                <li v-if="s.meal_plan">Meal plan: <strong>{{ s.meal_plan.name }}</strong>{{ s.meal_plan.target_kcal ? ` (${whole(s.meal_plan.target_kcal)} kcal a day)` : '' }}{{ role === 'client' ? ' — log your meals in My Meal Plan.' : '' }}</li>
                <li v-if="s.next_appointment">Next consultation: <strong>{{ longWhen(s.next_appointment.scheduled_at) }}</strong> ({{ s.next_appointment.type_label }}{{ s.next_appointment.status === 'pending' ? ', waiting for confirmation' : '' }})</li>
                <li v-else>{{ role === 'client' ? 'No follow-up booked yet — book one from Find an RND or My Appointments.' : 'No follow-up booked yet.' }}</li>
              </ul>
            </section>

            <p class="sig">{{ s.rnd.name }}, RND{{ s.rnd.prc_license_number ? ` · PRC No. ${s.rnd.prc_license_number}` : '' }}</p>
          </template>
        </div>

        <footer class="cs-foot">
          <p v-if="printError" class="nm-field-error">{{ printError }}</p>
          <button type="button" class="nm-btn-outline" @click="emit('close')">Close</button>
          <button v-if="s" type="button" class="nm-btn-dark" @click="print"><Printer :size="14" /> Print / PDF</button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
// The summary of one completed consultation — the client's version (finalized
// NCP content only, no RND-only notes) or the RND's (drafts flagged, clinical
// notes included). Built live by scheduling/consultation_summary.py.
import { AlertTriangle, Clock, Lock, Printer, X } from 'lucide-vue-next'

const props = defineProps({
  appointmentId: { type: [String, Number], required: true },
  role: { type: String, default: 'client' }, // 'client' | 'rnd'
})
const emit = defineEmits(['close'])
const { get } = useApi()

const s = ref(null)
const error = ref('')
const printError = ref('')
onMounted(async () => {
  try {
    s.value = await get(`/${props.role === 'rnd' ? 'rnd' : 'client'}/appointments/${props.appointmentId}/summary/`)
  } catch (e) {
    error.value = apiError(e, 'Could not load this summary.')
  }
})

const PH = { timeZone: 'Asia/Manila' }
const longWhen = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
const fmt = v => Number(v).toFixed(1).replace(/\.0$/, '')
const whole = v => Math.round(Number(v)).toLocaleString('en-PH')
const signed = v => `${Number(v) > 0 ? '+' : Number(v) < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)}`

function print() {
  const x = s.value
  const m = x.measurements
  const rows = []
  if (m) {
    if (m.weight_kg != null) rows.push(['Weight', `${fmt(m.weight_kg)} kg${x.weight_change ? ` (${signed(x.weight_change.kg)} kg since ${shortDate(x.weight_change.since)})` : ''}`])
    if (m.bmi != null) rows.push(['BMI', `${fmt(m.bmi)} · ${m.bmi_class}`])
    if (m.blood_pressure) rows.push(['Blood pressure', `${m.blood_pressure} mmHg`])
    if (m.blood_glucose != null) rows.push(['Fasting glucose', `${Math.round(m.blood_glucose)} mg/dL`])
    if (m.hba1c != null) rows.push(['HbA1c', `${fmt(m.hba1c)}%`])
    for (const o of m.other) rows.push([o.label, `${o.value} ${o.unit}`.trim()])
  }
  const sections = [{ heading: 'Measurements', rows, text: rows.length ? '' : 'No measurements were recorded for this visit.' }]
  const c = x.care_plan
  if (c) {
    if (c.pes_problem) sections.push({ heading: 'What we found', text: `${c.pes_problem}${c.pes_etiology ? ` related to ${c.pes_etiology}` : ''}${c.pes_signs ? `, as shown by ${c.pes_signs}` : ''}.` })
    const plan = []
    if (c.target_kcal) plan.push(['Energy', `${whole(c.target_kcal)} kcal a day`])
    if (c.target_carb_g) plan.push(['Carbohydrate / protein / fat', `${whole(c.target_carb_g)} g / ${whole(c.target_protein_g)} g / ${whole(c.target_fat_g)} g`])
    for (const t of c.other_targets) plan.push([t.label, `${t.value} ${t.unit}`.trim()])
    if (c.goal_status) plan.push(['Goals from the last visit', c.goal_status])
    sections.push({ heading: 'Plan', rows: plan, text: [c.diet_prescription, c.advice && `Advice: ${c.advice}`].filter(Boolean).join('\n') })
  } else if (x.ncp_pending) {
    sections.push({ heading: 'Plan', text: 'Your RND is still finishing your care plan from this visit.' })
  }
  const next = []
  if (x.meal_plan) next.push(`Meal plan: ${x.meal_plan.name}`)
  next.push(x.next_appointment ? `Next consultation: ${longWhen(x.next_appointment.scheduled_at)} (${x.next_appointment.type_label})` : 'No follow-up booked yet.')
  sections.push({ heading: 'Next steps', text: next.join('\n') })
  const ok = printDocument({
    title: 'Consultation summary',
    number: longWhen(x.appointment.scheduled_at),
    rows: [
      ['Client', x.client.name],
      ['Registered Nutritionist-Dietitian', `${x.rnd.name}${x.rnd.prc_license_number ? ` (PRC No. ${x.rnd.prc_license_number})` : ''}`],
      ['Consultation', `${x.appointment.type_label}, ${x.appointment.duration_minutes} minutes`],
    ],
    sections,
    foot: 'Confidential health information — handle according to the Data Privacy Act of 2012 (RA 10173). Generated by NutriMatch.',
  })
  printError.value = ok ? '' : 'Your browser blocked the print window — allow pop-ups for this site and try again.'
}
</script>

<style scoped>
.cs { background: #fff; border-radius: 16px; width: 100%; max-width: 640px; max-height: calc(100vh - 32px); display: flex; flex-direction: column; font-family: 'Inter', sans-serif; color: #1a3a1a; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2); overflow: hidden; }
.cs-head { display: flex; justify-content: space-between; gap: 12px; padding: 18px 22px 14px; border-bottom: 1px solid #f0f2f0; }
.kind { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #b8860b; margin: 0 0 2px; }
.cs-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; margin: 0; }
.sub { font-size: 0.8rem; color: #8a9a8a; margin: 2px 0 0; }
.icon-x { border: none; background: none; color: #6a7a6a; cursor: pointer; padding: 2px; border-radius: 6px; display: flex; align-self: flex-start; }
.cs-body { padding: 14px 22px 18px; overflow-y: auto; }
.note { display: flex; gap: 6px; align-items: flex-start; background: #fdf6e3; color: #7a5a00; border-radius: 8px; padding: 8px 10px; font-size: 0.8rem; margin: 0 0 10px; }
section { padding: 12px 0; border-top: 1px solid #f0f2f0; }
section:first-of-type { border-top: none; }
h3 { display: flex; align-items: center; gap: 5px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #6a7a6a; margin: 0 0 8px; }
.stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.stats div { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 9px 10px; display: flex; flex-direction: column; min-width: 0; }
.stats span { font-size: 0.68rem; color: #8a9a8a; }
.stats strong { font-size: 1rem; font-variant-numeric: tabular-nums; }
.stats small { font-size: 0.7rem; color: #8a9a8a; }
.src { font-size: 0.72rem; color: #9aaa9a; margin: 6px 0 0; }
.txt { font-size: 0.86rem; line-height: 1.55; margin: 0 0 8px; overflow-wrap: anywhere; }
.k { display: block; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; margin-bottom: 2px; }
.advice { background: #f3f8f4; border-radius: 8px; padding: 8px 10px; }
.targets { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 4px 0 8px; }
.targets div { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 8px 10px; display: flex; flex-direction: column; }
.targets strong { font-variant-numeric: tabular-nums; }
.targets span { font-size: 0.7rem; color: #8a9a8a; }
.list { margin: 0; padding-left: 18px; font-size: 0.84rem; line-height: 1.8; }
.private { background: #fafbfa; border-radius: 10px; padding: 10px 12px; margin-top: 8px; }
.sig { font-size: 0.76rem; color: #8a9a8a; margin: 10px 0 0; }
.cs-foot { display: flex; justify-content: flex-end; align-items: center; gap: 8px; flex-wrap: wrap; padding: 12px 22px; border-top: 1px solid #f0f2f0; }
.cs-foot .nm-field-error { flex-basis: 100%; margin: 0; text-align: right; }
.cs-foot .nm-btn-dark { display: inline-flex; align-items: center; gap: 6px; }
@media (max-width: 560px) {
  .cs { max-height: 100vh; height: 100%; border-radius: 0; }
  .stats, .targets { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>

<template>
  <div class="meal-planning-page">
    <!-- TOP CONTROLS (once a patient is chosen) -->
    <div v-if="selectedRelId && !isLoading" class="mp-top no-print">
      <button type="button" class="back-link" @click="backToList">
        <ChevronLeft :size="16" /> All patients
      </button>
      <div class="mode-toggle">
        <button class="mode-btn" :class="{ active: mode === 'view' }" :disabled="!patients.length" @click="showView">
          <Eye :size="16" /> View plan
        </button>
        <button class="mode-btn" :class="{ active: mode === 'create' }" :disabled="!patients.length" @click="openCreate">
          <component :is="selectedPlan ? Pencil : Plus" :size="16" /> {{ selectedPlan ? 'Edit plan' : 'Create plan' }}
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error no-print">{{ errorMessage }}</p>

    <div v-if="isLoading" class="mp-loading"><span class="mp-spin" aria-hidden="true"></span> Loading…</div>

    <div v-else-if="!patients.length" class="empty-state">
      <span class="empty-ico"><Utensils :size="24" /></span>
      <p class="empty-title">No active patients yet</p>
      <p class="empty-text">Meal plans can be created once a client's first appointment is confirmed.</p>
    </div>

    <!-- START: choose a patient (opening from the sidebar) -->
    <MealPlanPatientList v-else-if="!selectedRelId" class="no-print" @pick="pickPatient" />

    <!-- ================= VIEW PLANS MODE ================= -->
    <div v-else-if="mode === 'view' && !selectedPlan" class="empty-state">
      <span class="empty-ico"><Utensils :size="24" /></span>
      <p class="empty-title">No meal plan yet for {{ selectedPatientName }}</p>
      <button class="btn-primary" @click="startNewPlan"><Plus :size="15" /> Create meal plan</button>
    </div>

    <div v-else-if="mode === 'view'" class="mp-wrap">
      <section class="mp-hero no-print">
        <img class="mp-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="mp-hero-fade" aria-hidden="true"></span>
        <div class="mp-hero-who">
          <span class="mp-av" aria-hidden="true">{{ initials }}</span>
          <div class="mp-hero-txt">
            <p class="mp-eyebrow"><span></span>Weekly meal plan</p>
            <h2 class="mp-title">{{ selectedPatientName }}</h2>
            <p class="mp-sub">
              <span>{{ planMeta.name }}</span><i></i>
              <span class="mp-status" :class="'st-' + selectedPlan.status"><b></b>{{ statusLabel(selectedPlan.status) }}</span>
            </p>
          </div>
        </div>
        <div class="mp-targets">
          <div class="mp-t big"><small>Daily target</small><strong>{{ fmtNum(planMeta.kcalPerDay) }}</strong><em>kcal, {{ conditionLabel(planMeta.condition) }}</em></div>
          <div class="mp-t"><small><i style="background: #EFBF04"></i>Carbs</small><strong>{{ targets.carb ?? '—' }}</strong><em>g</em></div>
          <div class="mp-t"><small><i style="background: #6EE7A8"></i>Protein</small><strong>{{ targets.protein ?? '—' }}</strong><em>g</em></div>
          <div class="mp-t"><small><i style="background: #9DB4F0"></i>Fat</small><strong>{{ targets.fat ?? '—' }}</strong><em>g</em></div>
        </div>
        <div class="mp-hero-acts">
          <button class="mp-btn glass" type="button" @click="printPlan"><Printer :size="16" /> Print</button>
          <button class="mp-btn glass" type="button" @click="mode = 'create'"><Pencil :size="16" /> Edit</button>
          <button class="mp-btn gold" type="button" :disabled="isSending" @click="requestSend(sendToPatient)">
            <Send :size="16" /> {{ isSending ? 'Sending…' : selectedPlan.status === 'active' ? 'Resend to patient' : 'Send to patient' }}
          </button>
        </div>
      </section>

      <div class="planning-layout">
        <div class="mp-main">
          <div class="day-tabs no-print" role="tablist">
            <button
              v-for="day in days"
              :key="day"
              class="day-tab"
              :class="{ active: activeDay === day }"
              @click="activeDay = day"
            >
              {{ day }}
            </button>
          </div>

          <div class="panel plan-panel print-area">
            <div class="print-only print-head">
              <h3>Weekly meal plan for {{ selectedPatientName }}</h3>
              <p>{{ planMeta.name }}. {{ conditionLabel(planMeta.condition) }}<template v-if="planMeta.kcalPerDay">, {{ Number(planMeta.kcalPerDay).toLocaleString('en-PH') }} kcal/day</template></p>
            </div>

            <!-- Screen: selected day. Print: the whole week. -->
            <div v-for="day in printDays" :key="day" class="print-day" :class="{ 'screen-hidden': day !== activeDay }">
              <h4 class="print-only print-day-title">{{ DAY_FULL[day] }}</h4>
              <div class="mp-dayhead no-print">
                <h3>{{ DAY_FULL[day] }}</h3>
                <span>{{ mealCount(day) }} meals, {{ dayKcal(day).toLocaleString('en-PH') }} kcal</span>
              </div>
              <div class="meal-list">
                <!-- one small table per meal: food, portion, kcal and macros in lined-up columns -->
                <section v-for="meal in mealsForDay(day)" :key="meal.type" class="meal-block" :style="toneStyle(meal.type)">
                  <div class="meal-head">
                    <span class="meal-ico no-print"><component :is="meal.icon" :size="18" /></span>
                    <h4 class="meal-name">{{ sentence(meal.type) }}</h4>
                    <span v-if="meal.time" class="meal-time">
                      <svg class="ic" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
                      {{ formatTime(meal.time) }}
                    </span>
                  </div>
                  <div v-if="meal.foods.length" class="meal-tw">
                    <table class="meal-foods">
                      <thead>
                        <tr><th>Food</th><th>Portion</th><th class="n">kcal</th><th class="n c">Carbs</th><th class="n p">Protein</th><th class="n f">Fat</th></tr>
                      </thead>
                      <tbody>
                        <tr v-for="(f, i) in meal.foods" :key="i">
                          <td class="food">{{ f.name }}</td>
                          <td class="portion">{{ f.portion || '' }}</td>
                          <td class="n k">{{ cell(f.kcal) }}</td>
                          <td class="n">{{ cell(f.carb) }} g</td>
                          <td class="n">{{ cell(f.prot) }} g</td>
                          <td class="n">{{ cell(f.fat) }} g</td>
                        </tr>
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colspan="2">Meal total</td>
                          <td class="n k">{{ meal.kcal }}</td>
                          <td class="n">{{ mealTotal(meal, 'carb') }} g</td>
                          <td class="n">{{ mealTotal(meal, 'prot') }} g</td>
                          <td class="n">{{ mealTotal(meal, 'fat') }} g</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <p v-else class="meal-empty">No foods added</p>
                </section>
              </div>
            </div>

            <div v-if="instructions.allergies || instructions.notes" class="instructions-view print-only">
              <p v-if="instructions.allergies"><strong>Allergies and restrictions:</strong> {{ instructions.allergies }}</p>
              <p v-if="instructions.notes"><strong>Notes from the RND:</strong> {{ instructions.notes }}</p>
            </div>

            <div v-if="selectedPlan.status === 'draft'" class="plan-foot no-print">
              <p><Lock :size="14" /> Draft. Only you can see it, and you can still delete it.</p>
              <button class="btn-danger" type="button" @click="confirmDelete = true"><Trash2 :size="15" /> Delete draft</button>
            </div>
          </div>
        </div>

        <!-- RIGHT SIDEBAR -->
        <div class="side-column no-print">
          <div class="panel">
            <div class="side-head">
              <span class="side-ico ico-blue"><svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20V11M10 20V5M16 20v-6M21 20H3" /></svg></span>
              <div class="side-head-txt">
                <h4 class="side-title">{{ DAY_FULL[activeDay] }}'s totals</h4>
                <span class="side-subtitle">Against the plan's daily targets</span>
              </div>
            </div>
            <div class="mp-ring-row">
              <div class="mp-ring" :style="{ '--p': pct(nutrition.calories) }">
                <span><strong>{{ Number(nutrition.calories.value).toLocaleString('en-PH') }}</strong><small>of {{ nutrition.calories.target != null ? Number(nutrition.calories.target).toLocaleString('en-PH') : '—' }} kcal</small></span>
              </div>
              <div v-if="dayNote" class="mp-ring-note">
                <span class="mp-ok" :class="{ off: !dayNote.ok }">{{ dayNote.label }}</span>
                <p>{{ dayNote.text }}</p>
              </div>
            </div>
            <div class="nutrient-row">
              <div class="nutrient-top"><span><i class="dot" style="background: #C49102"></i>Carbohydrates</span><span><strong>{{ nutrition.carbs.value }} g</strong> / {{ nutrition.carbs.target ?? '—' }} g</span></div>
              <div class="nutrient-bar"><div class="nutrient-fill fill-gold" :style="{ width: pct(nutrition.carbs) + '%' }"></div></div>
            </div>
            <div class="nutrient-row">
              <div class="nutrient-top"><span><i class="dot" style="background: #1F9D55"></i>Protein</span><span><strong>{{ nutrition.protein.value }} g</strong> / {{ nutrition.protein.target ?? '—' }} g</span></div>
              <div class="nutrient-bar"><div class="nutrient-fill fill-green" :style="{ width: pct(nutrition.protein) + '%' }"></div></div>
            </div>
            <div class="nutrient-row">
              <div class="nutrient-top"><span><i class="dot" style="background: #3B5BA5"></i>Fat</span><span><strong>{{ nutrition.fat.value }} g</strong> / {{ nutrition.fat.target ?? '—' }} g</span></div>
              <div class="nutrient-bar"><div class="nutrient-fill fill-blue" :style="{ width: pct(nutrition.fat) + '%' }"></div></div>
            </div>
            <p class="exchange-note">FNRI values from the Food Exchange Lists, 4th ed., 2020</p>
          </div>

          <!-- same panel as in Edit plan, read-only here -->
          <div class="panel">
            <div class="side-head">
              <span class="side-ico ico-gold"><svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg></span>
              <div class="side-head-txt"><h4 class="side-title">Instructions for the patient</h4></div>
              <button class="nm-btn-soft nm-btn-sm" type="button" @click="mode = 'create'"><Pencil :size="13" aria-hidden="true" /> Edit</button>
            </div>
            <p v-if="patientAllergies.length" class="instr-allergy" role="note">
              <AlertTriangle :size="15" aria-hidden="true" /> <span>{{ patientFirstName }}'s recorded allergies: {{ patientAllergies.join(', ') }}</span>
            </p>
            <dl class="instr-read">
              <dt>Allergies and restrictions</dt>
              <dd :class="{ empty: !instructions.allergies }">{{ instructions.allergies || 'None written' }}</dd>
              <dt>Notes for the patient</dt>
              <dd :class="{ empty: !instructions.notes }">{{ instructions.notes || 'None written' }}</dd>
            </dl>
          </div>

          <div class="panel">
            <div class="side-head">
              <span class="side-ico ico-green"><svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg></span>
              <div class="side-head-txt"><h4 class="side-title">Plans for this patient</h4></div>
              <button class="nm-btn-soft nm-btn-sm" type="button" @click="startNewPlan"><Plus :size="13" aria-hidden="true" /> New plan</button>
            </div>
            <button
              v-for="p in plans"
              :key="p.id"
              class="saved-plan-card"
              :class="{ selected: p.id === selectedPlanId }"
              @click="selectPlan(p.id)"
            >
              <div>
                <div class="saved-plan-name">{{ p.name }}</div>
                <div class="saved-plan-meta">{{ conditionLabel(p.condition) }}<template v-if="p.target_kcal">, {{ Math.round(p.target_kcal).toLocaleString('en-PH') }} kcal/day</template></div>
              </div>
              <span class="active-pill" :class="'pill-' + p.status">{{ { draft: 'Draft', active: 'Sent', archived: 'Archived' }[p.status] || p.status }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ================= CREATE / EDIT PLAN MODE ================= -->
    <div v-else class="mp-wrap">
      <section class="mp-hero no-print" :aria-label="`${patientFirstName}'s measurements`">
        <img class="mp-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="mp-hero-fade" aria-hidden="true"></span>
        <div class="mp-hero-who">
          <span class="mp-av" aria-hidden="true">{{ initials }}</span>
          <div class="mp-hero-txt">
            <p class="mp-eyebrow"><span></span>{{ selectedPlan ? 'Editing meal plan' : 'New meal plan' }}</p>
            <h2 class="mp-title">{{ selectedPatientName }}</h2>
            <!-- The patient's age, sex and latest measurements, for setting the targets -->
            <p v-if="bodyParts.length" class="mp-sub">
              <template v-for="(part, i) in bodyParts" :key="i"><i v-if="i"></i><span>{{ part }}</span></template>
            </p>
            <p v-if="patientBody?.source" class="mp-src">{{ patientBody.source }}</p>
          </div>
        </div>
        <div class="mp-targets">
          <div class="mp-t big"><small>TER</small><strong>{{ fmtNum(planMeta.kcalPerDay) }}</strong><em>kcal/day</em></div>
          <div class="mp-t"><small><i style="background: #EFBF04"></i>Carbs</small><strong>{{ targets.carb ?? '—' }}</strong><em>g</em></div>
          <div class="mp-t"><small><i style="background: #6EE7A8"></i>Protein</small><strong>{{ targets.protein ?? '—' }}</strong><em>g</em></div>
          <div class="mp-t"><small><i style="background: #9DB4F0"></i>Fat</small><strong>{{ targets.fat ?? '—' }}</strong><em>g</em></div>
        </div>
        <div v-if="selectedPlan" class="mp-hero-acts edit">
          <button class="mp-btn glass" type="button" :disabled="!canUndo" title="Undo your last change (Ctrl+Z)" @click="undo"><Undo2 :size="16" /> Undo</button>
          <button class="mp-btn glass" type="button" :disabled="isSaving" @click="savePlan()">
            <svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h11l5 5v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z" /><path d="M7 3v6h8M7 21v-7h10v7" /></svg>
            {{ isSaving ? 'Saving…' : selectedPlan.status === 'draft' ? 'Save draft' : 'Save changes' }}
          </button>
          <button class="mp-btn gold" type="button" :disabled="isSaving || isSending" @click="requestSend(saveAndSend)"><Send :size="16" /> Save &amp; send to patient</button>
        </div>
      </section>

      <div v-if="selectedPlan" class="mp-note no-print" :class="{ sent: selectedPlan.status !== 'draft' }">
        <span class="mp-note-ico"><Lock :size="16" /></span>
        <p v-if="selectedPlan.status !== 'draft'" class="sent-lock">Sent to the client, so this plan can't be deleted. Edit it and resend, or send a new plan.</p>
        <p v-else class="sent-lock"><strong>Draft.</strong> Only you can see it, and you can still delete it. Once you send it to the client, it can't be deleted.</p>
        <div class="mp-note-acts">
          <button class="mp-ghost" type="button" @click="discardChanges">Discard changes</button>
          <button v-if="selectedPlan.status === 'draft'" class="btn-danger" type="button" @click="confirmDelete = true"><Trash2 :size="15" /> Delete draft</button>
        </div>
      </div>

      <div class="planning-layout">
        <div class="create-column">
          <!-- NEW PLAN: pick how to start first, so the two forms never sit on top of each other -->
          <div v-if="!selectedPlan" class="panel start-choice">
            <h4 class="no-plan-title">New meal plan for {{ selectedPatientName }}</h4>
            <div class="start-options" role="radiogroup" aria-label="How to start the plan">
              <button type="button" role="radio" class="start-opt" :class="{ on: startWith === 'template' }" :aria-checked="startWith === 'template'" @click="startWith = 'template'">
                <span class="start-ico"><Utensils :size="18" /></span>
                <span class="start-name">Start from a diet template <span class="start-rec">Recommended</span></span>
                <span class="start-desc">Pick the condition and calories. A full week is filled in for you to check and adjust.</span>
              </button>
              <button type="button" role="radio" class="start-opt" :class="{ on: startWith === 'blank' }" :aria-checked="startWith === 'blank'" @click="startWith = 'blank'">
                <span class="start-ico"><Plus :size="18" /></span>
                <span class="start-name">Start blank</span>
                <span class="start-desc">Name the plan and set the calories, then add every meal yourself.</span>
              </button>
            </div>
          </div>

          <!-- disease-specific diet template (diabetes, hypertension, renal, weight management) -->
          <MealPlanTemplatePicker v-if="!selectedPlan && startWith === 'template'" :relationship-id="selectedRelId" @created="onTemplateCreated" />

          <!-- STEP 1: PLAN DETAILS (a new blank plan, or the plan being edited) -->
          <div v-if="selectedPlan || startWith === 'blank'" class="panel">
            <div class="side-head">
              <span class="side-ico ico-green"><svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg></span>
              <div class="side-head-txt">
                <h4 class="side-title">Plan details</h4>
                <span class="side-subtitle">Name, condition and the daily calorie target</span>
              </div>
            </div>
            <p v-if="!selectedPlan && ncpTargets" class="prefill-note">Targets are filled in from this client's NCP Intervention. Adjust them if needed.</p>

            <div class="form-row-6">
              <div class="field">
                <label>Plan name</label>
                <input v-model="planMeta.name" type="text" placeholder="e.g., Diabetic-Friendly Plan" :class="{ invalid: nameMissing && !planMeta.name.trim() }" :aria-invalid="(nameMissing && !planMeta.name.trim()) || undefined" />
              </div>
              <div class="field">
                <label>Condition</label>
                <select class="nm-select" v-model="planMeta.condition">
                  <option v-for="c in CONDITIONS" :key="c.value" :value="c.value">{{ c.label }}</option>
                </select>
              </div>
              <div class="field">
                <label>TER (Total Energy Requirement)</label>
                <div class="unit-in">
                  <input v-model.number="planMeta.kcalPerDay" type="number" min="0" placeholder="e.g., 1800" aria-label="TER (Total Energy Requirement), kcal/day" />
                  <span>kcal/day</span>
                </div>
              </div>
            </div>

            <!-- Targets beyond calories, as Measured Variable / Value / Unit rows
                 (same pattern as the NCP form's "+ Add Field"), in two groups:
                 the macronutrients (the only ones that give calories; in grams
                 they drive the Macro Tracker) and other targets (sodium, fiber…),
                 which are not part of the calorie target. -->
            <div class="targets-section">
              <div class="targets-header">
                <span class="targets-title">Macronutrient targets <span class="optional">optional</span></span>
              </div>
              <p class="targets-hint">Protein, carbohydrate and fat are the only nutrients that give calories (4 / 4 / 9 kcal per gram), so they make up the calorie target.</p>
              <!-- Fixed rows: only the value is edited (the Macro Tracker reads them by name, in grams). -->
              <div class="mp-macros">
                <div v-for="row in macroRows" :key="row.label" class="mp-macro" :style="{ '--c': MACRO_COLORS[row.label] || '#004D3A' }">
                  <span class="mp-macro-l"><i></i>{{ row.label }}</span>
                  <div class="unit-in">
                    <input v-model="row.value" type="text" inputmode="decimal" placeholder="Value" maxlength="100" :aria-label="`${row.label} value`" />
                    <span>{{ row.unit }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="targets-section">
              <div class="targets-header">
                <span class="targets-title">Other targets <span class="optional">optional</span></span>
                <button type="button" class="targets-add-btn" @click="addTargetRow"><Plus :size="14" /> Add target</button>
              </div>
              <p class="targets-hint">Not counted in the calorie target, e.g. sodium, fiber, potassium, vitamins. Pick from the list or type your own.</p>
              <div v-for="(row, idx) in otherRows" :key="idx" class="targets-row">
                <MeasureNameCombo :row="row" :templates="MEASURE_TEMPLATES.intervention" :aria-label="`Target ${idx + 1} name`" />
                <input v-model="row.value" type="text" inputmode="decimal" placeholder="Value" maxlength="100" :aria-label="`Target ${idx + 1} value`" />
                <input v-model="row.unit" type="text" placeholder="Unit" maxlength="30" :aria-label="`Target ${idx + 1} unit`" />
                <button type="button" class="targets-remove-btn" title="Remove" aria-label="Remove target" @click="otherRows.splice(idx, 1)"><Trash2 :size="15" /></button>
              </div>
            </div>

            <button v-if="!selectedPlan" class="btn-primary create-btn" :disabled="!planMeta.name || !planMeta.kcalPerDay || isSaving" @click="createPlan">
              {{ isSaving ? 'Creating…' : 'Create meal plan' }}
            </button>
            <p v-if="!selectedPlan && createBlocker" class="create-hint">{{ createBlocker }} Then you can add the meals day by day.</p>
          </div>

          <!-- STEP 2: DAILY MEALS — only once the plan exists -->
          <template v-if="selectedPlan">
            <div class="day-row">
              <div class="day-tabs" role="tablist">
                <button
                  v-for="day in days"
                  :key="day"
                  class="day-tab"
                  :class="{ active: activeDay === day }"
                  @click="activeDay = day"
                >
                  {{ day }}<span v-if="warningDays.has(day)" class="day-warn-dot" title="A food on this day may not suit the patient's condition" />
                </button>
              </div>

              <div class="copy-day">
                <label for="copy-to">Copy {{ DAY_FULL[activeDay] }}'s meals to</label>
                <select id="copy-to" v-model="copyTarget" class="nm-select">
                  <option value="">Pick days</option>
                  <option value="all">Every other day</option>
                  <option value="weekdays">Monday to Friday</option>
                  <option value="weekend">Saturday and Sunday</option>
                  <option v-for="d in days.filter(x => x !== activeDay)" :key="d" :value="d">{{ DAY_FULL[d] }}</option>
                </select>
                <button type="button" class="btn-secondary" :disabled="!copyTarget || !dayHasFood(activeDay)" @click="copyDay">
                  <svg class="ic" viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></svg>
                  Copy
                </button>
              </div>
            </div>
            <p v-if="!dayHasFood(activeDay)" class="copy-hint">Add food to {{ DAY_FULL[activeDay] }} first to copy it to other days.</p>

            <div class="panel meals-panel">
              <div class="mp-dayhead">
                <h3>{{ DAY_FULL[activeDay] }}</h3>
                <span>{{ mealCount(activeDay) }} meals, {{ dayTotal('kcal').toLocaleString('en-PH') }} kcal</span>
              </div>

              <section class="meal-edit-panel" v-for="meal in currentDayMeals" :key="meal.type" :style="toneStyle(meal.type)">
                <div class="meal-edit-header">
                  <span class="meal-ico"><component :is="meal.icon" :size="18" /></span>
                  <span class="meal-edit-label">{{ sentence(meal.type) }}</span>
                  <label class="meal-time-pill">
                    <svg class="ic" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
                    <input v-model="weeklyPlan[activeDay][meal.type].time" type="time" class="meal-time-input" title="Meal time" />
                  </label>
                </div>

                <div class="food-table">
                  <div v-if="meal.items.length" class="food-table-head">
                    <span>Food</span>
                    <span>Portion</span>
                    <span class="n">kcal</span>
                    <span class="n c">Carbs (g)</span>
                    <span class="n p">Protein (g)</span>
                    <span class="n f">Fat (g)</span>
                    <span></span>
                  </div>
                  <p v-else class="meal-empty">No foods yet. Add one below.</p>
                  <div class="food-table-row" v-for="(item, idx) in meal.items" :key="idx" :class="{ usda: item.source === 'usda' }">
                    <template v-if="item.source === 'usda'">
                      <div class="usda-name" :title="`USDA FoodData Central #${item.fdcId}`"><span class="usda-tag">USDA</span>{{ item.name }}</div>
                      <div class="grams-input">
                        <input :value="item.grams" type="number" min="1" max="2000" step="1" aria-label="Grams" @input="setGrams(item, $event.target.value)" />
                        <span>g</span>
                      </div>
                      <label class="mp-num k" data-l="kcal"><input :value="item.kcal ?? ''" type="number" disabled placeholder="—" title="From USDA, per the grams" /></label>
                      <label class="mp-num" data-l="Carbs"><input :value="item.carb ?? ''" type="number" disabled placeholder="—" /></label>
                      <label class="mp-num" data-l="Protein"><input :value="item.prot ?? ''" type="number" disabled placeholder="—" /></label>
                      <label class="mp-num" data-l="Fat"><input :value="item.fat ?? ''" type="number" disabled placeholder="—" /></label>
                    </template>
                    <template v-else>
                      <div class="combo" @keydown.down.prevent="moveFood(1)" @keydown.up.prevent="moveFood(-1)" @keydown.enter="pickActiveFood(item, $event)" @keydown.esc="foodPick.key = null">
                        <input
                          v-model="item.name"
                          type="text"
                          placeholder="Search FNRI or type a food"
                          role="combobox" autocomplete="off" aria-label="Food item"
                          :aria-expanded="foodPick.key === `${activeDay}-${meal.type}-${idx}`"
                          @focus="openFoodPick(`${activeDay}-${meal.type}-${idx}`, item.name)"
                          @input="onFoodNameInput(item, $event.target.value, `${activeDay}-${meal.type}-${idx}`)"
                          @change="applyFnriMatch(item, $event.target.value)"
                          @blur="closeFoodPickSoon"
                        />
                        <div v-if="foodPick.key === `${activeDay}-${meal.type}-${idx}` && flatFoodMatches.length" class="combo-list" role="listbox">
                          <template v-for="g in foodMatches" :key="g.group">
                            <p class="combo-group">{{ g.group }}</p>
                            <button v-for="f in g.foods" :key="f.id" type="button" role="option" class="combo-opt"
                                    :class="{ on: flatFoodMatches[foodPick.active]?.id === f.id }" :aria-selected="flatFoodMatches[foodPick.active]?.id === f.id"
                                    @mousedown.prevent="pickFood(item, f)">
                              <span class="combo-name">{{ f.name }}<span v-if="allergyWarnings(f.name, patientAllergies).length" class="combo-allergy">Allergy</span></span>
                              <span class="combo-meta">{{ f.household_measure || '1 exchange' }}</span>
                            </button>
                          </template>
                        </div>
                      </div>
                      <!-- An FNRI food is measured in exchanges: its numbers follow the
                           count (like grams for USDA). A typed food keeps free numbers. -->
                      <template v-if="item.foodItemId && fnriById[item.foodItemId]">
                        <div class="grams-input exch-input" :title="`1 exchange = ${fnriById[item.foodItemId].household_measure || 'one FNRI exchange'}`">
                          <input :value="item.exchanges" type="number" min="0.5" max="20" step="0.5" aria-label="Exchanges" @input="setExchanges(item, $event.target.value)" />
                          <span>{{ item.portion || 'exch.' }}</span>
                        </div>
                        <label class="mp-num k" data-l="kcal"><input :value="item.kcal ?? ''" type="number" disabled placeholder="—" title="From the FNRI exchange list, per the number of exchanges" /></label>
                        <label class="mp-num" data-l="Carbs"><input :value="item.carb ?? ''" type="number" disabled placeholder="—" /></label>
                        <label class="mp-num" data-l="Protein"><input :value="item.prot ?? ''" type="number" disabled placeholder="—" /></label>
                        <label class="mp-num" data-l="Fat"><input :value="item.fat ?? ''" type="number" disabled placeholder="—" /></label>
                      </template>
                      <template v-else>
                        <input v-model="item.portion" type="text" class="portion-in" placeholder="e.g., ½ cup" aria-label="Portion" />
                        <label class="mp-num k" data-l="kcal"><input v-model.number="item.kcal" type="number" min="0" placeholder="0" /></label>
                        <label class="mp-num" data-l="Carbs"><input v-model.number="item.carb" type="number" min="0" placeholder="0" /></label>
                        <label class="mp-num" data-l="Protein"><input v-model.number="item.prot" type="number" min="0" placeholder="0" /></label>
                        <label class="mp-num" data-l="Fat"><input v-model.number="item.fat" type="number" min="0" placeholder="0" /></label>
                      </template>
                    </template>
                    <button class="remove-btn" type="button" title="Remove" aria-label="Remove food" @click="removeItem(meal, idx)"><Trash2 :size="15" /></button>
                    <p v-if="needsNumbers(item)" class="food-hint">Enter its calories and macros, or pick a food from the FNRI list so they fill in.</p>
                    <p v-if="itemWarnings(item).length" class="food-warn" :class="{ allergy: itemAllergyWarnings(item).length }" role="note">
                      <AlertTriangle :size="13" /> {{ itemWarnings(item).join(', ') }}
                    </p>
                  </div>
                </div>

                <div class="meal-foot" :class="{ empty: !meal.items.length }">
                  <div class="add-food-row">
                    <button class="btn-add-food" type="button" @click="addItem(meal)"><Plus :size="14" /> Add food</button>
                    <button class="btn-add-food usda-btn" type="button" @click="usdaMeal = meal"><Search :size="14" /> Add from USDA</button>
                  </div>
                  <template v-if="meal.items.length">
                    <span class="mf-n k" data-l="kcal">{{ mealTotal(meal, 'kcal') }}</span>
                    <span class="mf-n" data-l="Carbs">{{ mealTotal(meal, 'carb') }} g</span>
                    <span class="mf-n" data-l="Protein">{{ mealTotal(meal, 'prot') }} g</span>
                    <span class="mf-n" data-l="Fat">{{ mealTotal(meal, 'fat') }} g</span>
                    <span class="mf-gap" aria-hidden="true"></span>
                  </template>
                </div>
              </section>
            </div>

            <UsdaFoodPicker v-if="usdaMeal" :meal-label="`${activeDay}, ${usdaMeal.type}`" :allergies="patientAllergies" :patient-name="patientFirstName" @close="usdaMeal = null" @pick="addUsdaFood" />

            <!-- phones: the save buttons stay in reach above the bottom tabs -->
            <div class="mp-mbar no-print">
              <button class="btn-secondary" type="button" :disabled="!canUndo" title="Undo your last change (Ctrl+Z)" aria-label="Undo" @click="undo"><Undo2 :size="16" /></button>
              <button class="btn-secondary" type="button" :disabled="isSaving" @click="savePlan()">{{ isSaving ? 'Saving…' : selectedPlan.status === 'draft' ? 'Save draft' : 'Save changes' }}</button>
              <button class="btn-primary" type="button" :disabled="isSaving || isSending" @click="requestSend(saveAndSend)"><Send :size="15" /> Save &amp; send</button>
            </div>
          </template>
        </div>

        <!-- RIGHT SIDEBAR (CREATE MODE) -->
        <div class="side-column">
          <div v-if="selectedPlan" class="panel">
            <div class="side-head">
              <span class="side-ico ico-blue"><svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20V11M10 20V5M16 20v-6M21 20H3" /></svg></span>
              <div class="side-head-txt">
                <h4 class="side-title">Day totals</h4>
                <span class="side-subtitle">{{ DAY_FULL[activeDay] }}, against the targets</span>
              </div>
            </div>
            <div class="mp-ring-row">
              <div class="mp-ring" :style="{ '--p': macroPct('kcal') }">
                <span><strong>{{ dayTotal('kcal').toLocaleString('en-PH') }}</strong><small>of {{ planMeta.kcalPerDay ? Number(planMeta.kcalPerDay).toLocaleString('en-PH') : '—' }} kcal</small></span>
              </div>
              <div v-if="dayNote" class="mp-ring-note">
                <span class="mp-ok" :class="{ off: !dayNote.ok }">{{ dayNote.label }}</span>
                <p>{{ dayNote.text }}</p>
              </div>
            </div>
            <div class="nutrient-row">
              <div class="nutrient-top"><span><i class="dot" style="background: #C49102"></i>Carbs</span><span><strong>{{ dayTotal('carb') }} g</strong> / {{ targets.carb ?? '—' }} g</span></div>
              <div class="nutrient-bar"><div class="nutrient-fill fill-gold" :style="{ width: macroPct('carb') + '%' }"></div></div>
            </div>
            <div class="nutrient-row">
              <div class="nutrient-top"><span><i class="dot" style="background: #1F9D55"></i>Protein</span><span><strong>{{ dayTotal('prot') }} g</strong> / {{ targets.protein ?? '—' }} g</span></div>
              <div class="nutrient-bar"><div class="nutrient-fill fill-green" :style="{ width: macroPct('prot') + '%' }"></div></div>
            </div>
            <div class="nutrient-row">
              <div class="nutrient-top"><span><i class="dot" style="background: #3B5BA5"></i>Fat</span><span><strong>{{ dayTotal('fat') }} g</strong> / {{ targets.fat ?? '—' }} g</span></div>
              <div class="nutrient-bar"><div class="nutrient-fill fill-blue" :style="{ width: macroPct('fat') + '%' }"></div></div>
            </div>
            <p class="exchange-note">Based on foods entered for the selected day</p>
          </div>

          <div class="panel">
            <div class="side-head">
              <span class="side-ico ico-green"><svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01" /></svg></span>
              <div class="side-head-txt">
                <h4 class="side-title">Preview</h4>
                <span class="side-subtitle">What the patient sees</span>
              </div>
              <span v-if="selectedPlan" class="preview-day">{{ DAY_FULL[activeDay] }}</span>
            </div>

            <p v-if="!planMeta.name && !planMeta.kcalPerDay" class="macro-note">
              Fill in the plan details to see a live preview here.
            </p>

            <template v-else>
              <div class="preview-summary">
                <p class="preview-summary-name">{{ planMeta.name || 'Untitled Plan' }}</p>
                <div class="plan-badges">
                  <span v-if="planMeta.condition" class="badge badge-gold">{{ conditionLabel(planMeta.condition) }}</span>
                  <span v-if="planMeta.kcalPerDay" class="badge badge-blue">{{ planMeta.kcalPerDay }} kcal/day</span>
                </div>
              </div>

              <div v-if="planMeta.kcalPerDay || filledRows(macroRows).length" class="target-list">
                <!-- TER first, then the macros it's split into (user's call, 2026-11-01) -->
                <div v-if="planMeta.kcalPerDay" class="target-row target-ter">
                  <span>TER (Total Energy Requirement)</span><span>{{ Number(planMeta.kcalPerDay).toLocaleString('en-PH') }} kcal/day</span>
                </div>
                <div v-for="row in filledRows(macroRows)" :key="row.label" class="target-row">
                  <span>{{ row.label }}</span><span>{{ row.value }}{{ row.unit ? ` ${row.unit}` : '' }}</span>
                </div>
              </div>
              <div v-if="filledRows(otherRows).length" class="target-list">
                <p class="target-list-title">Other targets <span>(not in the TER)</span></p>
                <div v-for="row in filledRows(otherRows)" :key="row.label" class="target-row">
                  <span>{{ row.label }}</span><span>{{ row.value }}{{ row.unit ? ` ${row.unit}` : '' }}</span>
                </div>
              </div>
            </template>

            <div v-if="selectedPlan && currentDayMeals.some(m => m.items.some(i => i.name))" class="preview-list">
              <div class="preview-item" v-for="meal in currentDayMeals.filter(m => m.items.some(i => i.name))" :key="meal.type" :style="toneStyle(meal.type)">
                <span class="preview-ico"><component :is="meal.icon" :size="15" /></span>
                <div class="preview-body">
                  <div class="preview-label">{{ sentence(meal.type) }}</div>
                  <div class="preview-food">{{ firstFoodSummary(meal) }}</div>
                </div>
                <div class="preview-kcal">{{ mealTotal(meal, 'kcal') }} kcal</div>
              </div>
            </div>
            <p v-else-if="selectedPlan" class="macro-note">No meals added yet. Add food items per day to see the nutrition breakdown.</p>
          </div>

          <div v-if="selectedPlan" class="panel">
            <div class="side-head">
              <span class="side-ico ico-gold"><svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg></span>
              <div class="side-head-txt"><h4 class="side-title">Instructions for the patient</h4></div>
            </div>
            <div class="field">
              <label>Allergies and restrictions</label>
              <textarea v-model="instructions.allergies" rows="3" class="instr-box" placeholder="e.g., No shellfish, low potassium"></textarea>
            </div>
            <div class="field">
              <label>Notes for the patient</label>
              <textarea v-model="instructions.notes" data-allow-emoji rows="6" class="instr-box" placeholder="e.g., Please eat meals at regular times. Avoid skipping meals."></textarea>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="confirmDelete" class="nm-modal-overlay no-print" @click.self="confirmDelete = false">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="del-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="confirmDelete = false"><X :size="18" aria-hidden="true" /></button>
        <h3 id="del-title" class="nm-modal-title">Delete this draft?</h3>
        <p class="nm-modal-text">"{{ selectedPlan?.name }}" was never sent to {{ selectedPatientName || 'the patient' }}. Deleting it removes the whole 7-day week, every meal and food in it. This can't be undone.</p>
        <div class="nm-modal-actions">
          <button class="btn-secondary" type="button" @click="confirmDelete = false">Keep it</button>
          <button class="btn-danger solid" type="button" :disabled="isDeleting || deleteWait > 0" @click="deleteDraft"><Trash2 :size="15" /> {{ isDeleting ? 'Deleting…' : deleteWait > 0 ? `Delete draft (${deleteWait})` : 'Delete draft' }}</button>
        </div>
      </div>
    </div>
    <div v-if="leaveAsk" class="nm-modal-overlay no-print" @click.self="stayHere">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="leave-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="stayHere"><X :size="18" aria-hidden="true" /></button>
        <h3 id="leave-title" class="nm-modal-title">Leave without saving?</h3>
        <p class="nm-modal-text">Your changes to this plan aren't saved yet. If you leave now, they're lost.</p>
        <div class="nm-modal-actions">
          <button class="btn-secondary" type="button" @click="stayHere">Keep editing</button>
          <button class="btn-danger solid" type="button" @click="leaveAnyway">Leave without saving</button>
        </div>
      </div>
    </div>
    <div v-if="sendCheck" class="nm-modal-overlay no-print" @click.self="sendCheck = null">
      <div class="nm-modal send-check" role="dialog" aria-modal="true" aria-labelledby="send-check-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="sendCheck = null"><X :size="18" aria-hidden="true" /></button>
        <h3 id="send-check-title" class="nm-modal-title">{{ isResend ? 'Send the updated plan' : 'Send this plan' }} to {{ selectedPatientName || 'the patient' }}?</h3>
        <p class="send-consequence">
          <Lock :size="14" />
          <span v-if="isResend">{{ patientFirstName }} sees the changes right away. Their past meal logs are kept.</span>
          <span v-else><strong>Once sent, this plan can't be deleted.</strong> {{ patientFirstName }} sees it right away and starts logging meals against it. After that you can only edit and resend it, or replace it by sending a new plan.</span>
        </p>

        <template v-if="allergyHits.length">
          <p class="send-section allergy"><AlertTriangle :size="15" /> Allergy alert: contains foods {{ patientFirstName }} is allergic to ({{ patientAllergies.join(', ') }})</p>
          <ul class="send-check-list allergy">
            <li v-for="w in allergyHits" :key="w.key"><strong>{{ w.day }}, <span class="send-check-meal">{{ w.meal }}</span>: {{ w.food }}</strong><span>{{ w.allergy.join(', ') }}</span></li>
          </ul>
          <label class="allergy-ack">
            <input v-model="allergyAck" type="checkbox" />
            I've checked these foods against {{ patientFirstName }}'s allergies and confirm they are safe for them.
          </label>
        </template>

        <template v-if="conditionHits.length">
          <p class="send-section">May not suit {{ patientFirstName }}'s condition ({{ conditionSummary }})</p>
          <ul class="send-check-list">
            <li v-for="w in conditionHits" :key="w.key"><strong>{{ w.day }}, <span class="send-check-meal">{{ w.meal }}</span>: {{ w.food }}</strong><span>{{ w.condition.join(', ') }}</span></li>
          </ul>
        </template>

        <div class="nm-modal-actions">
          <button class="btn-secondary" type="button" @click="sendCheck = null">Go back and edit</button>
          <button class="btn-primary" type="button" :disabled="sendWait > 0 || (allergyHits.length > 0 && !allergyAck)" @click="confirmSend">
            <Send :size="15" /> {{ planWarnings.length ? 'Send anyway' : isResend ? 'Resend to patient' : 'Send to patient' }}<template v-if="sendWait > 0"> ({{ sendWait }})</template>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import {
  Eye, Plus, ChevronLeft, Printer, Pencil, Send, X,
  Sun, Coffee, Utensils, Apple, Moon, Bed, Search, AlertTriangle, Trash2, Undo2, Lock
} from 'lucide-vue-next'
import { usdaPortion } from '~/utils/usda'
import { MEASURE_TEMPLATES, TER_ACTIVITY, bmiClass, bmiOf } from '~/utils/ncp'
import { allergyWarnings, conditionKeys, foodWarnings } from '~/utils/foodWarnings'
import { focusFirstError } from '~/utils/focusFirstError'
import { useToast } from '~/composables/useToast'

const route = useRoute()
const router = useRouter()
const { get, post, patch, put, del } = useApi()

// Matches nutrition.MealPlan.Condition.
const CONDITIONS = [
  { value: 'diabetes', label: 'Diabetes' },
  { value: 'hypertension', label: 'Hypertension' },
  { value: 'renal', label: 'Renal Disease' },
  { value: 'weight_loss', label: 'Weight Loss' },
  { value: 'weight_gain', label: 'Weight Gain' },
  { value: 'general', label: 'General' },
]
function conditionLabel(value) {
  return CONDITIONS.find(c => c.value === value)?.label || value
}
function statusLabel(status) {
  return { draft: 'Draft, not sent yet', active: 'Sent, the patient can see it', archived: 'Archived' }[status] || status
}

// Design order Mon→Sun; day_of_week uses Sunday=0 (same as availability).
const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const DAY_INDEX = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }
const DAY_FULL = { Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday' }
const activeDay = ref(days[(new Date().getDay() + 6) % 7])

// Design meal slots → nutrition.MealPlanMeal.MealTime.
const mealOrder = ['Breakfast', 'Morning Snack', 'Lunch', 'Afternoon Snack', 'Dinner', 'Bedtime Snack']
const MEAL_TIME = { Breakfast: 'breakfast', 'Morning Snack': 'am_snack', Lunch: 'lunch', 'Afternoon Snack': 'pm_snack', Dinner: 'dinner', 'Bedtime Snack': 'bedtime_snack' }
// every 3 hours from 6 AM, filled into empty slots (same as the diet templates)
const DEFAULT_TIME = { Breakfast: '06:00', 'Morning Snack': '09:00', Lunch: '12:00', 'Afternoon Snack': '15:00', Dinner: '18:00', 'Bedtime Snack': '21:00' }
const MEAL_TYPE = Object.fromEntries(Object.entries(MEAL_TIME).map(([k, v]) => [v, k]))
const mealIcons = { Breakfast: Sun, 'Morning Snack': Coffee, Lunch: Utensils, 'Afternoon Snack': Apple, Dinner: Moon, 'Bedtime Snack': Bed }
const mealAccents = { Breakfast: 'green', 'Morning Snack': 'gold', Lunch: 'blue', 'Afternoon Snack': 'gold', Dinner: 'blue', 'Bedtime Snack': 'gold' }

const mode = ref('view')
const isLoading = ref(true)
const isSaving = ref(false)
const isSending = ref(false)
// errorMessage: only when the page itself could not load (it stays on the page).
// What an action did (saved, sent, failed) goes to the toast (2026-11-03), so
// it shows wherever the RND has scrolled. One toast slot for the page's actions.
const errorMessage = ref('')
const toast = useToast()
const TOAST_ID = 'meal-plan'
function flash(message, opts = {}) { toast.success(message, { id: TOAST_ID, ...opts }) }
function failed(message) { toast.error(message, { id: TOAST_ID }) }
const nameMissing = ref(false)
function apiError(error, fallback) {
  const data = error?.data || {}
  return data.detail || Object.values(data).flat().find(v => typeof v === 'string') || fallback
}

/* ---------- Patients (the RND's active clients) ---------- */
const patients = ref([])
const selectedRelId = ref(null)
const selectedPatientName = computed(() => patients.value.find(p => p.id === selectedRelId.value)?.name || '')

/* ---------- Plans for the selected patient ---------- */
const plans = ref([])
const selectedPlanId = ref(null)
const selectedPlan = computed(() => plans.value.find(p => p.id === selectedPlanId.value) || null)
const ncpTargets = ref(null)

const planMeta = reactive({ name: '', condition: 'general', kcalPerDay: null })
// Nutrient targets as Measured Variable / Value / Unit rows, shown in two
// groups but saved as one `nutrient_targets` list (macros first). The Macro
// Tracker reads protein / carbohydrate / fat from rows in grams — the same
// matching the API uses to fill the plan's macro columns.
const macroRows = ref([])
const otherRows = ref([])
const targetRows = computed(() => [...macroRows.value, ...otherRows.value])
const MACRO_LABELS = {
  protein: ['protein', 'proteins'],
  carb: ['carb', 'carbs', 'carbohydrate', 'carbohydrates'],
  fat: ['fat', 'fats', 'total fat'],
}
const isMacroLabel = label => Object.values(MACRO_LABELS).some(l => l.includes(String(label || '').trim().toLowerCase()))
// Saved plans keep one list. The macro group is always the three fixed rows,
// filled from the plan's first gram row for each; anything else (another
// macro row from an older plan included) goes to Other Targets.
function splitTargetRows(rows) {
  const clean = (rows || []).map(r => ({ label: r.label, value: r.value, unit: r.unit || '' }))
  const used = new Set()
  const take = key => {
    const row = clean.find(r => !used.has(r) && MACRO_LABELS[key].includes(r.label.trim().toLowerCase()) && GRAM_UNITS.includes(r.unit.trim().toLowerCase()))
    if (row) used.add(row)
    return row ? row.value : null
  }
  macroRows.value = defaultTargetRows(take('protein'), take('carb'), take('fat'))
  otherRows.value = clean.filter(r => !used.has(r))
}
const GRAM_UNITS = ['g', 'g/day', 'gram', 'grams', 'g per day', 'grams/day']
const targets = computed(() => {
  const out = { protein: null, carb: null, fat: null }
  for (const [key, labels] of Object.entries(MACRO_LABELS)) {
    const row = targetRows.value.find(r => labels.includes(r.label.trim().toLowerCase()) && GRAM_UNITS.includes(r.unit.trim().toLowerCase()))
    const value = row ? Number(row.value) : NaN
    out[key] = Number.isFinite(value) && value >= 0 ? value : null
  }
  return out
})
const filledRows = rows => rows.filter(r => r.label.trim() && String(r.value).trim())
function addTargetRow() {
  otherRows.value.push({ label: '', value: '', unit: '' })
}
function defaultTargetRows(protein = null, carb = null, fat = null) {
  const value = v => (v === null || v === undefined ? '' : String(v))
  return [
    { label: 'Protein', value: value(protein), unit: 'g/day' },
    { label: 'Carbohydrate', value: value(carb), unit: 'g/day' },
    { label: 'Fat', value: value(fat), unit: 'g/day' },
  ]
}
const instructions = reactive({ allergies: '', notes: '' })
const weeklyPlan = reactive(emptyWeek())

// New plan: 'template' or 'blank', picked before either form shows.
const startWith = ref(null)
const createBlocker = computed(() => {
  const missing = [!planMeta.name?.trim() && 'a plan name', !planMeta.kcalPerDay && 'daily calories'].filter(Boolean)
  return missing.length ? `Add ${missing.join(' and ')} to continue.` : ''
})

// Copy the open day's meals (times and foods) onto other days. Undo brings them back.
const copyTarget = ref('')
const COPY_SETS = { all: null, weekdays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], weekend: ['Sat', 'Sun'] }
function dayHasFood(day) {
  return mealOrder.some(type => weeklyPlan[day][type].items.some(i => i.name?.trim()))
}
function copyDay() {
  const from = activeDay.value
  const set = copyTarget.value in COPY_SETS ? (COPY_SETS[copyTarget.value] || days) : [copyTarget.value]
  const targets = set.filter(d => d !== from)
  for (const d of targets) {
    for (const type of mealOrder) weeklyPlan[d][type] = JSON.parse(JSON.stringify(weeklyPlan[from][type]))
  }
  copyTarget.value = ''
  flash(`Copied ${DAY_FULL[from]}'s meals to ${targets.map(d => DAY_FULL[d]).join(', ')}. Press Undo if that wasn't right.`, { duration: 6000 })
}

// A food typed by hand (not from FNRI or USDA) with no numbers adds nothing to the totals.
function needsNumbers(item) {
  return item.source !== 'usda' && !item.foodItemId && item.name?.trim()
    && [item.kcal, item.carb, item.prot, item.fat].every(v => !Number(v))
}

function emptyWeek() {
  const week = {}
  for (const day of days) {
    week[day] = {}
    for (const type of mealOrder) week[day][type] = { time: DEFAULT_TIME[type], items: [] }
  }
  return week
}
function num(v) {
  return v === null || v === undefined || v === '' ? null : Number(v)
}

function fillFromPlan(plan) {
  planMeta.name = plan.name
  planMeta.condition = plan.condition
  planMeta.kcalPerDay = num(plan.target_kcal) === null ? null : Math.round(num(plan.target_kcal))
  splitTargetRows(plan.nutrient_targets)
  instructions.allergies = plan.allergies_restrictions || ''
  instructions.notes = plan.notes || ''
  Object.assign(weeklyPlan, emptyWeek())
  for (const meal of plan.meals) {
    const type = MEAL_TYPE[meal.meal_time]
    const day = days.find(d => DAY_INDEX[d] === meal.day_of_week)
    if (!type || !day) continue
    weeklyPlan[day][type] = {
      time: meal.scheduled_time ? meal.scheduled_time.slice(0, 5) : DEFAULT_TIME[type],
      items: meal.food_items.map(i => ({
        foodItemId: i.food_item,
        name: i.food_name,
        portion: i.household_measure || '',
        exchanges: num(i.exchanges),
        kcal: num(i.kcal),
        carb: num(i.carbs_g),
        prot: num(i.protein_g),
        fat: num(i.fat_g),
        ...(i.source_type === 'usda' ? { source: 'usda', fdcId: i.external_food_id, grams: num(i.grams), per100: i.usda_per_100g } : {}),
      })),
    }
  }
  resetUndo()
}

function resetForm() {
  Object.assign(planMeta, { name: '', condition: 'general', kcalPerDay: null })
  macroRows.value = defaultTargetRows()
  otherRows.value = []
  Object.assign(instructions, { allergies: '', notes: '' })
  Object.assign(weeklyPlan, emptyWeek())
  // Pre-fill targets from the NCP Intervention phase when available.
  if (ncpTargets.value) {
    planMeta.kcalPerDay = ncpTargets.value.kcal
    macroRows.value = defaultTargetRows(ncpTargets.value.protein, ncpTargets.value.carb, ncpTargets.value.fat)
    otherRows.value = ncpTargets.value.other.map(r => ({ ...r }))
  }
  resetUndo()
}

/* ---------- Undo (unsaved week edits only) ---------- */
// The week is snapshotted half a second after each change (so typing a
// portion is one step, not one per letter); Undo steps back through up to 20
// snapshots. Loading or saving a plan clears it, so it can never reach
// anything already saved or sent.
const undoStack = ref([])
const pendingEdit = ref(false)
let lastSnapshot = null
let snapTimer = null
const snapshotWeek = () => JSON.stringify(weeklyPlan)
function resetUndo() {
  savedSnapshot = editorSnapshot()
  clearTimeout(snapTimer)
  undoStack.value = []
  pendingEdit.value = false
  lastSnapshot = snapshotWeek()
}
watch(weeklyPlan, () => {
  pendingEdit.value = snapshotWeek() !== lastSnapshot
  clearTimeout(snapTimer)
  snapTimer = setTimeout(() => {
    const now = snapshotWeek()
    if (lastSnapshot !== null && now !== lastSnapshot) {
      undoStack.value.push(lastSnapshot)
      if (undoStack.value.length > 20) undoStack.value.shift()
    }
    lastSnapshot = now
    pendingEdit.value = false
  }, 500)
}, { deep: true })
const canUndo = computed(() => pendingEdit.value || undoStack.value.length > 0)
function undo() {
  clearTimeout(snapTimer)
  // An edit not yet snapshotted goes back to the last snapshot first.
  const target = snapshotWeek() !== lastSnapshot ? lastSnapshot : undoStack.value.pop()
  if (!target) return
  Object.assign(weeklyPlan, JSON.parse(target))
  lastSnapshot = target
  pendingEdit.value = false
}
// Ctrl+Z / Cmd+Z in the week editor (text boxes keep their own undo).
function onUndoKey(event) {
  if (mode.value !== 'create' || !(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 'z' || event.shiftKey) return
  if (event.target instanceof HTMLElement && event.target.closest('input, textarea, select')) return
  event.preventDefault()
  undo()
}
onMounted(() => window.addEventListener('keydown', onUndoKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onUndoKey))

/* ---------- Leaving with unsaved edits ---------- */
// The whole editor (week, targets, name) as it was last loaded or saved;
// leaving the page or patient with changes asks first, closing the tab gets
// the browser's own prompt.
let savedSnapshot = null
const editorSnapshot = () => JSON.stringify([weeklyPlan, macroRows.value, otherRows.value, planMeta])
const hasUnsaved = () => mode.value === 'create' && savedSnapshot !== null && editorSnapshot() !== savedSnapshot
const leaveAsk = ref(false)
let leaveTo = null
function guard(to) {
  if (!hasUnsaved()) return true
  leaveTo = to
  leaveAsk.value = true
  return false
}
onBeforeRouteLeave(guard)
onBeforeRouteUpdate(guard) // ?relationship= changes (All patients, another patient)
function stayHere() {
  leaveAsk.value = false
  leaveTo = null
}
function leaveAnyway() {
  savedSnapshot = editorSnapshot() // let this navigation through
  const to = leaveTo
  stayHere()
  if (to) navigateTo(to.fullPath)
}
const onTabClose = (e) => { if (hasUnsaved()) { e.preventDefault(); e.returnValue = '' } }
onMounted(() => window.addEventListener('beforeunload', onTabClose))
onBeforeUnmount(() => window.removeEventListener('beforeunload', onTabClose))

/* ---------- Delete a draft (never sent) ---------- */
const confirmDelete = ref(false)
const isDeleting = ref(false)
// The Delete button stays locked for 3 seconds each time the pop-up opens, so
// the RND reads the warning first (user's call, 2026-10-15). Keep it works
// right away.
const deleteWait = ref(0)
let deleteTimer = null
watch(confirmDelete, (open) => {
  clearInterval(deleteTimer)
  deleteWait.value = open ? 3 : 0
  if (open) {
    deleteTimer = setInterval(() => {
      deleteWait.value -= 1
      if (deleteWait.value <= 0) clearInterval(deleteTimer)
    }, 1000)
  }
})
onBeforeUnmount(() => clearInterval(deleteTimer))
async function deleteDraft() {
  const plan = selectedPlan.value
  if (!plan || plan.status !== 'draft' || deleteWait.value > 0) return
  isDeleting.value = true
  errorMessage.value = ''
  try {
    await del(`/rnd/meal-plans/${plan.id}/`)
    plans.value = plans.value.filter(p => p.id !== plan.id)
    confirmDelete.value = false
    const next = plans.value.find(p => p.status === 'active') || plans.value[0]
    if (next) selectPlan(next.id)
    else { selectedPlanId.value = null; resetForm(); mode.value = 'view' }
    flash('Draft deleted.')
  } catch (error) {
    confirmDelete.value = false
    failed(apiError(error, 'Could not delete the draft.'))
  } finally {
    isDeleting.value = false
  }
}

function selectPlan(id) {
  selectedPlanId.value = id
  const plan = selectedPlan.value
  if (plan) fillFromPlan(plan)
  mode.value = 'view'
}

// + New plan clears the selection; View plan brings back the plan you were
// on (or the sent one) instead of showing "No meal plan yet".
let planBeforeNew = null
function showView() {
  if (!selectedPlanId.value && plans.value.length) {
    const back = plans.value.find(p => p.id === planBeforeNew)
      || plans.value.find(p => p.status === 'active') || plans.value[0]
    selectPlan(back.id)
    return
  }
  mode.value = 'view'
}

function startNewPlan() {
  planBeforeNew = selectedPlanId.value
  startWith.value = null
  selectedPlanId.value = null
  resetForm()
  mode.value = 'create'
}

function openCreate() {
  if (selectedPlan.value) fillFromPlan(selectedPlan.value)
  else { resetForm(); startWith.value = null }
  mode.value = 'create'
}

function discardChanges() {
  if (selectedPlan.value) fillFromPlan(selectedPlan.value)
  showView()
}

async function loadPatients() {
  const rels = await get('/rnd/relationships/active/')
  patients.value = rels.map(r => ({ id: r.id, name: `${r.client.first_name} ${r.client.last_name}` }))
  // Only open a patient when the link names one (patient chart, dashboard);
  // from the sidebar the page starts on the patient list.
  const requested = Number(route.query.relationship)
  selectedRelId.value = patients.value.find(p => p.id === requested)?.id ?? null
}

async function loadPatientPlans() {
  if (!selectedRelId.value) return
  errorMessage.value = ''
  const [planList, ncpList] = await Promise.all([
    get(`/rnd/relationships/${selectedRelId.value}/meal-plans/`),
    get(`/rnd/relationships/${selectedRelId.value}/ncp/`).catch(() => []),
  ])
  plans.value = planList
  loadPatientConditions(selectedRelId.value)
  const ncp = ncpList[0]
  ncpTargets.value = ncp && ncp.target_kcal
    ? {
        kcal: Math.round(num(ncp.target_kcal)), protein: num(ncp.target_protein_g), carb: num(ncp.target_carb_g), fat: num(ncp.target_fat_g),
        // The Intervention's "Other measurements" rows (sodium, fiber…); the
        // Assessment's rows are lab results, not diet targets, so they stay out.
        other: (ncp.intervention_extra || [])
          .filter(r => r.label?.trim() && String(r.value ?? '').trim() && !isMacroLabel(r.label))
          .map(r => ({ label: r.label.trim(), value: String(r.value).trim(), unit: (r.unit || '').trim() })),
      }
    : null

  const preferred = planList.find(p => p.status === 'active') || planList.find(p => p.status === 'draft') || planList[0]
  if (preferred) {
    selectPlan(preferred.id)
    if (route.query.edit) mode.value = 'create'
  } else {
    selectedPlanId.value = null
    resetForm()
    mode.value = route.query.edit ? 'create' : 'view'
  }
}

function pickPatient(id) {
  router.push({ query: { ...route.query, relationship: id } })
}
function backToList() {
  const { relationship, edit, ...rest } = route.query
  router.push({ query: rest })
}
// The URL is the source of truth: ?relationship=<id> opens that patient,
// no parameter shows the list (so Back works as expected).
watch(() => route.query.relationship, (rel) => {
  const id = patients.value.find(p => p.id === Number(rel))?.id ?? null
  if (id !== selectedRelId.value) selectedRelId.value = id
  if (!id) { selectedPlanId.value = null; mode.value = 'view' }
})
watch(selectedRelId, async (id, previous) => {
  if (id && String(route.query.relationship) !== String(id)) router.replace({ query: { ...route.query, relationship: id } })
  if (!id || previous === undefined) return
  try {
    await loadPatientPlans()
  } catch {
    errorMessage.value = 'Could not load this patient\'s meal plans.'
  }
})

onMounted(async () => {
  loadFnriItems()
  try {
    await loadPatients()
    await loadPatientPlans()
  } catch {
    errorMessage.value = 'Could not load meal plans. Please try again later.'
  } finally {
    isLoading.value = false
  }
})

/* ---------- Create / save / send ---------- */
function planDetailsPayload() {
  return {
    name: planMeta.name.trim(),
    condition: planMeta.condition,
    target_kcal: planMeta.kcalPerDay ?? null,
    nutrient_targets: targetRows.value
      .filter(r => r.label.trim())
      .map(r => ({ label: r.label.trim(), value: String(r.value ?? '').trim(), unit: (r.unit || '').trim() })),
    allergies_restrictions: instructions.allergies || null,
    notes: instructions.notes || null,
  }
}

function weekPayload() {
  const meals = []
  for (const day of days) {
    for (const type of mealOrder) {
      const slot = weeklyPlan[day][type]
      meals.push({
        day_of_week: DAY_INDEX[day],
        meal_time: MEAL_TIME[type],
        scheduled_time: slot.time || null,
        items: slot.items
          .filter(i => i.name && i.name.trim())
          .map(i => (i.source === 'usda' ? {
            food_name: i.name.trim(),
            source_type: 'usda',
            external_food_id: String(i.fdcId),
            grams: i.grams,
            household_measure: `${i.grams} g`,
          } : {
            food_item: i.foodItemId || null,
            food_name: i.name.trim(),
            household_measure: i.portion || null,
            exchanges: i.exchanges || 1,
            kcal: i.kcal ?? null,
            carbs_g: i.carb ?? null,
            protein_g: i.prot ?? null,
            fat_g: i.fat ?? null,
          })),
      })
    }
  }
  return { meals }
}

// A draft built from a diet template: show its week so the RND can review it.
function onTemplateCreated(plan, label) {
  replacePlan(plan)
  selectPlan(plan.id)
  flash(`Draft built from the ${label} template. Check each day and adjust, then send it to ${selectedPatientName.value}.`, { duration: 6000 })
}

function replacePlan(updated) {
  const idx = plans.value.findIndex(p => p.id === updated.id)
  if (idx >= 0) plans.value.splice(idx, 1, updated)
  else plans.value.unshift(updated)
}

async function createPlan() {
  isSaving.value = true
  errorMessage.value = ''
  try {
    const created = await post(`/rnd/relationships/${selectedRelId.value}/meal-plans/`, {
      relationship: selectedRelId.value,
      ...planDetailsPayload(),
    })
    replacePlan(created)
    selectedPlanId.value = created.id
    flash('Plan created as a draft. Add meals for each day, then send it to your patient.', { duration: 6000 })
  } catch (error) {
    failed(apiError(error, 'Could not create the plan.'))
  } finally {
    isSaving.value = false
  }
}

async function savePlan({ quiet = false } = {}) {
  if (!selectedPlan.value) return false
  if (!planMeta.name.trim()) {
    nameMissing.value = true
    toast.problem('Give the plan a name before saving.', { id: TOAST_ID })
    focusFirstError()
    return false
  }
  isSaving.value = true
  errorMessage.value = ''
  try {
    await patch(`/rnd/meal-plans/${selectedPlanId.value}/`, planDetailsPayload())
    const saved = await put(`/rnd/meal-plans/${selectedPlanId.value}/week/`, weekPayload())
    replacePlan(saved)
    fillFromPlan(saved)
    if (!quiet) flash('Plan saved.')
    else toast.dismiss(TOAST_ID) // a quiet save (before sending) still clears an old error
    return true
  } catch (error) {
    failed(apiError(error, 'Could not save the plan.'))
    return false
  } finally {
    isSaving.value = false
  }
}

/* ---------- Condition warnings (FNRI foods that may not suit the patient) ---------- */
const fnriById = ref({})
const patientConditions = ref([])
const patientAllergies = ref([])
async function loadFnriItems() {
  try {
    const items = await get('/food-exchange/items/')
    fnriById.value = Object.fromEntries(items.map(f => [f.id, f]))
  } catch {
    fnriById.value = {}
  }
}
const patientSummary = ref(null)
async function loadPatientConditions(relId) {
  patientConditions.value = []
  patientAllergies.value = []
  patientSummary.value = null
  try {
    const summary = await get(`/rnd/relationships/${relId}/summary/`)
    if (relId === selectedRelId.value) {
      patientConditions.value = summary.health?.conditions || []
      patientAllergies.value = summary.health?.allergies || []
      patientSummary.value = summary
    }
  } catch {
    // No conditions known — the plan's own condition still counts.
  }
}
// Age, sex and the latest measurements, for setting the targets: weight and
// height from the latest finalized NCP record, else the screening.
const patientBody = computed(() => {
  const s = patientSummary.value
  if (!s) return null
  const cp = s.care_plan
  const sc = s.screening
  const fromNcp = cp && cp.weight_kg != null
  const weight = fromNcp ? cp.weight_kg : sc?.weight_kg ?? null
  const height = (fromNcp && cp.height_cm) || sc?.height_cm || null
  const date = fromNcp ? cp.encounter_date : sc?.date
  const bmi = bmiOf(weight, height)
  const activity = TER_ACTIVITY.find(a => a.value === cp?.ter_activity)
  return {
    age: s.patient?.client?.age ?? null,
    sex: s.patient?.client?.sex ? s.patient.client.sex.charAt(0).toUpperCase() + s.patient.client.sex.slice(1) : null,
    weight, height, bmi, bmiClass: bmi ? bmiClass(bmi) : '',
    ter: cp?.target_kcal ?? null,
    terNote: cp?.target_kcal ? `NCP${activity ? `, ${activity.label.toLowerCase()} activity` : ''}` : '',
    source: weight == null ? '' : `Weight and height from the ${fromNcp ? 'NCP record' : 'screening'} of ${new Date(date).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })}.`,
  }
})
const warnKeys = computed(() => conditionKeys(patientConditions.value, planMeta.condition))
// The patient's conditions, plus the plan's condition when it adds one.
const conditionSummary = computed(() => {
  const names = [...patientConditions.value]
  const fromPatient = conditionKeys(names)
  const fromPlan = [...conditionKeys(planMeta.condition)]
  if (fromPlan.some(k => !fromPatient.has(k))) names.push(conditionLabel(planMeta.condition))
  return names.join(', ')
})
// Allergies first (any food, by name), then condition notes (FNRI foods only).
function itemAllergyWarnings(item) {
  return item?.name ? allergyWarnings(item.name, patientAllergies.value) : []
}
function itemConditionWarnings(item) {
  if (!item?.name || !item.foodItemId || item.source === 'usda') return []
  return foodWarnings(fnriById.value[item.foodItemId], warnKeys.value)
}
function itemWarnings(item) {
  return [...itemAllergyWarnings(item), ...itemConditionWarnings(item)]
}
const planWarnings = computed(() => {
  const out = []
  for (const day of days) {
    for (const type of mealOrder) {
      weeklyPlan[day][type].items.forEach((item, idx) => {
        const allergy = itemAllergyWarnings(item)
        const condition = itemConditionWarnings(item)
        if (allergy.length || condition.length) {
          out.push({ key: `${day}-${type}-${idx}`, day, meal: type, food: item.name, allergy, condition, reasons: [...allergy, ...condition] })
        }
      })
    }
  }
  return out
})
// Allergies can be life-threatening: listed apart, in red, and the RND must
// tick that they checked them before Send unlocks (user's rule, 2026-10-15).
const allergyHits = computed(() => planWarnings.value.filter(w => w.allergy.length))
const conditionHits = computed(() => planWarnings.value.filter(w => w.condition.length))
const allergyAck = ref(false)
const isResend = computed(() => selectedPlan.value?.status === 'active')
const patientFirstName = computed(() => (selectedPatientName.value || 'the patient').split(' ')[0])
const warningDays = computed(() => new Set(planWarnings.value.map(w => w.day)))
// Every send asks first: what sending means (a sent plan can't be deleted),
// plus any allergy / condition warnings.
const sendCheck = ref(null)
function requestSend(action) {
  allergyAck.value = false
  sendCheck.value = action
}
// Send stays locked for 3 seconds each time the confirmation opens, like
// Delete draft, so the RND reads it first (user's call, 2026-10-15).
const sendWait = ref(0)
let sendTimer = null
watch(sendCheck, (open) => {
  clearInterval(sendTimer)
  sendWait.value = open ? 3 : 0
  if (open) {
    sendTimer = setInterval(() => {
      sendWait.value -= 1
      if (sendWait.value <= 0) clearInterval(sendTimer)
    }, 1000)
  }
})
onBeforeUnmount(() => clearInterval(sendTimer))
function confirmSend() {
  if (sendWait.value > 0) return
  const action = sendCheck.value
  sendCheck.value = null
  action?.()
}

async function sendToPatient() {
  isSending.value = true
  errorMessage.value = ''
  const wasActive = selectedPlan.value?.status === 'active'
  try {
    const sent = await post(`/rnd/meal-plans/${selectedPlanId.value}/send/`)
    // Sending archives any other active plan for this patient.
    plans.value = plans.value.map(p => (p.status === 'active' && p.id !== sent.id ? { ...p, status: 'archived' } : p))
    replacePlan(sent)
    flash(wasActive ? `Updated plan sent to ${selectedPatientName.value}.` : `Plan sent to ${selectedPatientName.value}.`)
    mode.value = 'view'
  } catch (error) {
    failed(apiError(error, 'Could not send the plan.'))
  } finally {
    isSending.value = false
  }
}

async function saveAndSend() {
  if (await savePlan({ quiet: true })) await sendToPatient()
}

function printPlan() {
  window.print()
}

/* ---------- FNRI food picker ---------- */
// Same searchable picker style as the NCP form (one dropdown look app-wide):
// FNRI foods grouped by exchange group, filtered from the list already loaded
// for the warnings, with the patient's allergens tagged in red.
const foodPick = reactive({ key: null, term: '', active: -1 })
const foodMatches = computed(() => {
  if (!foodPick.key) return []
  const term = foodPick.term.trim().toLowerCase()
  const foods = Object.values(fnriById.value)
    .filter(f => !term || `${f.name} ${f.local_name || ''}`.toLowerCase().includes(term))
    .sort((a, b) => (a.category?.sort_order ?? 0) - (b.category?.sort_order ?? 0) || a.name.localeCompare(b.name))
  const groups = new Map()
  for (const f of foods) {
    const name = f.category?.name || 'Other'
    if (!groups.has(name)) groups.set(name, [])
    groups.get(name).push(f)
  }
  return [...groups].map(([group, list]) => ({ group, foods: list }))
})
const flatFoodMatches = computed(() => foodMatches.value.flatMap(g => g.foods))
function openFoodPick(key, value) {
  foodPick.key = key
  foodPick.term = value || ''
  foodPick.active = -1
}
function closeFoodPickSoon() {
  setTimeout(() => { foodPick.key = null }, 120)
}
function moveFood(step) {
  const n = flatFoodMatches.value.length
  if (!foodPick.key || !n) return
  foodPick.active = (foodPick.active + step + n) % n
}
function pickFood(item, food) {
  applyFnriItem(item, food)
  foodPick.key = null
}
function pickActiveFood(item, event) {
  const food = flatFoodMatches.value[foodPick.active]
  if (foodPick.key && food) {
    event.preventDefault()
    pickFood(item, food)
  }
}
// Typing clears any previous FNRI link until a food is picked again. The
// value comes from the event: this can run before v-model updates item.name.
function onFoodNameInput(item, value, key) {
  item.foodItemId = null
  foodPick.key = key
  foodPick.term = value || ''
  foodPick.active = -1
}
// A name typed in full (and tabbed out of) still links to its FNRI food.
function applyFnriMatch(item, value) {
  const term = (value || '').trim().toLowerCase()
  if (item.foodItemId || term.length < 2) return
  const match = Object.values(fnriById.value).find(f => f.name.toLowerCase() === term)
  if (match) applyFnriItem(item, match)
}
// Picking an FNRI food starts at 1 exchange; the RND sets how many exchanges
// and the portion and macros follow from its FNRI category (2026-11-02: they
// used to stay at 1 exchange whatever the portion said).
function applyFnriItem(item, match) {
  item.name = match.name
  item.foodItemId = match.id
  setExchanges(item, 1, match)
}
// "½", "1½", "2" for an exchange count
function fmtExchanges(n) {
  const whole = Math.floor(n)
  const half = Math.abs(n - whole - 0.5) < 0.01
  return half ? `${whole || ''}½` : String(Math.round(n * 100) / 100)
}
// The portion the client reads: the FNRI household measure of one exchange, times the count.
function portionLabel(measure, ex) {
  if (!measure) return `${fmtExchanges(ex)} exchange${ex === 1 ? '' : 's'}`
  return ex === 1 ? measure : `${fmtExchanges(ex)} × ${measure}`
}
function setExchanges(item, value, food = fnriById.value[item.foodItemId]) {
  const ex = value === '' || value == null ? null : Math.min(20, Math.max(0, Number(value)))
  item.exchanges = ex
  if (!food || !ex) {
    Object.assign(item, { kcal: null, carb: null, prot: null, fat: null })
    return
  }
  const cat = food.category
  const times = v => (v == null ? null : Math.round(num(v) * ex * 10) / 10)
  item.portion = portionLabel(food.household_measure, ex)
  Object.assign(item, { kcal: times(cat.kcal_per_exchange), carb: times(cat.carbs_g), prot: times(cat.protein_g), fat: times(cat.fat_g) })
}

/* ---------- Meals, totals ---------- */
function mealsForDay(day) {
  return mealOrder.map(type => {
    const meal = weeklyPlan[day][type]
    const named = meal.items.filter(i => i.name)
    return {
      type,
      time: meal.time,
      items: meal.items,
      icon: mealIcons[type],
      accent: mealAccents[type],
      kcal: round(named.reduce((sum, i) => sum + (Number(i.kcal) || 0), 0)),
      foods: named,
    }
  })
}
const currentDayMeals = computed(() => mealsForDay(activeDay.value))
// Print shows the whole week; the screen shows only the selected day.
const printDays = days

function round(n) {
  return Math.round(n * 10) / 10
}
// a meal-foods cell: 1 decimal, blanks as 0
const cell = v => round(Number(v) || 0)
const sentence = t => t.charAt(0) + t.slice(1).toLowerCase() // "Morning Snack" -> "Morning snack"
function mealTotal(meal, field) {
  return round(meal.items.reduce((sum, i) => sum + (Number(i[field]) || 0), 0))
}
function dayTotal(field) {
  return round(currentDayMeals.value.reduce((sum, meal) => sum + mealTotal(meal, field), 0))
}
function macroPct(field) {
  const fieldTargets = { kcal: planMeta.kcalPerDay, carb: targets.value.carb, prot: targets.value.protein, fat: targets.value.fat }
  const target = fieldTargets[field]
  if (!target) return 0
  return Math.min(100, Math.round((dayTotal(field) / target) * 100))
}

const nutrition = computed(() => ({
  calories: { value: dayTotal('kcal'), target: planMeta.kcalPerDay },
  carbs: { value: dayTotal('carb'), target: targets.value.carb },
  protein: { value: dayTotal('prot'), target: targets.value.protein },
  fat: { value: dayTotal('fat'), target: targets.value.fat },
}))
function pct(n) {
  if (!n.target) return 0
  return Math.min(100, Math.round((n.value / n.target) * 100))
}

function addItem(meal) {
  weeklyPlan[activeDay.value][meal.type].items.push({ foodItemId: null, name: '', portion: '', exchanges: 1, kcal: null, carb: null, prot: null, fat: null })
}
// USDA foods: name + FDC id + grams are saved; the numbers come from USDA's
// per-100 g values (kept in memory only) — see nutrition/usda.py.
const usdaMeal = ref(null)
function addUsdaFood({ fdcId, name, grams, per100 }) {
  const item = { source: 'usda', fdcId, name, grams, per100, foodItemId: null, portion: `${grams} g`, exchanges: 1 }
  setGrams(item, grams)
  weeklyPlan[activeDay.value][usdaMeal.value.type].items.push(item)
  usdaMeal.value = null
}
function setGrams(item, value) {
  item.grams = value === '' ? null : Number(value)
  item.portion = item.grams ? `${item.grams} g` : ''
  const v = usdaPortion(item.per100, item.grams)
  Object.assign(item, { kcal: v.kcal, carb: v.carbs_g, prot: v.protein_g, fat: v.fat_g })
}
function removeItem(meal, idx) {
  weeklyPlan[activeDay.value][meal.type].items.splice(idx, 1)
}
function firstFoodSummary(meal) {
  const named = meal.items.filter(i => i.name)
  return named.length ? `${named[0].name}${named.length > 1 ? ` (+${named.length - 1} more)` : ''}` : ''
}

function formatTime(t) {
  const [h, m] = t.split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const initials = computed(() => (selectedPatientName.value || '?').split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase())
// a colour per meal slot: icon box, left border and the header wash
const MEAL_TONES = {
  Breakfast: { c: '#9A7300', bg: '#FBF3D2' },
  'Morning Snack': { c: '#8A4B2A', bg: '#F8ECE4' },
  Lunch: { c: '#004D3A', bg: '#E3EFE7' },
  'Afternoon Snack': { c: '#B4384A', bg: '#FDEDEF' },
  Dinner: { c: '#3B5BA5', bg: '#EEF1FA' },
  'Bedtime Snack': { c: '#5B4A9A', bg: '#F1EEF8' },
}
const toneStyle = type => ({ '--mc': MEAL_TONES[type]?.c || '#004D3A', '--mb': MEAL_TONES[type]?.bg || '#E3EFE7' })
const MACRO_COLORS = { Protein: '#1F9D55', Carbohydrate: '#C49102', Fat: '#3B5BA5' }
const fmtNum = v => (v == null || v === '' ? '—' : Number(v).toLocaleString('en-PH'))
function dayKcal(day) {
  return round(mealsForDay(day).reduce((sum, m) => sum + m.kcal, 0))
}
function mealCount(day) {
  return mealsForDay(day).filter(m => m.foods.length).length
}
// the note beside the calorie ring (within 5% of the TER counts as on target)
const dayNote = computed(() => {
  const value = Number(nutrition.value.calories.value) || 0
  const target = Number(nutrition.value.calories.target) || 0
  if (!target) return null
  if (!value) return { ok: false, label: 'No foods yet', text: `Add foods to ${DAY_FULL[activeDay.value]} to see how it adds up.` }
  const gap = round(value - target)
  const ok = Math.abs(gap) <= target * 0.05
  const text = gap === 0 ? 'Right on the daily calories.' : `${Math.abs(gap).toLocaleString('en-PH')} kcal ${gap < 0 ? 'under' : 'over'} the target.`
  return { ok, label: ok ? 'On target' : gap < 0 ? 'Under target' : 'Over target', text }
})
// the patient's figures as one dotted line in the edit header
const bodyParts = computed(() => {
  const b = patientBody.value
  if (!b) return []
  return [
    b.age != null && `${b.age} yrs`,
    b.sex,
    b.height && `${Number(b.height)} cm`,
    b.weight != null && `${Number(b.weight)} kg`,
    b.bmi && `BMI ${b.bmi.toFixed(1)}${b.bmiClass ? `, ${b.bmiClass}` : ''}`,
    b.ter && `NCP TER ${Math.round(b.ter).toLocaleString('en-PH')} kcal${b.terNote && b.terNote !== 'NCP' ? ` (${b.terNote.replace(/^NCP, /, '')})` : ''}`,
  ].filter(Boolean)
})
</script>
<style scoped>
.meal-planning-page {
  --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22);
  color: #22362c;
}
.ic { flex-shrink: 0; }
button { font-family: inherit; }
.back-link:focus-visible, .mode-btn:focus-visible, .mp-btn:focus-visible, .day-tab:focus-visible, .btn-primary:focus-visible, .btn-secondary:focus-visible,
.btn-danger:focus-visible, .mp-ghost:focus-visible, .btn-add-food:focus-visible, .remove-btn:focus-visible, .saved-plan-card:focus-visible, .start-opt:focus-visible,
.targets-add-btn:focus-visible, .targets-remove-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

/* ---------- TOP CONTROLS ---------- */
.mp-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
.back-link {
  display: inline-flex; align-items: center; gap: 6px; height: 40px; padding: 0 16px 0 12px; border: 1px solid #e4ebe6; border-radius: 999px;
  background: #fff; font-size: 13.5px; font-weight: 700; color: #004d3a; cursor: pointer; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.back-link:hover { background: #f1f6f2; }
.mode-toggle { display: inline-flex; gap: 4px; padding: 4px; border-radius: 999px; background: #fff; border: 1px solid #e4ebe6; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04); }
.mode-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 38px; padding: 0 18px; border: none; border-radius: 999px;
  background: transparent; font-size: 13.5px; font-weight: 700; color: #4a5a52; cursor: pointer; white-space: nowrap;
}
.mode-btn:hover:not(:disabled):not(.active) { background: #f1f6f2; color: #004d3a; }
.mode-btn.active { background: #004d3a; color: #fff; box-shadow: 0 8px 16px -10px rgba(0, 77, 58, 0.9); }
.mode-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ---------- LOADING / EMPTY ---------- */
.mp-loading { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 60px 20px; font-size: 14px; font-weight: 600; color: #6b7d73; }
.mp-spin { width: 18px; height: 18px; border-radius: 50%; border: 2.5px solid #e3efe7; border-top-color: #004d3a; animation: mp-spin 0.8s linear infinite; }
@keyframes mp-spin { to { transform: rotate(360deg); } }
.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 56px 20px; text-align: center;
  background: #fff; border: 1.5px dashed #cfddd4; border-radius: 22px;
}
.empty-ico { width: 56px; height: 56px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.empty-title { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; margin: 0; }
.empty-text { margin: 0; max-width: 420px; font-size: 13.5px; line-height: 1.55; color: #6b7d73; }
.form-error { background: #fef3f2; border: 1px solid #f6cfcb; color: #912018; border-radius: 14px; padding: 12px 16px; font-size: 13.5px; font-weight: 600; margin: 0 0 16px; }

/* ---------- HERO ---------- */
.mp-wrap { display: flex; flex-direction: column; gap: 18px; }
.mp-hero {
  position: relative; overflow: hidden; display: flex; align-items: flex-end; justify-content: space-between; gap: 18px 24px; flex-wrap: wrap;
  padding: 26px 30px; border-radius: 24px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.mp-hero-plate { position: absolute; right: -70px; top: 50%; width: 360px; height: 360px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); opacity: 0.85; pointer-events: none; }
.mp-hero-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 48%, rgba(0, 77, 58, 0.8) 72%, rgba(0, 77, 58, 0.3) 100%); }
.mp-hero-who { position: relative; z-index: 1; display: flex; align-items: center; gap: 16px; min-width: 0; flex: 1 1 360px; }
.mp-av {
  flex-shrink: 0; width: 60px; height: 60px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.14);
}
.mp-hero-txt { min-width: 0; }
.mp-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 6px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.mp-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.mp-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.15; color: #fff; overflow-wrap: anywhere; }
.mp-sub { display: flex; align-items: center; flex-wrap: wrap; gap: 4px 10px; margin: 0; font-size: 14px; color: rgba(255, 255, 255, 0.86); }
.mp-sub i { width: 4px; height: 4px; border-radius: 50%; background: rgba(255, 255, 255, 0.45); }
.mp-src { margin: 6px 0 0; font-size: 12px; color: rgba(255, 255, 255, 0.6); }
.mp-status { display: inline-flex; align-items: center; gap: 7px; font-weight: 700; color: #efbf04; }
.mp-status b { width: 8px; height: 8px; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.14); }
.mp-status.st-active { color: #6ee7a8; }
.mp-status.st-archived { color: rgba(255, 255, 255, 0.7); }
.mp-targets { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(4, auto); gap: 8px; }
.mp-t {
  display: flex; flex-direction: column; min-width: 86px; padding: 10px 14px; border-radius: 14px;
  background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.18); backdrop-filter: blur(6px);
}
.mp-t small { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700; letter-spacing: 0.4px; color: rgba(255, 255, 255, 0.75); }
.mp-t small i { width: 7px; height: 7px; border-radius: 2px; }
.mp-t strong { font-family: 'Playfair Display', serif; font-size: 24px; line-height: 1.2; color: #fff; }
.mp-t em { font-style: normal; font-size: 11.5px; color: rgba(255, 255, 255, 0.65); white-space: nowrap; }
.mp-t.big { min-width: 120px; background: #fff; border-color: #fff; }
.mp-t.big small, .mp-t.big em { color: #6b7d73; }
.mp-t.big strong { color: #004d3a; }
.mp-hero-acts { position: relative; z-index: 1; flex-basis: 100%; display: flex; flex-wrap: wrap; gap: 8px; }
.mp-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 18px; border-radius: 12px;
  border: 1px solid transparent; font-size: 13.5px; font-weight: 800; white-space: nowrap; cursor: pointer; transition: transform 0.15s, background 0.15s;
}
.mp-btn:hover:not(:disabled) { transform: translateY(-1px); }
.mp-btn.glass { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.22); color: #fff; }
.mp-btn.glass:hover:not(:disabled) { background: rgba(255, 255, 255, 0.18); }
.mp-btn.gold { background: #efbf04; color: #004d3a; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.mp-btn.gold:hover:not(:disabled) { background: #f5cb1c; }
.mp-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ---------- LAYOUT / PANELS ---------- */
.planning-layout { display: grid; grid-template-columns: minmax(0, 2.3fr) minmax(0, 1fr); gap: 22px; align-items: start; }
.mp-main, .create-column, .side-column { display: flex; flex-direction: column; gap: 18px; min-width: 0; }
.panel { background: #fff; border-radius: 22px; padding: 22px; border: none; }
/* the client dashboard shadow, on every panel here and in the parts this page shows
   (patient list, template picker) */
.meal-planning-page :deep(.panel), .meal-planning-page :deep(.nm-panel) { box-shadow: var(--sh); }

.side-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.side-head-txt { flex: 1; min-width: 0; }
.side-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; display: inline-flex; align-items: center; justify-content: center; }
.ico-green { background: #e3efe7; color: #004d3a; }
.ico-blue { background: #eef1fa; color: #3b5ba5; }
.ico-gold { background: #fbf3d2; color: #9a7300; }
.side-title { margin: 0; font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #0e3a2c; }
.side-subtitle { display: block; margin-top: 2px; font-size: 12.5px; color: #6b7d73; }

/* ---------- DAY TABS ---------- */
.day-tabs {
  display: flex; gap: 4px; padding: 5px; width: max-content; max-width: 100%; box-sizing: border-box; overflow-x: auto; scrollbar-width: none;
  border-radius: 999px; background: #fff; border: 1px solid #e4ebe6; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.day-tabs::-webkit-scrollbar { display: none; }
.day-tab {
  position: relative; flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center; height: 38px; min-width: 54px; padding: 0 14px;
  border: none; border-radius: 999px; background: transparent; font-size: 13.5px; font-weight: 700; color: #4a5a52; cursor: pointer;
}
.day-tab:hover:not(.active) { background: #f1f6f2; color: #004d3a; }
.day-tab.active { background: #004d3a; color: #fff; box-shadow: 0 8px 16px -10px rgba(0, 77, 58, 0.9); }
.day-warn-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #e0a100; margin-left: 6px; }

/* ---------- VIEW: DAY + MEALS ---------- */
.mp-dayhead { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding-bottom: 16px; margin-bottom: 16px; border-bottom: 1px solid #eef2ef; }
.mp-dayhead h3 { margin: 0; font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700; color: #0e3a2c; }
.mp-dayhead span { padding: 5px 12px; border-radius: 999px; background: #e3efe7; font-size: 12.5px; font-weight: 800; color: #004d3a; white-space: nowrap; }
.meal-list { display: flex; flex-direction: column; gap: 14px; }
.meal-block { border: 1px solid #eef2ef; border-radius: 18px; overflow: hidden; background: #fff; }
.meal-head, .meal-edit-header {
  display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-left: 4px solid var(--mc);
  background: linear-gradient(90deg, var(--mb), rgba(255, 255, 255, 0) 85%);
}
.meal-ico { flex-shrink: 0; width: 38px; height: 38px; border-radius: 12px; background: #fff; color: var(--mc); display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06); }
.meal-name, .meal-edit-label { margin: 0; font-size: 16px; font-weight: 800; color: #0e3a2c; }
.meal-time { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 10px; border-radius: 999px; background: #fff; border: 1px solid #e4ebe6; font-size: 12.5px; font-weight: 700; color: #4a5a52; font-variant-numeric: tabular-nums; }
.meal-tw { overflow-x: auto; }
.meal-foods { width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; }
/* same column widths in every meal, so the numbers line up down the day */
.meal-foods th:nth-child(1) { width: 34%; }
.meal-foods th:nth-child(2) { width: 24%; }
.meal-foods th { padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 800; color: #6b7d73; background: #f7faf8; border-bottom: 1px solid #eef2ef; white-space: nowrap; }
.meal-foods th.c, .food-table-head .c { color: #9a7300; }
.meal-foods th.p, .food-table-head .p { color: #1f7a4d; }
.meal-foods th.f, .food-table-head .f { color: #3b5ba5; }
.meal-foods td { padding: 11px 16px; border-bottom: 1px solid #f3f6f4; color: #22362c; vertical-align: top; }
.meal-foods tbody tr:nth-child(even) td { background: #fbfcfb; }
.meal-foods tbody tr:hover td { background: #f3f8f5; }
.meal-foods .food { font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.meal-foods .portion { font-size: 13px; color: #6b7d73; }
.meal-foods .n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.meal-foods .k { font-weight: 800; color: #0e3a2c; }
.meal-foods tfoot td { padding: 10px 16px; border-bottom: none; background: #f7faf8; font-size: 13px; font-weight: 800; color: #1f5c45; }
.meal-empty { margin: 0; padding: 14px 18px; font-size: 13.5px; color: #8a9a91; }
.plan-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-top: 18px; padding-top: 16px; border-top: 1px solid #eef2ef; }
.plan-foot p { display: flex; align-items: center; gap: 8px; margin: 0; font-size: 12.5px; color: #6b7d73; }

/* ---------- BUTTONS ---------- */
.btn-primary, .btn-secondary, .btn-danger {
  display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 42px; padding: 0 16px; border-radius: 12px;
  font-size: 13.5px; font-weight: 800; line-height: 1.2; cursor: pointer; white-space: nowrap; border: 1px solid transparent;
}
.btn-primary { background: #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.btn-primary:hover:not(:disabled) { background: #00382a; }
.btn-secondary { background: #f1f6f2; border-color: #dce8e0; color: #004d3a; }
.btn-secondary:hover:not(:disabled) { background: #e3efe7; }
.btn-danger { background: #fef3f2; border-color: #f6cfcb; color: #b42318; }
.btn-danger:hover:not(:disabled) { background: #fde4e1; }
.btn-danger.solid { background: #c0392b; border-color: #c0392b; color: #fff; }
.btn-danger.solid:hover:not(:disabled) { background: #a93226; }
.btn-primary:disabled, .btn-secondary:disabled, .btn-danger:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }

/* ---------- SIDE: TOTALS ---------- */
.mp-ring-row { display: flex; align-items: center; gap: 16px; padding: 16px; border-radius: 18px; background: #f7faf8; }
.mp-ring { flex-shrink: 0; width: 112px; height: 112px; border-radius: 50%; display: grid; place-items: center; background: conic-gradient(#004d3a calc(var(--p, 0) * 1%), #e3ebe6 0); }
.mp-ring > span { width: 88px; height: 88px; border-radius: 50%; background: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.mp-ring strong { font-family: 'Playfair Display', serif; font-size: 19px; line-height: 1.1; color: #0e3a2c; }
.mp-ring small { margin-top: 2px; font-size: 10.5px; color: #6b7d73; }
.mp-ring-note { min-width: 0; }
.mp-ring-note p { margin: 8px 0 0; font-size: 12.5px; line-height: 1.45; color: #6b7d73; }
.mp-ok { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 999px; background: #e3f4ea; color: #1f7a4d; font-size: 12px; font-weight: 800; }
.mp-ok.off { background: #fff4d6; color: #8a6500; }
.nutrient-row { margin-top: 16px; }
.nutrient-top { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 7px; font-size: 13px; color: #6b7d73; }
.nutrient-top > span:first-child { display: inline-flex; align-items: center; gap: 8px; font-weight: 700; color: #22362c; }
.nutrient-top strong { color: #0e3a2c; }
.dot { width: 9px; height: 9px; border-radius: 3px; }
.nutrient-bar { height: 8px; border-radius: 999px; background: #eef2ef; overflow: hidden; }
.nutrient-fill { height: 100%; border-radius: 999px; transition: width 0.3s; }
.fill-green { background: #1f9d55; }
.fill-gold { background: #c49102; }
.fill-blue { background: #3b5ba5; }
.exchange-note, .macro-note { margin: 14px 0 0; font-size: 12px; color: #8a9a91; }

/* ---------- SIDE: INSTRUCTIONS / PLANS ---------- */
.instr-allergy { display: flex; gap: 8px; align-items: flex-start; margin: 0 0 14px; padding: 10px 12px; border-radius: 12px; background: #fef3f2; border: 1px solid #f6cfcb; font-size: 13px; font-weight: 700; line-height: 1.45; color: #912018; }
.instr-allergy svg { flex-shrink: 0; margin-top: 1px; color: #c0392b; }
.instr-read { margin: 0; }
.instr-read dt { margin: 0 0 6px; font-size: 11.5px; font-weight: 800; color: #6b7d73; }
.instr-read dd { margin: 0 0 14px; padding: 12px 14px; border-radius: 12px; background: #f7faf8; font-size: 13.5px; line-height: 1.55; color: #22362c; white-space: pre-line; overflow-wrap: anywhere; }
.instr-read dd:last-child { margin-bottom: 0; }
.instr-read dd.empty { color: #8a9a91; font-style: italic; }
.saved-plan-card {
  display: flex; justify-content: space-between; align-items: center; gap: 10px; width: 100%; margin-top: 8px; padding: 12px 14px;
  border-radius: 14px; background: #f7faf8; border: 1.5px solid transparent; text-align: left; cursor: pointer; transition: border-color 0.15s, background 0.15s;
}
.saved-plan-card:hover { border-color: #cfddd4; background: #fff; }
.saved-plan-card.selected { border-color: #004d3a; background: #fff; box-shadow: 0 8px 18px -12px rgba(0, 77, 58, 0.5); }
.saved-plan-name { font-size: 13.5px; font-weight: 800; color: #0e3a2c; }
.saved-plan-meta { margin-top: 2px; font-size: 12px; color: #6b7d73; }
.active-pill { flex-shrink: 0; padding: 4px 10px; border-radius: 999px; background: #e3f4ea; color: #1f7a4d; font-size: 11.5px; font-weight: 800; }
.active-pill.pill-draft { background: #fff4d6; color: #8a6500; }
.active-pill.pill-archived { background: #eef2ef; color: #6b7d73; }

/* ---------- EDIT: NOTICE ---------- */
.mp-note { display: flex; align-items: center; gap: 12px; padding: 12px 14px 12px 12px; border-radius: 16px; background: #fffbea; border: 1px solid #f3e2a0; }
.mp-note.sent { background: #f1f6f2; border-color: #d6e5db; }
.mp-note-ico { flex-shrink: 0; width: 36px; height: 36px; border-radius: 11px; background: #fbf1c7; color: #9a7300; display: inline-flex; align-items: center; justify-content: center; }
.mp-note.sent .mp-note-ico { background: #e3efe7; color: #004d3a; }
.sent-lock { flex: 1; margin: 0; font-size: 13.5px; line-height: 1.5; color: #5e4b0c; }
.mp-note.sent .sent-lock { color: #2c4a3c; }
.sent-lock strong { color: #3d3005; }
.mp-note-acts { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.mp-ghost { min-height: 40px; padding: 0 14px; border: none; border-radius: 12px; background: transparent; font-size: 13.5px; font-weight: 700; color: #6b5a1e; cursor: pointer; }
.mp-ghost:hover { background: rgba(0, 0, 0, 0.05); }

/* ---------- EDIT: NEW PLAN CHOICE ---------- */
.no-plan-title { margin: 0 0 16px; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.start-options { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.start-opt {
  display: flex; flex-direction: column; gap: 6px; padding: 16px; text-align: left; cursor: pointer;
  background: #fff; border: 1.5px solid #e4ebe6; border-radius: 16px; transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
}
.start-opt:hover { border-color: #9ec4ad; }
.start-opt.on { border-color: #004d3a; background: #f4f9f6; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.08); }
.start-ico { width: 38px; height: 38px; margin-bottom: 4px; border-radius: 12px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.start-opt.on .start-ico { background: #004d3a; color: #fff; }
.start-name { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; font-size: 14.5px; font-weight: 800; color: #0e3a2c; }
.start-rec { padding: 2px 9px; border-radius: 999px; background: #efbf04; font-size: 11px; font-weight: 800; color: #004d3a; }
.start-desc { font-size: 13px; line-height: 1.5; color: #4a5a52; }

/* ---------- EDIT: PLAN DETAILS ---------- */
.prefill-note { margin: -4px 0 16px; padding: 10px 12px; border-radius: 12px; background: #f1f6f2; font-size: 12.5px; color: #2c4a3c; }
.form-row-6 { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 14px; align-items: end; }
.field { display: flex; flex-direction: column; gap: 7px; min-width: 0; }
.field + .field { margin-top: 14px; }
.form-row-6 .field + .field { margin-top: 0; }
.field label { font-size: 12px; font-weight: 800; color: #6b7d73; }
.field input, .field textarea, .field .nm-select {
  width: 100%; min-height: 46px; padding: 0 14px; box-sizing: border-box; border: 1.5px solid #e4ebe6; border-radius: 12px;
  background-color: #fbfcfb; font-family: inherit; font-size: 14px; font-weight: 600; color: #14261e; transition: border-color 0.15s, box-shadow 0.15s, background-color 0.15s;
}
.field textarea { padding: 12px 14px; line-height: 1.55; font-weight: 500; resize: vertical; }
.field input:hover, .field textarea:hover, .field .nm-select:hover { border-color: #cfddd4; }
.field input:focus, .field textarea:focus, .field .nm-select:focus { outline: none; background-color: #fff; border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.field input.invalid { border-color: #e2a39b; background-color: #fff8f7; }
.unit-in { display: flex; align-items: center; height: 46px; border: 1.5px solid #e4ebe6; border-radius: 12px; background: #fbfcfb; overflow: hidden; transition: border-color 0.15s, box-shadow 0.15s; }
.unit-in:focus-within { border-color: #004d3a; background: #fff; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.field .unit-in input, .unit-in input { flex: 1; min-width: 0; height: 100%; min-height: 0; padding: 0 14px; border: none; border-radius: 0; background: transparent; box-shadow: none; outline: none; font-family: inherit; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.unit-in span { flex-shrink: 0; padding: 0 14px; font-size: 12.5px; font-weight: 700; color: #8a9a91; }
.targets-section { margin-top: 20px; padding-top: 18px; border-top: 1px solid #eef2ef; }
.targets-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.targets-title { font-size: 15px; font-weight: 800; color: #0e3a2c; }
.optional { margin-left: 6px; padding: 2px 8px; border-radius: 999px; background: #f3f6f4; font-size: 11px; font-weight: 700; color: #6b7d73; }
.targets-hint { margin: 4px 0 12px; max-width: 640px; font-size: 12.5px; line-height: 1.5; color: #6b7d73; }
.targets-add-btn { display: inline-flex; align-items: center; gap: 6px; min-height: 34px; padding: 0 14px; border: 1px solid #dce8e0; border-radius: 999px; background: #f1f6f2; font-size: 12.5px; font-weight: 800; color: #004d3a; cursor: pointer; }
.targets-add-btn:hover { background: #e3efe7; }
.mp-macros { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.mp-macro { display: flex; flex-direction: column; gap: 8px; padding: 14px; border-radius: 16px; background: #fff; border: 1px solid #eef2ef; border-top: 3px solid var(--c); }
.mp-macro-l { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 800; color: #22362c; }
.mp-macro-l i { width: 9px; height: 9px; border-radius: 3px; background: var(--c); }
.targets-row { display: grid; grid-template-columns: 1.4fr 1fr 0.8fr auto; gap: 10px; align-items: center; margin-bottom: 8px; }
.targets-row > input, .targets-row :deep(.combo input) {
  width: 100%; min-height: 44px; padding: 0 12px; box-sizing: border-box; border: 1.5px solid #e4ebe6; border-radius: 12px;
  background: #fbfcfb; font-family: inherit; font-size: 14px; color: #14261e;
}
.targets-row > input:focus, .targets-row :deep(.combo input:focus) { outline: none; background: #fff; border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.targets-remove-btn { display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border: none; border-radius: 12px; background: #fef3f2; color: #b42318; cursor: pointer; }
.targets-remove-btn:hover { background: #fde4e1; }
.create-btn { margin-top: 18px; }
.create-hint { margin: 8px 0 0; font-size: 12.5px; color: #6b7d73; }

/* ---------- EDIT: DAY ROW / COPY ---------- */
.day-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.copy-day { display: flex; align-items: center; gap: 8px; padding: 5px 5px 5px 14px; border-radius: 999px; background: #fff; border: 1px solid #e4ebe6; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04); }
.copy-day label { font-size: 13px; font-weight: 700; color: #4a5a52; white-space: nowrap; }
.copy-day .nm-select { min-height: 36px; height: 36px; width: 170px; border-radius: 999px; font-size: 13px; }
.copy-day .btn-secondary { min-height: 36px; border-radius: 999px; }
.copy-hint { margin: -8px 0 0; font-size: 12.5px; color: #6b7d73; text-align: right; }

/* ---------- EDIT: MEALS ---------- */
.meals-panel { padding: 22px; }
.meal-edit-panel { border: 1px solid #eef2ef; border-radius: 18px; background: #fff; } /* no overflow:hidden — the food picker list must show past the card */
.meal-edit-panel + .meal-edit-panel { margin-top: 14px; }
.meal-edit-header { border-radius: 17px 17px 0 0; }
.meal-time-pill { display: inline-flex; align-items: center; gap: 6px; height: 30px; padding: 0 6px 0 10px; border-radius: 999px; background: #fff; border: 1px solid #e4ebe6; color: #4a5a52; }
.meal-time-input { border: none; outline: none; background: transparent; padding: 0; font-family: inherit; font-size: 12.5px; font-weight: 700; color: #22362c; }
.food-table { --cols: minmax(0, 2.2fr) minmax(0, 1.5fr) repeat(4, minmax(0, 0.7fr)) 34px; }
.food-table-head, .food-table-row, .meal-foot { display: grid; grid-template-columns: var(--cols); gap: 8px; align-items: center; padding: 0 14px; }
.food-table-head { padding-top: 10px; padding-bottom: 10px; background: #f7faf8; border-bottom: 1px solid #eef2ef; font-size: 11px; font-weight: 800; color: #6b7d73; white-space: nowrap; }
.food-table-head > span:first-child, .food-table-head > span:nth-child(2) { padding-left: 12px; }
.food-table-head .n { text-align: right; padding-right: 12px; }
.food-table-row { position: relative; padding-top: 8px; padding-bottom: 8px; border-bottom: 1px solid #f3f6f4; transition: background 0.15s; }
.food-table-row:hover { background: #fafcfb; }
.food-table-row input {
  width: 100%; height: 38px; padding: 0 10px; box-sizing: border-box; border: 1.5px solid transparent; border-radius: 10px;
  background: transparent; font-family: inherit; font-size: 14px; color: #22362c; transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}
.food-table-row input:not(:disabled) { cursor: text; }
.food-table-row:hover input:not(:disabled) { background: #fff; border-color: #e4ebe6; }
.food-table-row input:focus { outline: none; background: #fff !important; border-color: #004d3a !important; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.1); }
.combo { position: relative; min-width: 0; }
.combo input { font-weight: 700; color: #0e3a2c; }
.portion-in, .mp-num input:not(:disabled) { background: #f7faf8 !important; border-color: #e4ebe6 !important; }
.mp-num { display: block; min-width: 0; }
.mp-num input { text-align: right; font-variant-numeric: tabular-nums; }
.mp-num input:disabled { opacity: 1; color: #22362c; -webkit-text-fill-color: #22362c; cursor: default; }
.mp-num.k input { font-weight: 800; color: #0e3a2c; -webkit-text-fill-color: #0e3a2c; }
.grams-input { display: flex; align-items: center; gap: 8px; min-width: 0; }
.grams-input input { flex-shrink: 0; width: 62px; text-align: center; font-weight: 800; background: #f1f6f2 !important; border-color: #e1eae4 !important; }
.grams-input span { min-width: 0; font-size: 12.5px; line-height: 1.3; color: #6b7d73; overflow-wrap: anywhere; }
.usda-name { min-width: 0; padding: 0 10px; font-size: 14px; font-weight: 700; line-height: 1.35; color: #0e3a2c; overflow-wrap: anywhere; }
.usda-tag { display: inline-block; margin-right: 6px; padding: 1px 6px; border-radius: 6px; background: #eef1fa; font-size: 10.5px; font-weight: 800; color: #3b5ba5; vertical-align: 1px; }
.remove-btn { width: 32px; height: 32px; border: none; border-radius: 10px; background: transparent; color: #a8b5ae; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; }
.remove-btn:hover { background: #fef3f2; color: #b42318; }
.food-hint { grid-column: 1 / -1; margin: 2px 0 4px; padding: 8px 12px; border-radius: 10px; background: #f2f6f3; border: 1px dashed #9ec4ad; font-size: 12.5px; line-height: 1.4; color: #2c4a3c; }
.food-warn { grid-column: 1 / -1; display: flex; align-items: flex-start; gap: 6px; margin: 2px 0 4px; padding: 8px 12px; border-radius: 10px; background: #fff6e5; border: 1px solid #f3dcae; font-size: 12.5px; font-weight: 700; line-height: 1.4; color: #9a5b00; }
.food-warn svg { flex-shrink: 0; margin-top: 1px; }
.food-warn.allergy { color: #b3261e; background: #fdecea; border-color: #f2b8b5; }
.meal-foot { padding-top: 10px; padding-bottom: 12px; background: #f7faf8; border-radius: 0 0 17px 17px; }
.meal-foot .add-food-row { grid-column: span 2; display: flex; flex-wrap: wrap; gap: 6px; }
.meal-foot.empty .add-food-row { grid-column: 1 / -1; }
.mf-n { padding-right: 12px; text-align: right; font-size: 13px; font-weight: 800; color: #1f5c45; font-variant-numeric: tabular-nums; white-space: nowrap; }
.mf-n.k { color: #0e3a2c; }
.btn-add-food {
  display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border: 1px dashed #bfd3c6; border-radius: 999px;
  background: #fff; font-size: 12.5px; font-weight: 800; color: #004d3a; cursor: pointer;
}
.btn-add-food:hover { border-style: solid; border-color: #004d3a; }
.usda-btn { color: #3b5ba5; border-color: #cfd8ea; }
.usda-btn:hover { border-color: #3b5ba5; }
.combo-list { position: absolute; z-index: 20; top: calc(100% + 6px); left: 0; width: max(100%, 340px); max-height: 280px; overflow-y: auto; padding: 6px; background: #fff; border: 1px solid #e4ebe6; border-radius: 14px; box-shadow: 0 18px 36px -12px rgba(16, 35, 27, 0.3); }
.combo-group { margin: 8px 8px 4px; font-size: 11px; font-weight: 800; color: #6b7d73; }
.combo-opt { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; width: 100%; padding: 8px 10px; border: none; border-radius: 10px; background: none; text-align: left; font-size: 13.5px; color: #0e3a2c; cursor: pointer; }
.combo-opt:hover, .combo-opt.on { background: #f1f6f2; }
.combo-meta { font-size: 12px; color: #8a9a91; white-space: nowrap; }
.combo-allergy { margin-left: 6px; padding: 0 6px; border-radius: 6px; background: #fdecea; border: 1px solid #f2b8b5; font-size: 10.5px; font-weight: 800; color: #b3261e; vertical-align: 1px; }
.mp-mbar { display: none; }

/* ---------- EDIT: PREVIEW ---------- */
.preview-day { padding: 4px 10px; border-radius: 999px; background: #f1f6f2; font-size: 12px; font-weight: 800; color: #004d3a; }
.preview-summary-name { margin: 0 0 8px; font-size: 14.5px; font-weight: 800; color: #0e3a2c; }
.plan-badges { display: flex; flex-wrap: wrap; gap: 6px; }
.badge { padding: 4px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 800; }
.badge-blue { background: #eef1fa; color: #3b5ba5; }
.badge-gold { background: #fbf3d2; color: #9a7300; }
.target-list { display: flex; flex-direction: column; gap: 8px; margin-top: 14px; padding-top: 14px; border-top: 1px solid #eef2ef; }
.target-row { display: flex; justify-content: space-between; gap: 12px; font-size: 13px; color: #4a5a52; }
.target-row span:last-child { font-weight: 700; color: #22362c; white-space: nowrap; }
.target-ter { font-weight: 800; color: #0e3a2c; }
.target-list-title { margin: 0; font-size: 13.5px; font-weight: 800; color: #0e3a2c; }
.target-list-title span { font-weight: 500; color: #8a9a91; }
.preview-list { display: flex; flex-direction: column; margin-top: 14px; }
.preview-item { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-top: 1px solid #f0f3f1; }
.preview-ico { flex-shrink: 0; width: 32px; height: 32px; border-radius: 10px; background: var(--mb); color: var(--mc); display: inline-flex; align-items: center; justify-content: center; }
.preview-body { flex: 1; min-width: 0; }
.preview-label { font-size: 13px; font-weight: 800; color: #0e3a2c; }
.preview-food { font-size: 12px; color: #6b7d73; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.preview-kcal { flex-shrink: 0; font-size: 12px; font-weight: 800; color: var(--mc); }

/* ---------- MODALS (send check) ---------- */
.send-check { max-width: 540px; }
.send-consequence { display: flex; gap: 8px; align-items: flex-start; margin: 0 0 14px; padding: 12px 14px; background: #f1f6f2; border-radius: 12px; font-size: 13px; color: #2c4a3c; line-height: 1.5; }
.send-consequence svg { flex-shrink: 0; margin-top: 2px; }
.send-section { display: flex; align-items: center; gap: 6px; margin: 12px 0 8px; font-size: 13px; font-weight: 800; color: #7a5a1a; }
.send-section.allergy { color: #b3261e; }
.send-check-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; max-height: 45vh; overflow-y: auto; }
.send-check-list li { display: flex; flex-direction: column; gap: 2px; padding: 10px 12px; border-radius: 12px; background: #fff6e5; border: 1px solid #f3dcae; font-size: 12.5px; color: #5a4a2a; }
.send-check-list strong { color: #0e3a2c; font-weight: 800; }
.send-check-list.allergy li { background: #fdecea; border-color: #f2b8b5; color: #8c1d18; }
.send-check-meal { text-transform: capitalize; }
.allergy-ack { display: flex; gap: 8px; align-items: flex-start; margin-top: 10px; font-size: 13px; font-weight: 700; color: #8c1d18; cursor: pointer; }
.allergy-ack input { margin-top: 2px; accent-color: #b3261e; }

/* ---------- PRINT ---------- */
.print-only { display: none; }
.screen-hidden { display: none; }
.instructions-view { margin-top: 16px; padding: 14px 16px; background: #fafbfa; border-radius: 8px; }
.instructions-view p { font-size: 0.8rem; color: #4a5a4a; margin: 0 0 6px; line-height: 1.5; }
.instructions-view p:last-child { margin: 0; }
.print-head h3 { margin: 0 0 4px; font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; }
.print-head p { margin: 0 0 10px; font-size: 0.85rem; color: #4a5a4a; }

@media print {
  :global(body *) { visibility: hidden; }
  .print-area, .print-area * { visibility: visible; }
  .print-area { position: absolute; left: 0; top: 0; width: 100%; border: none; box-shadow: none !important; padding: 0; }
  .no-print { display: none !important; }
  .print-only { display: block; }
  .screen-hidden { display: block; }
  .print-day { break-inside: avoid; margin-bottom: 14px; }
  .print-day-title { font-size: 0.95rem; color: #1a3a1a; margin: 12px 0 6px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
  .meal-list { gap: 8px; }
  .meal-block { border-color: #ddd; border-radius: 6px; }
  .meal-head { background: none; padding: 6px 10px; }
  .meal-foods th, .meal-foods td, .meal-foods tfoot td { padding: 4px 8px; font-size: 0.78rem; background: none !important; }
}

/* ---------- TABLET ---------- */
@media (max-width: 1200px) {
  .mp-targets { grid-template-columns: repeat(4, minmax(0, 1fr)); flex-basis: 100%; }
}
@media (max-width: 1150px) {
  .planning-layout { grid-template-columns: minmax(0, 1fr); }
  .form-row-6 { grid-template-columns: 1fr 1fr; }
  .form-row-6 .field:first-child { grid-column: 1 / -1; }
}

/* ---------- PHONE ---------- */
@media (max-width: 760px) {
  .meal-planning-page { padding-bottom: 110px; }
  .mp-top { margin-bottom: 14px; }
  .mode-toggle { flex: 1; }
  .mode-btn { flex: 1; padding: 0 12px; }
  .panel, .meals-panel { padding: 16px; border-radius: 20px; }
  .mp-hero { padding: 20px 18px; border-radius: 22px; gap: 16px; }
  .mp-hero-plate { width: 220px; height: 220px; right: -80px; top: 60px; transform: none; opacity: 0.5; }
  .mp-hero-who { flex-basis: 100%; gap: 12px; }
  .mp-av { width: 48px; height: 48px; font-size: 18px; }
  .mp-title { font-size: 24px; }
  .mp-sub { font-size: 13px; }
  .mp-targets { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .mp-t strong { font-size: 21px; }
  .mp-hero-acts { display: grid; grid-template-columns: 1fr 1fr; }
  .mp-hero-acts .gold { grid-column: 1 / -1; order: -1; }
  .mp-hero-acts.edit { display: none; }
  .day-tabs { width: 100%; }
  .day-tab { min-width: 0; flex: 1 0 auto; padding: 0 12px; }
  .mp-dayhead h3 { font-size: 21px; }
  .meal-head, .meal-edit-header { flex-wrap: wrap; gap: 8px 10px; padding: 10px 12px; }
  .meal-ico { width: 34px; height: 34px; }

  /* view: food and portion on top, numbers in four labelled cells */
  .meal-foods thead { display: none; }
  .meal-foods, .meal-foods tbody, .meal-foods tfoot, .meal-foods tr, .meal-foods td { display: block; }
  .meal-foods tbody tr, .meal-foods tfoot tr { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 4px 8px; padding: 12px; border-bottom: 1px solid #f3f6f4; }
  .meal-foods td, .meal-foods tfoot td { padding: 0; border: none; background: none !important; }
  .meal-foods .food, .meal-foods .portion, .meal-foods tfoot td:first-child { grid-column: 1 / -1; }
  .meal-foods .portion { margin-bottom: 6px; }
  .meal-foods .n { text-align: left; font-size: 13px; }
  .meal-foods tfoot tr { background: #f7faf8; border-bottom: none; }
  .meal-foods td.n::before { display: block; font-size: 10px; font-weight: 800; color: #8a9a91; }
  .meal-foods td.n:nth-child(3)::before { content: 'kcal'; }
  .meal-foods td.n:nth-child(4)::before { content: 'Carbs'; }
  .meal-foods td.n:nth-child(5)::before { content: 'Protein'; }
  .meal-foods td.n:nth-child(6)::before { content: 'Fat'; }
  .meal-foods tfoot td.n:nth-child(2)::before { content: 'kcal'; }
  .meal-foods tfoot td.n:nth-child(3)::before { content: 'Carbs'; }
  .meal-foods tfoot td.n:nth-child(4)::before { content: 'Protein'; }
  .meal-foods tfoot td.n:nth-child(5)::before { content: 'Fat'; }

  /* edit: notice, form, day row */
  .mp-note { flex-wrap: wrap; }
  .sent-lock { flex-basis: calc(100% - 48px); font-size: 12.5px; }
  .mp-note-acts { width: 100%; }
  .mp-note-acts > * { flex: 1; }
  .start-options { grid-template-columns: 1fr; }
  .form-row-6, .mp-macros { grid-template-columns: minmax(0, 1fr); }
  .targets-header { flex-wrap: wrap; }
  .targets-row { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto; }
  .targets-row > :first-child { grid-column: 1 / -1; }
  .copy-day { width: 100%; box-sizing: border-box; flex-wrap: wrap; padding: 12px; border-radius: 16px; }
  .copy-day label { width: 100%; }
  .copy-day .nm-select { flex: 1; width: auto; min-width: 0; }
  .copy-hint { text-align: left; }

  /* edit: each food is a small card */
  .food-table-head { display: none; }
  .food-table-row { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; padding: 12px; }
  .food-table-row > .combo, .food-table-row > .usda-name { grid-column: 1 / -1; padding-right: 40px; }
  .food-table-row > .usda-name { padding-left: 0; }
  .food-table-row > .grams-input, .food-table-row > .portion-in { grid-column: 1 / -1; }
  .food-table-row input:not(:disabled) { background: #fbfcfb; border-color: #e4ebe6; }
  .remove-btn { position: absolute; top: 15px; right: 10px; }
  .mp-num::before, .mf-n::before { content: attr(data-l); display: block; margin-bottom: 3px; font-size: 10px; font-weight: 800; color: #8a9a91; }
  .mp-num input { height: 36px; text-align: left; }
  .mp-num input:disabled { padding-left: 0; }
  .meal-foot { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px 8px; padding: 12px; }
  .meal-foot .add-food-row { grid-column: 1 / -1; }
  .btn-add-food { flex: 1; justify-content: center; height: 40px; white-space: nowrap; }
  .mf-n { padding: 0; text-align: left; }
  .mf-gap { display: none; }
  .combo-list { position: static; width: 100%; margin-top: 6px; box-shadow: none; overflow-x: hidden; }
  .combo-opt { flex-direction: column; align-items: flex-start; gap: 2px; }
  .combo-meta { white-space: normal; }
  .mp-mbar {
    position: sticky; bottom: 84px; z-index: 5; display: grid; grid-template-columns: auto 1fr 1.3fr; gap: 8px; padding: 10px;
    border-radius: 18px; background: rgba(255, 255, 255, 0.97); border: 1px solid #e4ebe6; box-shadow: 0 18px 36px -18px rgba(16, 35, 27, 0.45);
  }
  .mp-mbar .btn-secondary:first-child { width: 44px; padding: 0; }
  .mp-ring { width: 100px; height: 100px; }
  .mp-ring > span { width: 78px; height: 78px; }
  .saved-plan-card { gap: 10px; }
}
</style>
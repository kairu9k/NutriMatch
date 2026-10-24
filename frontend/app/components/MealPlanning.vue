<template>
  <div class="meal-planning-page">
    <!-- TOP CONTROLS (once a patient is chosen) -->
    <button v-if="selectedRelId && !isLoading" type="button" class="back-link no-print" @click="backToList">
      <ChevronLeft :size="15" /> All patients
    </button>
    <div v-if="selectedRelId && !isLoading" class="top-controls no-print">
      <div class="mode-toggle">
        <button class="mode-btn" :class="{ active: mode === 'view' }" :disabled="!patients.length" @click="showView">
          <Eye :size="15" /> View plan
        </button>
        <button class="mode-btn" :class="{ active: mode === 'create' }" :disabled="!patients.length" @click="openCreate">
          <Plus :size="15" /> {{ selectedPlan ? 'Edit plan' : 'Create plan' }}
        </button>
      </div>

    </div>

    <p v-if="errorMessage" class="form-error no-print">{{ errorMessage }}</p>
    <p v-if="notice" class="form-notice no-print"><CheckCircle2 :size="15" /> {{ notice }}</p>

    <p v-if="isLoading" class="macro-note">Loading…</p>

    <div v-else-if="!patients.length" class="empty-state">
      <p class="empty-title">No active patients yet</p>
      <p class="macro-note">Meal plans can be created once a client's first appointment is confirmed.</p>
    </div>

    <!-- START: choose a patient (opening from the sidebar) -->
    <MealPlanPatientList v-else-if="!selectedRelId" class="no-print" @pick="pickPatient" />

    <!-- ================= VIEW PLANS MODE ================= -->
    <div v-else-if="mode === 'view' && !selectedPlan" class="empty-state">
      <p class="empty-title">No meal plan yet for {{ selectedPatientName }}</p>
      <button class="btn-primary" @click="startNewPlan"><Plus :size="15" /> Create meal plan</button>
    </div>

    <div v-else-if="mode === 'view'" class="planning-layout">
      <div class="panel plan-panel print-area">
        <div class="plan-header">
          <div>
            <h3>Weekly meal plan for {{ selectedPatientName }}</h3>
            <p class="plan-subtitle">{{ planMeta.name }}. <span class="status-text">{{ statusLabel(selectedPlan.status) }}</span></p>
          </div>
          <div class="plan-badges">
            <span v-if="planMeta.kcalPerDay" class="badge badge-blue">{{ Number(planMeta.kcalPerDay).toLocaleString('en-PH') }} kcal/day</span>
            <span class="badge badge-gold">{{ conditionLabel(planMeta.condition) }}</span>
          </div>
        </div>

        <div class="day-tabs no-print">
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

        <!-- Screen: selected day. Print: the whole week. -->
        <div v-for="day in printDays" :key="day" class="print-day" :class="{ 'screen-hidden': day !== activeDay }">
          <h4 class="print-only print-day-title">{{ DAY_FULL[day] }}</h4>
          <div class="meal-list">
            <!-- one small table per meal: food, portion, kcal and macros in lined-up columns -->
            <section v-for="meal in mealsForDay(day)" :key="meal.type" class="meal-block">
              <div class="meal-head">
                <h4 class="meal-name">{{ sentence(meal.type) }}</h4>
                <span v-if="meal.time" class="meal-time">{{ formatTime(meal.time) }}</span>
                <span class="meal-kcal">{{ meal.kcal }} kcal</span>
              </div>
              <table v-if="meal.foods.length" class="meal-foods">
                <thead>
                  <tr><th>Food</th><th>Portion</th><th class="n">kcal</th><th class="n">Carbs</th><th class="n">Protein</th><th class="n">Fat</th></tr>
                </thead>
                <tbody>
                  <tr v-for="(f, i) in meal.foods" :key="i">
                    <td class="food">{{ f.name }}</td>
                    <td class="portion">{{ f.portion || '' }}</td>
                    <td class="n">{{ cell(f.kcal) }}</td>
                    <td class="n">{{ cell(f.carb) }} g</td>
                    <td class="n">{{ cell(f.prot) }} g</td>
                    <td class="n">{{ cell(f.fat) }} g</td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="meal-empty">No foods added</p>
            </section>
          </div>
        </div>

        <div v-if="instructions.allergies || instructions.notes" class="instructions-view print-only">
          <p v-if="instructions.allergies"><strong>Allergies and restrictions:</strong> {{ instructions.allergies }}</p>
          <p v-if="instructions.notes"><strong>Notes from the RND:</strong> {{ instructions.notes }}</p>
        </div>

        <div class="plan-actions no-print">
          <button v-if="selectedPlan.status === 'draft'" class="btn-danger" type="button" @click="confirmDelete = true"><Trash2 :size="15" /> Delete draft</button>
          <button class="btn-secondary" @click="printPlan"><Printer :size="15" /> Print plan</button>
          <button class="btn-secondary" @click="mode = 'create'"><Pencil :size="15" /> Edit plan</button>
          <button class="btn-primary" :disabled="isSending" @click="requestSend(sendToPatient)">
            <Send :size="15" /> {{ isSending ? 'Sending…' : selectedPlan.status === 'active' ? 'Resend to patient' : 'Send to patient' }}
          </button>
        </div>
      </div>

      <!-- RIGHT SIDEBAR -->
      <div class="side-column no-print">
        <!-- same panel as in Edit plan, read-only here -->
        <div class="panel">
          <div class="side-header-row">
            <h4 class="side-title">Instructions for the patient</h4>
            <button class="nm-btn-soft nm-btn-sm" type="button" @click="mode = 'create'"><Pencil :size="13" aria-hidden="true" /> Edit</button>
          </div>
          <p v-if="patientAllergies.length" class="instr-allergy" role="note">
            <AlertTriangle :size="14" aria-hidden="true" /> {{ patientFirstName }}'s recorded allergies: {{ patientAllergies.join(', ') }}
          </p>
          <dl class="instr-read">
            <dt>Allergies and restrictions</dt>
            <dd :class="{ empty: !instructions.allergies }">{{ instructions.allergies || 'None written' }}</dd>
            <dt>Notes for the patient</dt>
            <dd :class="{ empty: !instructions.notes }">{{ instructions.notes || 'None written' }}</dd>
          </dl>
        </div>

        <div class="panel">
          <h4 class="side-title">{{ DAY_FULL[activeDay] }}'s totals</h4>
          <span class="side-subtitle">Against the plan's daily targets</span>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Calories</span><span>{{ Number(nutrition.calories.value).toLocaleString('en-PH') }} of {{ nutrition.calories.target != null ? Number(nutrition.calories.target).toLocaleString('en-PH') : '—' }} kcal</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-green" :style="{ width: pct(nutrition.calories) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Carbohydrates</span><span>{{ nutrition.carbs.value }} g of {{ nutrition.carbs.target ?? '—' }} g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-gold" :style="{ width: pct(nutrition.carbs) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Protein</span><span>{{ nutrition.protein.value }} g of {{ nutrition.protein.target ?? '—' }} g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-green" :style="{ width: pct(nutrition.protein) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Fat</span><span>{{ nutrition.fat.value }} g of {{ nutrition.fat.target ?? '—' }} g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-dark" :style="{ width: pct(nutrition.fat) + '%' }"></div></div>
          </div>
          <p class="exchange-note">FNRI values from the Food Exchange Lists, 4th ed., 2020</p>
        </div>

        <div class="panel">
          <div class="side-header-row">
            <h4 class="side-title">Plans for this patient</h4>
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

    <!-- ================= CREATE / EDIT PLAN MODE ================= -->
    <div v-else class="planning-layout">
      <div class="create-column">
        <!-- NEW PLAN: pick how to start first, so the two forms never sit on top of each other -->
        <div v-if="!selectedPlan" class="panel start-choice">
          <h4 class="no-plan-title">New meal plan for {{ selectedPatientName }}</h4>
          <div class="start-options" role="radiogroup" aria-label="How to start the plan">
            <button type="button" role="radio" class="start-opt" :class="{ on: startWith === 'template' }" :aria-checked="startWith === 'template'" @click="startWith = 'template'">
              <span class="start-name">Start from a diet template <span class="start-rec">Recommended</span></span>
              <span class="start-desc">Pick the condition and calories. A full week is filled in for you to check and adjust.</span>
            </button>
            <button type="button" role="radio" class="start-opt" :class="{ on: startWith === 'blank' }" :aria-checked="startWith === 'blank'" @click="startWith = 'blank'">
              <span class="start-name">Start blank</span>
              <span class="start-desc">Name the plan and set the calories, then add every meal yourself.</span>
            </button>
          </div>
        </div>

        <!-- disease-specific diet template (diabetes, hypertension, renal, weight management) -->
        <MealPlanTemplatePicker v-if="!selectedPlan && startWith === 'template'" :relationship-id="selectedRelId" @created="onTemplateCreated" />

        <!-- STEP 1: PLAN DETAILS (a new blank plan, or the plan being edited) -->
        <div v-if="selectedPlan || startWith === 'blank'" class="panel">
          <h4 class="side-title">Plan details</h4>
          <p v-if="!selectedPlan && ncpTargets" class="macro-note prefill-note">Targets are filled in from this client's NCP Intervention. Adjust them if needed.</p>

          <div class="form-row-6">
            <div class="field">
              <label>Plan name</label>
              <input v-model="planMeta.name" type="text" placeholder="e.g., Diabetic-Friendly Plan" />
            </div>
            <div class="field">
              <label>Condition</label>
              <select class="nm-select" v-model="planMeta.condition">
                <option v-for="c in CONDITIONS" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
            </div>
            <div class="field">
              <label>Target calories per day</label>
              <input v-model.number="planMeta.kcalPerDay" type="number" min="0" placeholder="e.g., 1800" />
            </div>
          </div>

          <!-- Targets beyond calories, as Measured Variable / Value / Unit rows
               (same pattern as the NCP form's "+ Add Field"), in two groups:
               the macronutrients (the only ones that give calories; in grams
               they drive the Macro Tracker) and other targets (sodium, fiber…),
               which are not part of the calorie target. -->
          <div class="targets-section">
            <div class="targets-header">
              <span class="targets-title">Macronutrient targets <span class="optional">(optional)</span></span>
            </div>
            <p class="targets-hint">Protein, carbohydrate and fat are the only nutrients that give calories (4 / 4 / 9 kcal per gram), so they make up the calorie target.</p>
            <!-- Fixed rows: only the value is edited (the Macro Tracker reads them by name, in grams). -->
            <div v-for="row in macroRows" :key="row.label" class="targets-row locked">
              <input :value="row.label" type="text" readonly tabindex="-1" :aria-label="`${row.label} target`" />
              <input v-model="row.value" type="text" inputmode="decimal" placeholder="Value" maxlength="100" :aria-label="`${row.label} value`" />
              <input :value="row.unit" type="text" readonly tabindex="-1" aria-label="Unit" />
              <span class="targets-remove-btn spacer" aria-hidden="true"><X :size="14" /></span>
            </div>
          </div>
          <div class="targets-section">
            <div class="targets-header">
              <span class="targets-title">Other targets <span class="optional">(optional)</span></span>
              <button type="button" class="targets-add-btn" @click="addTargetRow"><Plus :size="14" /> Add target</button>
            </div>
            <p class="targets-hint">Not counted in the calorie target, e.g. sodium, fiber, potassium, vitamins. Pick from the list or type your own.</p>
            <div v-for="(row, idx) in otherRows" :key="idx" class="targets-row">
              <MeasureNameCombo :row="row" :templates="MEASURE_TEMPLATES.intervention" :aria-label="`Target ${idx + 1} name`" />
              <input v-model="row.value" type="text" inputmode="decimal" placeholder="Value" maxlength="100" :aria-label="`Target ${idx + 1} value`" />
              <input v-model="row.unit" type="text" placeholder="Unit" maxlength="30" :aria-label="`Target ${idx + 1} unit`" />
              <button type="button" class="targets-remove-btn" title="Remove" @click="otherRows.splice(idx, 1)"><X :size="14" /></button>
            </div>
          </div>

          <button v-if="!selectedPlan" class="btn-primary" :disabled="!planMeta.name || !planMeta.kcalPerDay || isSaving" @click="createPlan">
            {{ isSaving ? 'Creating…' : 'Create meal plan' }}
          </button>
          <p v-if="!selectedPlan && createBlocker" class="create-hint">{{ createBlocker }} Then you can add the meals day by day.</p>
        </div>

        <!-- STEP 2: DAILY MEALS — only once the plan exists -->
        <template v-if="selectedPlan">
          <div class="day-tabs">
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
            <button type="button" class="btn-secondary" :disabled="!copyTarget || !dayHasFood(activeDay)" @click="copyDay">Copy</button>
            <span v-if="!dayHasFood(activeDay)" class="copy-hint">Add food to {{ DAY_FULL[activeDay] }} first.</span>
          </div>

          <div class="panel meal-edit-panel" v-for="meal in currentDayMeals" :key="meal.type">
            <div class="meal-edit-header">
              <span class="meal-edit-label"><component :is="meal.icon" :size="14" /> {{ sentence(meal.type) }}</span>
              <input v-model="weeklyPlan[activeDay][meal.type].time" type="time" class="meal-time-input" title="Meal time" />
            </div>

            <div class="food-table">
              <div class="food-table-head">
                <span></span>
                <span>Food</span>
                <span>Portion</span>
                <span>kcal</span>
                <span>Carbs (g)</span>
                <span>Protein (g)</span>
                <span>Fat (g)</span>
              </div>
              <div class="food-table-row" v-for="(item, idx) in meal.items" :key="idx" :class="{ usda: item.source === 'usda' }">
                <button class="remove-btn" title="Remove" @click="removeItem(meal, idx)"><X :size="12" /></button>
                <template v-if="item.source === 'usda'">
                  <div class="usda-name" :title="`USDA FoodData Central #${item.fdcId}`"><span class="usda-tag">USDA</span>{{ item.name }}</div>
                  <div class="grams-input">
                    <input :value="item.grams" type="number" min="1" max="2000" step="1" aria-label="Grams" @input="setGrams(item, $event.target.value)" />
                    <span>g</span>
                  </div>
                  <input :value="item.kcal ?? ''" type="number" disabled placeholder="—" title="From USDA, per the grams" />
                  <input :value="item.carb ?? ''" type="number" disabled placeholder="—" />
                  <input :value="item.prot ?? ''" type="number" disabled placeholder="—" />
                  <input :value="item.fat ?? ''" type="number" disabled placeholder="—" />
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
                  <input v-model="item.portion" type="text" placeholder="e.g., ½ cup" />
                  <input v-model.number="item.kcal" type="number" min="0" placeholder="0" />
                  <input v-model.number="item.carb" type="number" min="0" placeholder="0" />
                  <input v-model.number="item.prot" type="number" min="0" placeholder="0" />
                  <input v-model.number="item.fat" type="number" min="0" placeholder="0" />
                </template>
                <p v-if="needsNumbers(item)" class="food-hint">Enter its calories and macros, or pick a food from the FNRI list so they fill in.</p>
                <p v-if="itemWarnings(item).length" class="food-warn" :class="{ allergy: itemAllergyWarnings(item).length }" role="note">
                  <AlertTriangle :size="13" /> {{ itemWarnings(item).join(', ') }}
                </p>
              </div>
            </div>

            <div class="add-food-row">
              <button class="btn-add-food" @click="addItem(meal)"><Plus :size="14" /> Add food</button>
              <button class="btn-add-food usda-btn" @click="usdaMeal = meal"><Search :size="14" /> Add from USDA</button>
            </div>
          </div>

          <UsdaFoodPicker v-if="usdaMeal" :meal-label="`${activeDay}, ${usdaMeal.type}`" :allergies="patientAllergies" :patient-name="patientFirstName" @close="usdaMeal = null" @pick="addUsdaFood" />

          <p v-if="selectedPlan.status !== 'draft'" class="sent-lock"><Lock :size="13" /> Sent to the client, so this plan can't be deleted. Edit it and resend, or send a new plan.</p>
          <p v-else class="sent-lock"><Lock :size="13" /> Draft. Only you can see it, and you can still delete it. Once you send it to the client, it can't be deleted.</p>
          <div class="plan-actions create-actions">
            <button v-if="selectedPlan.status === 'draft'" class="btn-danger" type="button" @click="confirmDelete = true"><Trash2 :size="15" /> Delete draft</button>
            <button class="btn-secondary" type="button" :disabled="!canUndo" title="Undo your last change (Ctrl+Z)" @click="undo"><Undo2 :size="15" /> Undo</button>
            <button class="btn-secondary" @click="discardChanges">Discard changes</button>
            <button class="btn-secondary" :disabled="isSaving" @click="savePlan()">{{ isSaving ? 'Saving…' : selectedPlan.status === 'draft' ? 'Save draft' : 'Save changes' }}</button>
            <button class="btn-primary" :disabled="isSaving || isSending" @click="requestSend(saveAndSend)"><Send :size="15" /> Save &amp; send to patient</button>
          </div>
        </template>
      </div>

      <!-- RIGHT SIDEBAR (CREATE MODE) -->
      <div class="side-column">
        <div class="panel">
          <div class="side-header-row">
            <h4 class="side-title">Preview</h4>
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

            <div v-if="filledRows(macroRows).length" class="target-list">
              <div v-for="row in filledRows(macroRows)" :key="row.label" class="target-row">
                <span>{{ row.label }}</span><span>{{ row.value }}{{ row.unit ? ` ${row.unit}` : '' }}</span>
              </div>
            </div>
            <div v-if="filledRows(otherRows).length" class="target-list">
              <p class="target-list-title">Other targets <span>(not in the kcal target)</span></p>
              <div v-for="row in filledRows(otherRows)" :key="row.label" class="target-row">
                <span>{{ row.label }}</span><span>{{ row.value }}{{ row.unit ? ` ${row.unit}` : '' }}</span>
              </div>
            </div>
          </template>

          <div v-if="selectedPlan && currentDayMeals.some(m => m.items.some(i => i.name))" class="preview-list">
            <div class="preview-item" v-for="meal in currentDayMeals.filter(m => m.items.some(i => i.name))" :key="meal.type" :class="'preview-' + meal.accent">
              <div class="preview-label"><component :is="meal.icon" :size="13" /> {{ sentence(meal.type) }}</div>
              <div class="preview-food">{{ firstFoodSummary(meal) }}</div>
              <div class="preview-kcal">{{ mealTotal(meal, 'kcal') }} kcal</div>
            </div>
          </div>
          <p v-else-if="selectedPlan" class="macro-note">No meals added yet. Add food items per day to see the nutrition breakdown.</p>
        </div>

        <div v-if="selectedPlan" class="panel">
          <h4 class="side-title">Day totals</h4>
          <div class="macro-row"><span>Calories</span><span class="macro-value">{{ dayTotal('kcal') }} kcal</span></div>
          <div class="macro-bar"><div class="macro-fill fill-dark" :style="{ width: macroPct('kcal') + '%' }"></div></div>

          <div class="macro-row"><span>Carbs (g)</span><span class="macro-value">{{ dayTotal('carb') }}g</span></div>
          <div class="macro-bar"><div class="macro-fill fill-gold" :style="{ width: macroPct('carb') + '%' }"></div></div>

          <div class="macro-row"><span>Protein (g)</span><span class="macro-value">{{ dayTotal('prot') }}g</span></div>
          <div class="macro-bar"><div class="macro-fill fill-green" :style="{ width: macroPct('prot') + '%' }"></div></div>

          <div class="macro-row"><span>Fat (g)</span><span class="macro-value">{{ dayTotal('fat') }}g</span></div>
          <div class="macro-bar"><div class="macro-fill fill-dark2" :style="{ width: macroPct('fat') + '%' }"></div></div>

          <p class="macro-note">Based on foods entered for the selected day</p>
        </div>

        <div v-if="selectedPlan" class="panel">
          <h4 class="side-title">Instructions for the patient</h4>
          <div class="field">
            <label>Allergies and restrictions</label>
            <textarea v-model="instructions.allergies" rows="2" placeholder="e.g., No shellfish, low potassium"></textarea>
          </div>
          <div class="field">
            <label>Notes for the patient</label>
            <textarea v-model="instructions.notes" data-allow-emoji rows="3" placeholder="e.g., Please eat meals at regular times. Avoid skipping meals."></textarea>
          </div>
        </div>
      </div>
    </div>
    <div v-if="confirmDelete" class="nm-modal-overlay no-print" @click.self="confirmDelete = false">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="del-title">
        <h3 id="del-title" class="nm-modal-title">Delete this draft?</h3>
        <p class="nm-modal-text">"{{ selectedPlan?.name }}" was never sent to {{ selectedPatientName || 'the patient' }}. Deleting it removes the whole 7-day week, every meal and food in it. This can't be undone.</p>
        <div class="nm-modal-actions">
          <button class="btn-secondary" type="button" @click="confirmDelete = false">Keep it</button>
          <button class="btn-danger solid" type="button" :disabled="isDeleting || deleteWait > 0" @click="deleteDraft"><Trash2 :size="15" /> {{ isDeleting ? 'Deleting…' : deleteWait > 0 ? `Delete draft (${deleteWait})` : 'Delete draft' }}</button>
        </div>
      </div>
    </div>
    <div v-if="sendCheck" class="nm-modal-overlay no-print" @click.self="sendCheck = null">
      <div class="nm-modal send-check" role="dialog" aria-modal="true" aria-labelledby="send-check-title">
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
  Eye, Plus, ChevronLeft, Printer, Pencil, Send, X, CheckCircle2,
  Sun, Coffee, Utensils, Apple, Moon, Search, AlertTriangle, Trash2, Undo2, Lock
} from 'lucide-vue-next'
import { usdaPortion } from '~/utils/usda'
import { MEASURE_TEMPLATES } from '~/utils/ncp'
import { allergyWarnings, conditionKeys, foodWarnings } from '~/utils/foodWarnings'

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
const mealOrder = ['Breakfast', 'Morning Snack', 'Lunch', 'Afternoon Snack', 'Dinner']
const MEAL_TIME = { Breakfast: 'breakfast', 'Morning Snack': 'am_snack', Lunch: 'lunch', 'Afternoon Snack': 'pm_snack', Dinner: 'dinner' }
const MEAL_TYPE = Object.fromEntries(Object.entries(MEAL_TIME).map(([k, v]) => [v, k]))
const mealIcons = { Breakfast: Sun, 'Morning Snack': Coffee, Lunch: Utensils, 'Afternoon Snack': Apple, Dinner: Moon }
const mealAccents = { Breakfast: 'green', 'Morning Snack': 'gold', Lunch: 'blue', 'Afternoon Snack': 'gold', Dinner: 'blue' }

const mode = ref('view')
const isLoading = ref(true)
const isSaving = ref(false)
const isSending = ref(false)
const errorMessage = ref('')
const notice = ref('')
let noticeTimer = null
function flash(message) {
  notice.value = message
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => { notice.value = '' }, 4000)
}
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
  flash(`Copied ${DAY_FULL[from]}'s meals to ${targets.map(d => DAY_FULL[d]).join(', ')}. Press Undo if that wasn't right.`)
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
    for (const type of mealOrder) week[day][type] = { time: '', items: [] }
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
      time: meal.scheduled_time ? meal.scheduled_time.slice(0, 5) : '',
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
    errorMessage.value = apiError(error, 'Could not delete the draft.')
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
  flash(`Draft built from the ${label} template. Check each day and adjust, then send it to ${selectedPatientName.value}.`)
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
    flash('Plan created as a draft. Add meals for each day, then send it to your patient.')
  } catch (error) {
    errorMessage.value = apiError(error, 'Could not create the plan.')
  } finally {
    isSaving.value = false
  }
}

async function savePlan({ quiet = false } = {}) {
  if (!selectedPlan.value) return false
  if (!planMeta.name.trim()) {
    errorMessage.value = 'Plan name is required.'
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
    return true
  } catch (error) {
    errorMessage.value = apiError(error, 'Could not save the plan.')
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
async function loadPatientConditions(relId) {
  patientConditions.value = []
  patientAllergies.value = []
  try {
    const summary = await get(`/rnd/relationships/${relId}/summary/`)
    if (relId === selectedRelId.value) {
      patientConditions.value = summary.health?.conditions || []
      patientAllergies.value = summary.health?.allergies || []
    }
  } catch {
    // No conditions known — the plan's own condition still counts.
  }
}
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
    errorMessage.value = apiError(error, 'Could not send the plan.')
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
// Picking an FNRI food fills 1 exchange's household measure and macros from
// its FNRI category — the RND can still adjust the numbers.
function applyFnriItem(item, match) {
  const cat = match.category
  item.name = match.name
  item.foodItemId = match.id
  item.exchanges = 1
  item.portion = match.household_measure || item.portion
  item.kcal = num(cat.kcal_per_exchange)
  item.carb = num(cat.carbs_g)
  item.prot = num(cat.protein_g)
  item.fat = num(cat.fat_g)
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
</script>

<style scoped>
.top-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; }
.back-link { display: inline-flex; align-items: center; gap: 4px; border: none; background: #e3efe7; border-radius: 8px; min-height: 32px; padding: 0 12px; margin: 0 0 12px; font-family: inherit; font-size: 0.78rem; font-weight: 600; color: #0a4a37; cursor: pointer; }
.back-link:hover { background: #d3e7da; }
.back-link:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.mode-toggle { display: flex; gap: 10px; }
.mode-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 36px; padding: 0 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer; font-family: inherit; line-height: 1.2;
  border: none; background: #e3efe7; color: #0a4a37;
}
.mode-btn:hover:not(:disabled):not(.active) { background: #d3e7da; }
.mode-btn.active { background: #0a4a37; color: #fff; }


.planning-layout { display: grid; grid-template-columns: minmax(0, 2.3fr) minmax(0, 1fr); gap: 24px; align-items: start; }

.panel { background: #fff; border-radius: 12px; padding: 24px; border: 1px solid #eceeec; margin-bottom: 20px; }
/* the light card shadow, on every panel here and in the parts this page shows
   (patient list, template picker) */
.meal-planning-page :deep(.panel), .meal-planning-page :deep(.nm-panel) { box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }

/* VIEW MODE */
.plan-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.plan-header h3 { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0; }
.plan-badges { display: flex; gap: 8px; }
.badge { font-size: 0.72rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; }
.badge-blue { background: #e3edfc; color: #3b6fd6; }
.badge-gold { background: #fdf1d6; color: #b8860b; }

.day-tabs { display: flex; gap: 8px; margin-bottom: 24px; }
.day-tab {
  border: 1px solid #e0e5e0; background: #fff; color: #4a5a4a;
  padding: 8px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.day-tab.active { background: #163a1c; color: #fff; border-color: #163a1c; }

.meal-list { display: flex; flex-direction: column; }
.meal-block { padding: 16px 0; border-bottom: 1px solid #f0f2f0; }
.meal-block:first-child { padding-top: 4px; }
.meal-block:last-child { border-bottom: none; }
.meal-head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 8px; }
.meal-name { font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.meal-time { font-size: 0.82rem; color: #7a8a7a; font-variant-numeric: tabular-nums; }
.meal-kcal { margin-left: auto; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; white-space: nowrap; font-variant-numeric: tabular-nums; }
.meal-foods { width: 100%; border-collapse: collapse; font-size: 0.84rem; table-layout: fixed; }
/* same column widths in every meal, so the numbers line up down the day */
.meal-foods th:nth-child(1) { width: 36%; }
.meal-foods th:nth-child(2) { width: 24%; }
.meal-foods th { text-align: left; font-size: 0.74rem; font-weight: 500; color: #8a9a8a; padding: 0 8px 4px 0; }
.meal-foods td { padding: 6px 8px 6px 0; border-top: 1px solid #f4f6f4; vertical-align: top; color: #3a4a3a; }
.meal-foods .food { color: #1a3a1a; font-weight: 500; }
.meal-foods .portion { color: #6a7a6a; }
.meal-foods .n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.meal-foods th.n { padding-right: 8px; }
.meal-empty { font-size: 0.84rem; color: #9aaa9a; margin: 0; }
@media (max-width: 640px) {
  /* phones: food and portion on one line, numbers on the next */
  .meal-foods thead { display: none; }
  .meal-foods tr { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-top: 1px solid #f4f6f4; padding: 6px 0; }
  .meal-foods td { border: none; padding: 0; }
  .meal-foods .food { grid-column: 1 / -1; }
  .meal-foods .portion { grid-column: 1 / -1; margin-bottom: 4px; }
  .meal-foods .n { width: auto; text-align: left; font-size: 0.78rem; color: #5a6a5a; }
  .meal-foods .n:nth-child(3)::after { content: ' kcal'; }
  .meal-foods .n:nth-child(4)::before { content: 'Carbs '; }
  .meal-foods .n:nth-child(5)::before { content: 'Protein '; }
  .meal-foods .n:nth-child(6)::before { content: 'Fat '; }
  .meal-foods tr { grid-template-columns: 0.8fr 1fr 1.1fr 0.8fr; }
}

.plan-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; padding-top: 18px; border-top: 1px solid #f0f2f0; }
.btn-secondary {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 36px; padding: 0 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer; font-family: inherit; line-height: 1.2;
  border: none; background: #e3efe7; color: #0a4a37;
}
.btn-secondary:hover:not(:disabled) { background: #d3e7da; }
.btn-primary {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 36px; padding: 0 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer; font-family: inherit; line-height: 1.2;
  background: #0a4a37; color: #fff; border: none;
}
.btn-primary:hover:not(:disabled) { background: #00382a; }
.btn-primary:focus-visible, .btn-secondary:focus-visible, .btn-danger:focus-visible, .mode-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 36px; padding: 0 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer; font-family: inherit; line-height: 1.2; margin-right: auto;
  border: none; background: #c0392b; color: #fff;
}
.btn-danger:hover:not(:disabled) { background: #a93226; }
.btn-danger.solid { margin-right: 0; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
.sent-lock { display: flex; align-items: center; gap: 6px; margin: 16px 0 0; font-size: 0.78rem; color: #6a7a6a; }

/* SIDE COLUMN (shared) */
.side-title { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; }
.side-subtitle { font-size: 0.75rem; color: #9aaa9a; }
.side-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }

.nutrient-row { margin-top: 16px; }
.nutrient-top { display: flex; justify-content: space-between; font-size: 0.78rem; color: #4a5a4a; margin-bottom: 6px; }
.nutrient-bar { height: 6px; background: #eceeec; border-radius: 3px; overflow: hidden; }
.nutrient-fill { height: 100%; border-radius: 3px; }
.fill-green { background: #2e9e52; }
.fill-gold { background: #D4A017; }
.fill-dark { background: #163a1c; }
.fill-dark2 { background: #3a4a3a; }

.saved-plan-card {
  display: flex; justify-content: space-between; align-items: center;
  background: #eef5ee; border-radius: 10px; padding: 14px; margin-top: 6px;
}
.saved-plan-name { font-size: 0.85rem; font-weight: 700; color: #1a3a1a; }
.saved-plan-meta { font-size: 0.72rem; color: #7a8a7a; margin-top: 2px; }
.active-pill { background: #e6efe0; color: #2e6b3a; font-size: 0.72rem; font-weight: 600; padding: 3px 9px; border-radius: 10px; }

.exchange-note { font-size: 0.72rem; color: #9aaa9a; margin-top: 12px; }

/* CREATE MODE — STEP 1 (simplified plan details form) */
.no-plan-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }
.start-choice { margin-bottom: 16px; }
.start-options { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.start-opt { display: flex; flex-direction: column; gap: 4px; text-align: left; background: #fff; border: 1.5px solid #d9e3dc; border-radius: 12px; padding: 12px 14px; font-family: inherit; cursor: pointer; }
.start-opt:hover { border-color: #9ec4ad; }
.start-opt:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.start-opt.on { border-color: #0a4a37; background: #e3efe7; }
.start-name { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; font-weight: 700; font-size: 0.9rem; color: #1a3a1a; }
.start-rec { font-size: 0.7rem; font-weight: 700; color: #1a3a1a; background: #D4A017; border-radius: 999px; padding: 1px 8px; }
.start-desc { font-size: 0.8rem; color: #4a5a4a; line-height: 1.45; }
.create-hint { font-size: 0.8rem; color: #4a5a4a; margin: 8px 0 0; }
.copy-day { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 10px; margin: -12px 0 16px; font-size: 0.82rem; color: #1a3a1a; }
.copy-day label { font-weight: 600; }
.copy-hint { font-size: 0.78rem; color: #6a7a6a; }
.food-hint { grid-column: 2 / -1; margin: -4px 0 0; font-size: 0.76rem; color: #4a5a4a; background: #f2f6f3; border: 1px dashed #9ec4ad; border-radius: 6px; padding: 6px 9px; line-height: 1.4; }
@media (max-width: 640px) {
  .start-options { grid-template-columns: 1fr; }
  .copy-day .nm-select { flex: 1; min-width: 0; }
}
.form-row-6 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 24px; margin-bottom: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.field label { font-size: 0.8rem; font-weight: 600; color: #3a4a3a; }
.optional { font-weight: 400; text-transform: none; color: #9aaa9a; }
.field input, .field textarea {
  border: 1px solid #dde3dd; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #1a3a1a;
}
.field textarea { resize: vertical; }

/* NUTRIENT TARGET ROWS (Measured Variable / Value / Unit) */
.targets-section { border-top: 1px dashed #e0e5e0; padding-top: 14px; margin-bottom: 14px; }
.targets-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.targets-title { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; }
.targets-add-btn {
  display: inline-flex; align-items: center; gap: 4px; border: none; color: #0a4a37; font-family: inherit;
  background: #e3efe7; border-radius: 8px; min-height: 32px; padding: 0 12px; font-size: 0.78rem; font-weight: 600; cursor: pointer;
}
.targets-add-btn:hover { background: #d3e7da; }
.targets-hint { font-size: 0.75rem; color: #8a9a8a; margin: -4px 0 10px; line-height: 1.45; }
.targets-row { display: grid; grid-template-columns: 1.4fr 1fr 0.8fr auto; gap: 10px; align-items: center; margin-bottom: 8px; }
.targets-row.locked input[readonly] { background: #f6f8f6; color: #4a5a4a; cursor: default; }
.targets-remove-btn.spacer { visibility: hidden; }
.targets-row input, .targets-row :deep(.combo input) {
  border: 1px solid #dde3dd; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #1a3a1a; width: 100%;
}
.targets-remove-btn {
  display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px;
  border: none; border-radius: 8px; background: #c0392b; color: #fff; cursor: pointer;
}
.targets-remove-btn:hover { background: #a93226; }

/* LIVE PREVIEW (create mode) */
.preview-summary { margin-bottom: 12px; }
.preview-summary-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0 0 8px; }
.target-list { margin-top: 12px; padding-top: 12px; border-top: 1px solid #f0f2f0; display: flex; flex-direction: column; gap: 6px; }
.target-row { display: flex; justify-content: space-between; font-size: 0.8rem; color: #4a5a4a; }
.target-list-title { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.target-list-title span { font-weight: 400; text-transform: none; letter-spacing: 0; color: #9aaa9a; }

.meal-edit-panel { padding: 0; margin-bottom: 18px; } /* no overflow:hidden — the food picker list must show past the card */
.meal-edit-header {
  display: flex; justify-content: space-between; align-items: center;
  background: #eef5ee; padding: 16px 24px; border-radius: 12px 12px 0 0;
}
.meal-edit-label { display: flex; align-items: center; gap: 6px; font-size: 0.92rem; font-weight: 700; color: #1a3a1a; }
.meal-edit-time { font-size: 0.75rem; color: #7a8a7a; }

.food-table { padding: 20px 24px 4px; }
.food-table-head, .food-table-row {
  display: grid; grid-template-columns: 24px 2fr 1fr 0.8fr 0.9fr 0.9fr 0.8fr; gap: 12px; align-items: center;
}
.food-table-head { font-size: 0.74rem; font-weight: 500; color: #8a9a8a; padding-bottom: 8px; }
.food-table-head span:first-child { visibility: hidden; }
.food-table-row { margin-bottom: 12px; }
.combo { position: relative; min-width: 0; }
.combo-list { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; width: max(100%, 320px); max-height: 260px; overflow-y: auto; background: #fff; border: 1px solid #d5dad5; border-radius: 10px; box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12); padding: 6px; }
.combo-group { font-size: 0.74rem; font-weight: 600; color: #6a7a6a; margin: 6px 8px 2px; }
.combo-opt { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; width: 100%; text-align: left; border: none; background: none; padding: 7px 8px; border-radius: 6px; font-family: inherit; font-size: 0.84rem; color: #1a3a1a; cursor: pointer; }
.combo-opt:hover, .combo-opt.on { background: #eef3ec; }
.combo-meta { font-size: 0.72rem; color: #8a9a8a; white-space: nowrap; }
.combo-allergy { margin-left: 6px; font-size: 0.62rem; font-weight: 700; color: #b3261e; background: #fdecea; border: 1px solid #f2b8b5; border-radius: 5px; padding: 0 5px; vertical-align: 1px; }
.food-warn { grid-column: 2 / -1; display: flex; align-items: flex-start; gap: 6px; margin: -4px 0 0; font-size: 0.74rem; font-weight: 600; color: #9a5b00; background: #fff6e5; border: 1px solid #f3dcae; border-radius: 6px; padding: 6px 9px; line-height: 1.4; }
.food-warn svg { flex-shrink: 0; margin-top: 1px; }
.food-warn.allergy { color: #b3261e; background: #fdecea; border-color: #f2b8b5; }
.day-warn-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #e0a100; margin-left: 6px; vertical-align: 2px; }
.send-check { max-width: 540px; }
.send-consequence { display: flex; gap: 8px; align-items: flex-start; margin: 0 0 14px; padding: 10px 12px; background: #f3f6f3; border-radius: 8px; font-size: 0.82rem; color: #3a4a3a; line-height: 1.5; }
.send-consequence svg { flex-shrink: 0; margin-top: 2px; }
.send-section { display: flex; align-items: center; gap: 6px; margin: 12px 0 8px; font-size: 0.8rem; font-weight: 700; color: #7a5a1a; }
.send-section.allergy { color: #b3261e; }
.send-check-list.allergy li { background: #fdecea; border-color: #f2b8b5; color: #8c1d18; }
.allergy-ack { display: flex; gap: 8px; align-items: flex-start; margin-top: 10px; font-size: 0.8rem; font-weight: 600; color: #8c1d18; cursor: pointer; }
.allergy-ack input { margin-top: 2px; accent-color: #b3261e; }
.send-check-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; max-height: 45vh; overflow-y: auto; }
.send-check-list li { background: #fff6e5; border: 1px solid #f3dcae; border-radius: 8px; padding: 8px 10px; font-size: 0.8rem; color: #5a4a2a; display: flex; flex-direction: column; gap: 2px; }
.send-check-list strong { color: #1a3a1a; font-weight: 700; }
.send-check-meal { text-transform: capitalize; }
.food-table-row input {
  border: 1px solid #e0e5e0; border-radius: 6px; padding: 9px 10px; font-size: 0.82rem; font-family: inherit; width: 100%;
}
.food-table-row input:disabled { background: #f6f8f6; color: #4a5a4a; }
.usda-name { font-size: 0.82rem; color: #1a3a1a; line-height: 1.35; min-width: 0; overflow-wrap: anywhere; }
.usda-tag { display: inline-block; font-size: 0.6rem; font-weight: 700; background: #eef1f8; color: #34508a; border-radius: 5px; padding: 1px 5px; margin-right: 6px; vertical-align: 1px; }
.grams-input { display: flex; align-items: center; gap: 4px; }
.grams-input span { font-size: 0.78rem; color: #6a7a6a; }
.add-food-row { display: flex; gap: 10px; margin: 6px 24px 22px; }
.add-food-row .btn-add-food { flex: 1; width: auto; margin: 0; }
.usda-btn { color: #34508a; border-color: #cfd8ea; }
.usda-btn:hover { background: #f4f6fb; }
.remove-btn {
  width: 20px; height: 20px; border-radius: 5px; border: none;
  background: #fbe1de; color: #c0483a; display: flex; align-items: center; justify-content: center; cursor: pointer;
}

.btn-add-food {
  display: flex; align-items: center; gap: 6px; justify-content: center;
  width: calc(100% - 48px); margin: 6px 24px 22px;
  border: 1px dashed #cdd8cd; background: none; color: #1a6a2a;
  padding: 11px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.btn-add-food:hover { background: #f4f8f4; }

.preview-list { display: flex; flex-direction: column; gap: 10px; margin-top: 14px; }
.preview-item { background: #fafbfa; border: 1px solid #eef1ee; border-radius: 8px; padding: 10px 12px; }
.preview-label { display: flex; align-items: center; gap: 5px; font-size: 0.72rem; font-weight: 700; color: #4a5a4a; margin-bottom: 3px; }
.preview-food { font-size: 0.8rem; color: #1a3a1a; margin-bottom: 3px; }
.preview-kcal { font-size: 0.72rem; color: #9aaa9a; }
.preview-day { font-size: 0.72rem; color: #9aaa9a; }

.macro-row { display: flex; justify-content: space-between; font-size: 0.82rem; color: #3a4a3a; margin-top: 18px; margin-bottom: 8px; }
.macro-value { font-weight: 600; }
.macro-bar { height: 6px; background: #eceeec; border-radius: 3px; overflow: hidden; }
.macro-fill { height: 100%; border-radius: 3px; }
.macro-note { font-size: 0.72rem; color: #9aaa9a; margin-top: 16px; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0; }

.mode-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.form-notice {
  display: flex; align-items: center; gap: 8px;
  background: #e3f3ea; border: 1px solid #b8dcc6; color: #1f8f5c;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; font-weight: 600; margin: 0 0 16px;
}
.plan-subtitle { font-size: 0.8rem; color: #7a8a7a; margin: 4px 0 0; }
.status-text { font-weight: 600; }
.prefill-note { margin: -8px 0 14px; }

button.saved-plan-card { width: 100%; border: 1.5px solid transparent; cursor: pointer; text-align: left; font-family: inherit; }
button.saved-plan-card:hover { border-color: #cfe0cf; }
button.saved-plan-card.selected { border-color: #163a1c; }
.active-pill.pill-draft { background: #fdf1d6; color: #b8860b; }
.active-pill.pill-archived { background: #eceeec; color: #7a8a7a; }

.instructions-view { margin-top: 16px; padding: 14px 16px; background: #fafbfa; border-radius: 8px; }
.instructions-view p { font-size: 0.8rem; color: #4a5a4a; margin: 0 0 6px; line-height: 1.5; }
.instructions-view p:last-child { margin: 0; }
.instr-read { margin: 10px 0 0; }
.instr-allergy { display: flex; gap: 6px; align-items: flex-start; margin: 10px 0 0; font-size: 0.8rem; font-weight: 600; line-height: 1.4; color: #8a1f14; background: #fdf1ef; border: 1.5px solid #c0392b; border-radius: 8px; padding: 7px 10px; }
.instr-allergy svg { flex-shrink: 0; margin-top: 1px; color: #c0392b; }
.instr-read dt { font-size: 0.78rem; font-weight: 600; color: #4a5a4a; margin: 0 0 3px; }
.instr-read dd { font-size: 0.84rem; color: #1a3a1a; line-height: 1.5; margin: 0 0 12px; white-space: pre-line; overflow-wrap: anywhere; }
.instr-read dd:last-child { margin-bottom: 0; }
.instr-read dd.empty { color: #8a9a8a; }

.meal-time-input { border: 1px solid #d5dfd5; border-radius: 6px; padding: 5px 8px; font-size: 0.78rem; font-family: inherit; color: #1a3a1a; background: #fff; }
.create-actions { margin: 0 0 20px; padding: 0; border-top: none; }

.print-only { display: none; }
.screen-hidden { display: none; }

@media print {
  :global(body *) { visibility: hidden; }
  .print-area, .print-area * { visibility: visible; }
  .print-area { position: absolute; left: 0; top: 0; width: 100%; border: none; }
  .no-print { display: none !important; }
  .print-only { display: block; }
  .screen-hidden { display: block; }
  .print-day { break-inside: avoid; margin-bottom: 14px; }
  .print-day-title { font-size: 0.95rem; color: #1a3a1a; margin: 12px 0 6px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
}

@media (max-width: 1150px) {
  .planning-layout { grid-template-columns: minmax(0, 1fr); }
  .form-row-6 { grid-template-columns: 1fr 1fr; }
  .food-table-head, .food-table-row { grid-template-columns: 20px 2fr 1fr 1fr 1fr; }
  .food-table-head span:nth-child(6), .food-table-row input:nth-child(6),
  .food-table-head span:nth-child(7), .food-table-row input:nth-child(7) { display: none; }
}

/* PHONE */
@media (max-width: 640px) {
  .top-controls { flex-wrap: wrap; gap: 12px; margin-bottom: 18px; }
  .mode-toggle { flex-wrap: wrap; }
  .panel { padding: 16px; }
  .plan-header { flex-wrap: wrap; gap: 10px; }
  .plan-badges { flex-wrap: wrap; }
  /* seven day tabs: swipe sideways instead of overflowing */
  .day-tabs { overflow-x: auto; scrollbar-width: none; margin-left: -16px; margin-right: -16px; padding: 0 16px 2px; }
  .day-tabs::-webkit-scrollbar { display: none; }
  .day-tab { flex-shrink: 0; }
  .meal-kcal { margin-left: 10px; }
  .plan-actions { flex-wrap: wrap; }
  .plan-actions > * { flex: 1 1 auto; justify-content: center; }
  .form-row-6 { grid-template-columns: minmax(0, 1fr); gap: 0; }
  .targets-header { flex-wrap: wrap; }
  .targets-row { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto; }
  .targets-row > :first-child { grid-column: 1 / -1; }
  .meal-edit-header { flex-wrap: wrap; gap: 8px; padding: 12px 16px; }
  /* the food editor keeps its columns and scrolls sideways inside the card */
  .food-table { overflow-x: auto; padding: 16px 16px 4px; }
  .combo-list { position: static; width: 100%; margin-top: 4px; box-shadow: none; }
  .combo-list { overflow-x: hidden; }
  .combo-opt { flex-direction: column; align-items: flex-start; gap: 2px; }
  .combo-meta { white-space: normal; }
  .food-table-head, .food-table-row { min-width: 480px; }
  .btn-add-food { width: calc(100% - 32px); margin: 6px 16px 18px; }
  .add-food-row { margin: 6px 16px 18px; flex-direction: column; }
  .add-food-row .btn-add-food { width: 100%; margin: 0; }
  .saved-plan-card { gap: 10px; }
}
</style>

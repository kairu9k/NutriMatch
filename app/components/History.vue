<template>
  <div class="history-page">
    <div class="panel">
      <div class="panel-header-row">
        <div>
          <h3 class="panel-title">Your Activity</h3>
          <p class="panel-sub">Every screening, appointment request, and meal log you've saved.</p>
        </div>
        <div class="header-actions">
          <div class="filter-tabs">
            <button v-for="f in filters" :key="f.key" class="filter-tab" :class="{ active: activeFilter === f.key }" @click="activeFilter = f.key">{{ f.label }}</button>
          </div>
          <button class="print-btn" @click="printHistory"><Printer :size="14" /> Print</button>
        </div>
      </div>

      <div v-if="!filteredLog.length" class="empty-state">
        <ClipboardList :size="26" class="empty-icon" />
        <p>Nothing saved yet.</p>
        <p class="empty-sub">Complete a screening, book an appointment, or log a meal — it'll show up here.</p>
      </div>

      <div v-for="entry in filteredLog" :key="entry.id" class="entry-row">
        <div class="entry-icon" :class="iconClass(entry.type)">
          <component :is="typeIcon(entry.type)" :size="16" />
        </div>
        <div class="entry-info">
          <p class="entry-title">{{ entry.title }}</p>
          <p class="entry-detail">{{ entry.detail }}</p>
        </div>
        <span class="entry-time">{{ entry.timestamp }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ClipboardList, ShieldCheck, CalendarCheck, UtensilsCrossed, Printer } from 'lucide-vue-next'
import { useClientHistory } from '~/composables/useClientHistory'

const { historyLog } = useClientHistory()

const filters = [
  { key: 'all', label: 'All' },
  { key: 'screening', label: 'Screenings' },
  { key: 'appointment', label: 'Appointments' },
  { key: 'mealLog', label: 'Meal Logs' }
]
const activeFilter = ref('all')
const filteredLog = computed(() =>
  activeFilter.value === 'all' ? historyLog.value : historyLog.value.filter(e => e.type === activeFilter.value)
)

function typeIcon(type) {
  return { screening: ShieldCheck, appointment: CalendarCheck, mealLog: UtensilsCrossed }[type] || ClipboardList
}
function iconClass(type) {
  return { screening: 'icon-blue', appointment: 'icon-gold', mealLog: 'icon-green' }[type] || 'icon-green'
}
function printHistory() {
  window.print()
}
</script>

<style scoped>
* { box-sizing: border-box; }
.history-page { font-family: 'Inter', sans-serif; }

.panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px 24px; }
.panel-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0; }
.panel-sub { font-size: 0.84rem; color: #9aaa9a; margin: 4px 0 0; }

.header-actions { display: flex; align-items: center; gap: 10px; }
.print-btn {
  display: inline-flex; align-items: center; gap: 6px; border: 1px solid #d5dad5; background: #fff; color: #1a3a1a;
  border-radius: 8px; padding: 9px 14px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.print-btn:hover { background: #f7f9f7; }

.filter-tabs { display: flex; gap: 4px; background: #f7f9f7; padding: 4px; border-radius: 999px; }
.filter-tab { border: none; background: none; padding: 7px 14px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; color: #8a9a8a; cursor: pointer; }
.filter-tab.active { background: #14301a; color: #fff; }

.empty-state { padding: 50px 20px; text-align: center; color: #9aaa9a; }
.empty-icon { color: #d5dad5; margin-bottom: 10px; }
.empty-state p { margin: 0; font-size: 0.9rem; }
.empty-sub { font-size: 0.8rem; margin-top: 4px !important; color: #b5bdb5; }

.entry-row { display: flex; align-items: flex-start; gap: 14px; padding: 14px 0; border-top: 1px solid #f0f2f0; }
.entry-row:first-of-type { border-top: none; padding-top: 0; }
.entry-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.icon-blue { background: #e3ecf7; color: #2a5a8a; }
.icon-gold { background: #fdf1d6; color: #b8860b; }
.icon-green { background: #e3f3ea; color: #1f8f5c; }
.entry-info { flex: 1; }
.entry-title { font-size: 0.87rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.entry-detail { font-size: 0.8rem; color: #6a7a6a; margin: 3px 0 0; }
.entry-time { font-size: 0.76rem; color: #9aaa9a; flex-shrink: 0; white-space: nowrap; margin-top: 2px; }

@media print {
  .header-actions { display: none; }
}
</style>
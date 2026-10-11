<template>
  <!-- One-time "Welcome sa NutriMatch" (Taglish), per role. Shown by
       layouts/dashboard.vue the first time a client/RND reaches their
       dashboard (User.welcome_seen_at is null), and reopened any time from
       the account menu ("How NutriMatch works"). -->
  <Transition name="welcome-fade">
    <div v-if="open" class="welcome-overlay" @click.self="close">
      <div ref="dialog" class="welcome-card" role="dialog" aria-modal="true" aria-labelledby="welcome-title" tabindex="-1">
        <button class="welcome-x" type="button" aria-label="Close" @click="close"><X :size="18" /></button>

        <header class="welcome-head">
          <div class="welcome-blob"></div>
          <div class="welcome-brand">
            <img src="/resources/nutrimatchlogo.png" alt="" class="welcome-logo" />
            <span class="welcome-wordmark">Nutri<span class="gold">Match</span></span>
          </div>
          <h2 id="welcome-title" class="welcome-title">{{ copy.title }}</h2>
          <p class="welcome-intro">{{ copy.intro }}</p>
        </header>

        <div class="welcome-body">
          <p class="welcome-howto">{{ copy.howto }}</p>
          <ol class="welcome-steps">
            <li v-for="(s, i) in copy.steps" :key="s.title" class="welcome-step">
              <span class="step-icon"><component :is="s.icon" :size="17" /></span>
              <div>
                <p class="step-title"><span class="step-num">{{ i + 1 }}.</span> {{ s.title }}</p>
                <p class="step-text">{{ s.text }}</p>
              </div>
            </li>
          </ol>
          <p class="welcome-closing">{{ copy.closing }}</p>

          <div class="welcome-actions">
            <button class="outline-btn" type="button" @click="go(copy.secondary.to)">{{ copy.secondary.label }}</button>
            <button ref="primaryBtn" class="btn-dark" type="button" @click="go(copy.primary.to)">{{ copy.primary.label }} <ArrowRight :size="15" /></button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  X, ArrowRight, Search, CalendarCheck, Video, UtensilsCrossed, TrendingUp,
  Users, ClipboardCheck, CreditCard, HeartHandshake, Wallet,
} from 'lucide-vue-next'

const props = defineProps({
  open: { type: Boolean, default: false },
  role: { type: String, default: 'client' }, // 'client' | 'rnd'
  firstName: { type: String, default: '' },
})
const emit = defineEmits(['close'])

const COPY = {
  client: (name) => ({
    title: `Welcome sa NutriMatch${name ? `, ${name}` : ''}! 💚`,
    intro: "Sobrang saya namin na nandito ka. Ang pag-aalaga sa kinakain mo ay isa sa pinakamagandang regalo mo sa sarili mo — at hindi mo kailangang gawin ito mag-isa.",
    howto: 'Ganito tayo magsisimula:',
    steps: [
      { icon: Search, title: 'Hanapin ang RND mo', text: 'Pumili ng licensed Registered Nutritionist-Dietitian na kabisado ang pagkaing Pinoy at ang health needs mo.' },
      { icon: CalendarCheck, title: 'Mag-book at magbayad in advance', text: 'Pumili ng oras na swak sa schedule mo, then bayaran ito bago ang session.' },
      { icon: Video, title: 'Makipag-consult', text: 'Sa video call, chat, o in person — kung saan ka komportable.' },
      { icon: UtensilsCrossed, title: 'Sundan ang meal plan mo', text: "Ginawa para sa'yo, meal by meal, gamit ang mga pagkaing gusto mo na." },
      { icon: TrendingUp, title: 'Bantayan ang progress mo', text: 'I-log ang meals mo para makita mo kung gaano ka na kalayo.' },
    ],
    closing: "Kaya mo 'to — kasama mo kami sa bawat hakbang. 🌱",
    primary: { label: 'Hanapin ang RND ko', to: '/find-rnd' },
    secondary: { label: 'Tingnan ang dashboard ko', to: null },
  }),
  rnd: (name) => ({
    title: `Welcome sa NutriMatch family${name ? `, RND ${name}` : ''}! 🌿`,
    intro: 'Maraming salamat sa pag-share ng expertise mo sa mga Pilipinong nangangailangan nito. Bawat consultation mo ay tumutulong sa isang tao na kumain nang tama at mamuhay nang mas healthy.',
    howto: 'Ganito gumagana ang NutriMatch para sa’yo:',
    steps: [
      { icon: Users, title: 'Hahanapin ka ng clients', text: 'Magbu-book sila sa loob ng weekly hours na sinet mo.' },
      { icon: ClipboardCheck, title: 'I-review at i-accept', text: 'Tingnan muna ang health screening nila bago i-confirm ang booking.' },
      { icon: CreditCard, title: 'Bayad muna bago consult', text: 'Magbubukas ang consultation kapag bayad na — puwede kang mag-join 15 minutes before.' },
      { icon: HeartHandshake, title: 'Alagaan ang clients mo', text: 'Gawin ang NCP record at ang weekly meal plan nila, at sundan ang meal logs nila.' },
      { icon: Wallet, title: 'Kumita', text: 'Ipinapadala ang kita mo tuwing ika-5 ng buwan sa GCash o bank mo — i-add ang payout details mo sa Earnings page.' },
    ],
    closing: 'Excited na kaming makita ang impact mo! 💚',
    primary: { label: 'Pumunta sa dashboard ko', to: null },
    secondary: { label: 'I-set ang availability ko', to: '/profile-settings?tab=availability' },
  }),
}
const copy = computed(() => (COPY[props.role] || COPY.client)(props.firstName))

const dialog = ref(null)
const primaryBtn = ref(null)

function close() {
  emit('close')
}
function go(to) {
  emit('close')
  if (to) navigateTo(to)
}

function onKeydown(e) {
  if (props.open && e.key === 'Escape') close()
}
watch(() => props.open, async (isOpen) => {
  if (!isOpen) return
  await nextTick()
  primaryBtn.value?.focus()
})
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.welcome-overlay {
  position: fixed; inset: 0; z-index: 500; background: rgba(6, 26, 16, 0.55);
  display: flex; align-items: center; justify-content: center; padding: 16px;
}
.welcome-card {
  position: relative; width: 100%; max-width: 560px; max-height: calc(100vh - 32px); overflow-y: auto;
  background: #fff; border-radius: 18px; box-shadow: 0 24px 60px rgba(0, 0, 0, 0.25); font-family: 'Inter', sans-serif;
}
.welcome-card:focus { outline: none; }
.welcome-x {
  position: absolute; top: 12px; right: 12px; z-index: 2; width: 34px; height: 34px; border-radius: 50%;
  border: none; background: rgba(255, 255, 255, 0.15); color: #fff; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.welcome-x:hover { background: rgba(255, 255, 255, 0.28); }

.welcome-head {
  position: relative; overflow: hidden; color: #fff; padding: 26px 28px 24px;
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%);
}
.welcome-blob { position: absolute; width: 220px; height: 220px; border-radius: 50%; background: rgba(255, 255, 255, 0.06); top: -90px; right: -60px; }
.welcome-brand { position: relative; display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.welcome-logo { width: 28px; height: 28px; object-fit: contain; }
.welcome-wordmark { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1rem; }
.gold { color: #D4A017; }
.welcome-title { position: relative; font-family: 'Playfair Display', serif; font-size: 1.55rem; line-height: 1.25; margin: 0 0 10px; }
.welcome-intro { position: relative; font-size: 0.9rem; line-height: 1.6; color: #dceae2; margin: 0; }

.welcome-body { padding: 22px 28px 24px; color: #1a3a1a; }
.welcome-howto { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #b8860b; margin: 0 0 12px; }
.welcome-steps { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 12px; }
.welcome-step { display: flex; gap: 12px; align-items: flex-start; }
.step-icon {
  width: 34px; height: 34px; border-radius: 10px; background: #eef3ec; color: #1e4a26; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.step-title { font-size: 0.9rem; font-weight: 700; margin: 0; }
.step-num { color: #b8860b; }
.step-text { font-size: 0.83rem; color: #5a6a5a; margin: 2px 0 0; line-height: 1.5; }
.welcome-closing {
  font-size: 0.88rem; font-weight: 600; color: #1f6f46; background: #f0f9f4; border-radius: 10px;
  padding: 10px 14px; margin: 18px 0 0; text-align: center;
}
.welcome-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn-dark {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; background: #163a1c; color: #fff;
  border: none; border-radius: 8px; padding: 11px 18px; font-size: 0.88rem; font-weight: 600; cursor: pointer; font-family: inherit;
}
.btn-dark:hover { background: #0f2a14; }
.outline-btn {
  display: inline-flex; align-items: center; justify-content: center; border: 1px solid #d5dad5; background: #fff; color: #1a3a1a;
  border-radius: 8px; padding: 11px 16px; font-size: 0.86rem; font-weight: 600; cursor: pointer; font-family: inherit;
}
.outline-btn:hover { background: #f7f9f7; }

.welcome-fade-enter-active, .welcome-fade-leave-active { transition: opacity 0.2s ease; }
.welcome-fade-enter-active .welcome-card, .welcome-fade-leave-active .welcome-card { transition: transform 0.2s ease; }
.welcome-fade-enter-from, .welcome-fade-leave-to { opacity: 0; }
.welcome-fade-enter-from .welcome-card { transform: translateY(10px) scale(0.98); }

@media (max-width: 640px) {
  .welcome-overlay { align-items: flex-end; padding: 0; }
  .welcome-card { max-width: none; max-height: 92vh; border-radius: 18px 18px 0 0; }
  .welcome-head { padding: 22px 20px 20px; }
  .welcome-title { font-size: 1.3rem; padding-right: 30px; }
  .welcome-body { padding: 18px 20px 22px; }
  .welcome-actions { flex-direction: column-reverse; }
  .welcome-actions > * { width: 100%; }
}
</style>

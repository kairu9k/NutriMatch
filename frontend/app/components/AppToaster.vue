<template>
  <!-- The app's one toast area (composables/useToast.js). Bottom centre, where
       the old per-page toasts were; on phones it sits above the support button. -->
  <Toaster
    position="bottom-center"
    :offset="{ bottom: '28px' }"
    :mobile-offset="{ bottom: '90px', left: '16px', right: '16px' }"
    :visible-toasts="3"
    :gap="10"
    container-aria-label="Messages"
    :toast-options="{ closeButtonAriaLabel: 'Close' }"
  >
    <template #success-icon><CheckCircle2 :size="17" aria-hidden="true" /></template>
    <template #error-icon><AlertCircle :size="17" aria-hidden="true" /></template>
    <template #warning-icon><AlertCircle :size="17" aria-hidden="true" /></template>
    <template #loading-icon><Loader2 :size="17" class="nm-toast-spin" aria-hidden="true" /></template>
  </Toaster>
</template>

<script setup>
import { Toaster } from 'vue-sonner'
import 'vue-sonner/style.css'
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-vue-next'
</script>

<!-- Not scoped: vue-sonner renders its own markup. Overrides its default look
     with the app's (dark green success, red for problems, light green shadow). -->
<style>
[data-sonner-toaster] { --width: 420px; font-family: 'Inter', sans-serif; }
[data-sonner-toaster] [data-sonner-toast][data-styled='true'] {
  align-items: center; gap: 10px; padding: 13px 18px; border-radius: 10px;
  font-size: 0.86rem; font-weight: 600; line-height: 1.4;
  background: #0a4a37; color: #fff; border: 1px solid #0a4a37;
  box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
[data-sonner-toaster] [data-sonner-toast][data-styled='true'] [data-title] { font-weight: 600; }
[data-sonner-toaster] [data-sonner-toast][data-styled='true'] [data-icon] { width: 17px; height: 17px; margin: 0; flex-shrink: 0; }

/* a problem or a failed action: red, the app's warning colour */
[data-sonner-toaster] [data-sonner-toast][data-styled='true'][data-type='error'],
[data-sonner-toaster] [data-sonner-toast][data-styled='true'][data-type='warning'] {
  background: #fff6f5; color: #8a2318; border-color: #e2a39b;
}
[data-sonner-toaster] [data-sonner-toast][data-type='error'] [data-icon],
[data-sonner-toaster] [data-sonner-toast][data-type='warning'] [data-icon] { color: #c0392b; }

/* working on it ("Saving…") */
[data-sonner-toaster] [data-sonner-toast][data-styled='true'][data-type='loading'] {
  background: #fff; color: #0a4a37; border-color: #d9e3dc;
}

/* a plain × on the right, like the pop-ups */
[data-sonner-toaster] [data-sonner-toast][data-styled='true']:has([data-close-button]) { padding-right: 44px; }
[data-sonner-toaster] [data-sonner-toast] [data-close-button] {
  left: auto; right: 10px; top: 50%; transform: translateY(-50%);
  width: 26px; height: 26px; border: none; border-radius: 6px; background: transparent; color: inherit; opacity: 0.75;
}
[data-sonner-toaster] [data-sonner-toast] [data-close-button]:hover { opacity: 1; background: rgba(192, 57, 43, 0.1); }
[data-sonner-toaster] [data-sonner-toast] [data-close-button]:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
[data-sonner-toaster] [data-sonner-toast] [data-close-button] svg { width: 14px; height: 14px; }

.nm-toast-spin { animation: nm-toast-spin 0.9s linear infinite; }
@keyframes nm-toast-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .nm-toast-spin { animation: none; } }
</style>

# Test findings, 2026-11-16

Plan: `vault/test-plan-2026-11-16.md`. Scratch database and servers (127.0.0.1:3001 / 8001); real Gmail, PayMongo test mode, Cloudinary; no SMS, no video call.

## Checked and working

- Backend suite: 621 tests OK.
- Public pages (landing with real stats, about, contact, privacy, forgot password, admin sign-in): load with no console errors.
- Password reset code email sent through Gmail (5 s, no error).
- Sign-in: a wrong password shows the generic "Incorrect email or password."
- Client dashboard: BMI 29.1 Obese I (Asia-Pacific), TER 2,450 kcal (checked by hand), NRS-2002 1 No risk, next consultation, to-do to pay.
- Client Appointments: pending request, payment due with the 15-minute deadline, history.
- PayMongo test payment (GCash) → invoice turned Paid through the Billing page's sync; receipt pop-up with method and reference.
- Reschedule: RND offer (later times only), client accept (earlier session).

## Findings

| # | Page | Width | What | Severity | Status |
|---|------|-------|------|----------|--------|
| 1 | Client dashboard | desktop | "Upload Lab Results" panel title is title case (rule: sentence case) | wording | **fixed**: "Upload lab results" |
| 2 | Client Billing | desktop | ~12 s on "Loading your invoices…" while it checks PayMongo; the summary meanwhile says ₱0.00 / "Nothing to pay" | misleading | **fixed**: the list loads first, then the PayMongo check runs and refreshes only if something changed; RED ~12 s → GREEN 1.3 s with ₱1,600.00 shown |
| 3 | Client Appointments | desktop | Pay opens PayMongo in a separate pop-up window (by design); automated test had to open the link in the same tab | note | — |
| 4 | Contact support | desktop | "Sending…" for ~6 s: the support emails go out inside the request (on commit) | slow | **fixed**: support emails go out on a background thread after commit (`core/background.py run_after_commit`, inline under the test runner); RED ~6 s → GREEN 25 ms, no send errors logged |
| 5 | Route guard | all | A client could open RND pages (`/rnd-dashboard`, `/client-detail/1`) and see "Could not load" (API refused with 403, no data leaked); only admin pages were guarded | broken flow | **fixed**: `meta.role` ('rnd' on 10 pages, 'client' on 9) + `middleware/auth.global.ts` sends anyone else to their own dashboard; checked RED (stayed on the page) → GREEN (redirected), shared pages unaffected |
| 6 | Lab upload pop-up | desktop | The pop-up re-centres and jumps up when the fasting question appears, so a click lands on the wrong tick box | layout | **fixed**: the lab upload pop-up is pinned to the top and grows downward; RED jumped → GREEN top stays at 76 px when the fasting question appears |

| 7 | RND Earnings vs RND dashboard | desktop | "Earned this month" is ₱1,440 on Earnings but ₱720 on the dashboard (Earnings counts the paid, not yet completed Nov 19 consultation) | money wording | **fixed**: Earnings counts consultations completed this month (paid, not refunded), the dashboard's rule; test `test_earned_this_month_counts_completed_consultations_only` RED (₱1,440) → GREEN (₱720 on the page) |
| 8 | Booking review pop-up | desktop | BMI shown as 29.05; dashboard, screening and Meal Planning show 29.1 | consistency | **fixed**: BMI shows one decimal everywhere (booking review, NCP form and baseline, NCP review line, client Profile Settings); checked 29.1 in the NCP record |
| 9 | Diabetes template | desktop | Description and patient notes say low-GI / brown rice first, but the generated week uses well-milled rice and white bread (the seeded FNRI list may have no low-GI starches) | clinical question for an RND | left as is (user's call) |
| 10 | NCP form | desktop | Lab note link says "View them in a new tab" (lab files should open in a pop-up, never a new tab) | check | **fixed**: "View lab results" opens the patient's lab results in a pop-up over the NCP form (files open in their own pop-up); builds, not clicked through (the link only shows on an editable record) |
| 11 | Wording | desktop | Title case: "Patient Reviews" (Reviews page heading); "Returning patient" tag is blue (not in the palette) | wording | heading and tag **fixed**: "Patient reviews"; "Returning patient" is the green pill (other blue pills left: Self-reported, confirmed consultations, meal accents, paid out) |

| 12 | NCP record pop-up | phone | Not full screen on a phone (358 × 726 with margins, the page showed below it); CLAUDE.md says the NCP form goes full screen | layout | **fixed**: phone rule like the lab file pop-up; RED 358×726 → GREEN 390×844 |
| 13 | Consultation summary pop-up | phone | Not full screen (358 × 812): its phone rule was there but the shared overlay's 16 px padding still framed it | layout | **fixed**: `cs-overlay` padding 0 on phones; RED 358×812 → GREEN 390×844 |
| 14 | Help button | phone | The floating help button covers the bottom-right corner of content (for example the NRS-2002 figure on the patient chart) | layout | left as is (user's call) |

Mobile (390 × 844, the app inside a 390 px frame because Windows Chrome can't go narrower than ~500 px): no sideways scroll on any of 13 admin, 24 RND and 13 client page views. Pop-ups full screen: booking, screening, lab file, NCP record (after fix), consultation summary (after fix). Meal log with a photo (Cloudinary, private) saved from the phone view and shown back through the signed 10-minute link (640 × 480).

Admin checked and working: dashboard figures, RND application rejected with a reason (email sent), Users (counts), Appointments, Billing & Commission, Payouts, Platform Reports, Support reply (email sent, status Answered), Audit Logs, System Settings.

RND side checked and working: dashboard figures (₱800 fee, 10% commission, ₱720 share, 3-day hold), confirm booking (invoice + email), lab result accept, NCP record written and finalized (BP/glucose/HbA1c categories, PES pickers, TER/macro grams checked by hand), diabetes template week (Monday within 1% of 2,450 kcal), allergy row red + send confirmation locked behind the tick box and countdown, Undo / Discard changes, plan sent, My Patients, NCP Records, Food Exchange Search, Earnings, Reviews, Availability, PDF resource upload to Cloudinary + share (client notified), notifications, Profile Settings, role guard (RND sent away from client pages).

Also checked: lab result image upload → Cloudinary (private) and viewed back through the API; chat message sent live; support request SR-0001 sent.

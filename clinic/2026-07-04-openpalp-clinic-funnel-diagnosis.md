# OpenPalp Clinic — Zero-Bookings Funnel Diagnosis (v2, booking flow verified)

**Date:** 2026-07-04
**Diagnosed by:** Claude (read-only inspection via Claude-in-Chrome on pc1)
**Scope:** READ-ONLY. No Ads settings/budget changed. **No real booking submitted** — the booking flow was verified by inspecting its wiring and by benign endpoint probes only.
**Launch target:** 28 July 2026
**Context update from Mahmood:** the offering is pivoting from a 12-lead ECG test to the **palpitations clinic (OpenPalp)**, and the **website has already been redone for the clinic**. This v2 verifies the *new* live site and its booking flow, and pushes the repositioning work onto the Ads side.

---

## 0. TL;DR

- **✅ Confirmed: the current live site is the NEW clinic site.** `gulfecg.com` serves *"OpenPalp — Private Palpitations Programme in Hampstead"* fresh (HTTP 200, cache-busted, via Cloudflare), with palpitations-clinic content — not the old ECG-test version.
- **❌ The new booking flow does NOT work as a booking system.** It is **mailto-only with an unconditional "success" message**. There is **no server-side booking capture**. The `fetch` POST you were looking at is **not the booking mechanism** — it's an analytics page-view beacon (and it's failing with HTTP 400). **This is a stand-alone cause of zero bookings even if the ads were running.**
- **Mechanical blockers (a)** and **repositioning (b)** are separated below. The repositioning now lands **mostly on the Ads side**, because the site itself is already clinic-focused.

---

## PART A — Mechanical blockers (things that are simply broken)

### A1. 🔴 The booking flow silently fails — verified end-to-end

**How it actually works (from inspecting the live page's JS):**
- The screening form (`#screening-form`, submit button *"Send screening to Dr Ahmad"*, required fields **name, email, symptom, consent**) is submitted by a JS handler that:
  1. `preventDefault()`s the native submit;
  2. Builds a **`mailto:drmahmoodclinic@pm.me`** link packaging the patient's **name, email, phone, symptom** (via `encodeURIComponent`);
  3. Hands off to the device's email client;
  4. **Shows a success/confirmation state UNCONDITIONALLY** — there is no check that anything was actually sent (no `if`, `try/catch`, `.then`, or response check between building the mailto and showing "success").
- **There is NO server call in the booking handler.** Whole-page totals: **exactly 1 `fetch` and 0 `XHR`**, and the single `fetch` is the analytics beacon (below), *not* in the submit handler (`submitHandlerHasNoServerCall = true`). No Formspree/Netlify/EmailJS/Getform/Apps Script; no external JS.

**Why this produces zero bookings (and matches "only test emails"):**
- A patient fills the form, taps "Send screening to Dr Ahmad," and **sees a success message** — but the *only* delivery path is their own email client opening a pre-drafted email that **they must then manually send**.
- On **mobile** and for **webmail users** (no OS default mail client configured — very common, and most ad traffic is mobile), the `mailto:` opens nothing or a broken handoff, **yet the success message still shows**. The patient believes they've booked; **Dr Ahmad receives nothing.**
- The "only test emails" you saw are consistent with this: on *your* device a mail client is configured, so the handoff completes; real patients don't complete it.
- **No JavaScript errors and no CORS errors** are thrown — it fails *silently by design*. That's the trap.

**Where a booking "reaches Mahmood":** nowhere reliable. There is no inbox/DB/dashboard/webhook that receives submissions automatically. The only destination is a `mailto:` that depends entirely on the patient's device completing and sending the email.

### A2. 🟠 The analytics endpoint is failing (400) — no first-party analytics either
- The one `fetch` on the page is **`POST /api/analytics/pageview`** (a Cloudflare Pages Function). Probed responses:
  - `OPTIONS` → **200**, `Allow: POST` (endpoint exists, POST-only).
  - `GET` → **404** `{"error":"Not found"}`.
  - `POST {diagnostic:true}` → **400** `{"error":"path required"}` — it validates and expects a `path` field.
- The page's own page-view beacon also returns **400** in the live network log → **even page-view analytics aren't being recorded.** So Mahmood currently has no first-party traffic/analytics data, and (critically) **this endpoint is analytics only — it is not, and was never, a booking store.**

### A3. 🔴 Google Ads: not serving + all ads disapproved (unchanged from v1)
- Banner: *"None of your ads are running — Your campaigns and ad groups are paused or removed."*
- Two campaigns, **both Paused**: **GECG_KSA_AR** (£10/day, "Most ads disapproved") and **LCC | Search | 12-Lead ECG | London** (£5/day, "Some ads disapproved"). Plus 1 draft.
- Every ad: **"Not eligible — Disapproved (Destination not working +1 more), Campaign is paused."**
- Cause confirmed: the ad landing URLs **`gulfecg.com/تقرير`** and **`gulfecg.com/ecg-diary/report`** both return **404 "Page Not Found."** The ads point at dead ECG-era pages.
- Traffic to date (2 Jun–4 Jul): **6.11k impressions · 197 clicks · £1.00 CPC · £197 spent · 0.00 conversions**, spiking early June then flatlining.
- No account-level suspension observed (billing works).

### A4. 🟠 Conversion tracking dead + doesn't measure bookings (unchanged from v1)
- All 3 conversion actions broken: **Purchase** = *"Tag inactive. Last activity 16 Jun 2026 (18 days ago)"*; **Free read - ECG uploaded** = *Inactive*; **Page view** = *Inactive*.
- The **Leads goal group is empty** (*"You're not measuring any goals here right now"*), and there is **no booking/lead conversion action at all** — a booking could never register, so bidding is blind.

### A5. 🟡 Minor: mobile nav overflow
- Horizontal overflow (`scrollWidth ~1635 > viewport ~1425`) from the top `.nav-links` (8 items) not collapsing to a hamburger. Hurts the mostly-mobile experience.

---

## PART B — Repositioning (ECG-test → palpitations-clinic)

The **site is already repositioned** (clinic content, clinic CTA). So repositioning work is now **almost entirely on the Ads side** — aligning copy, keywords, targeting, and landing URL to the clinic the site already sells:

- **B1. Landing URL.** Point every ad's final URL at the **live clinic page** (`gulfecg.com/` or a dedicated clinic landing section) — not the dead `/تقرير` or `/ecg-diary/report` ECG pages.
- **B2. Ad copy.** Rewrite from *"Read Your ECG Online / Apple Watch ECG Report / 12-Lead ECG"* to the **palpitations-clinic consultation** (e.g., "Private palpitations assessment in Hampstead — free clinic consultation with a cardiologist, optional ECG & 1-week home rhythm monitoring, no referral").
- **B3. Keywords.** Shift from ECG-test/device terms (*read my ECG, Apple Watch ECG report, 12-lead ECG*) to **clinic-intent terms** (*heart palpitations clinic London, private cardiologist palpitations Hampstead, palpitations consultation, why is my heart racing appointment*). Add negatives for the old ECG-report intent.
- **B4. Geo/targeting.** The **GECG_KSA_AR (Saudi Arabia, Arabic)** campaign advertises to Saudi Arabia for an **in-person Hampstead** clinic — geographically incoherent for bookings. Repoint to Greater London / Hampstead catchment (or pause the KSA campaign) as part of the pivot.
- **B5. Conversion definition.** The booking to optimise toward is a **clinic booking (lead)** — define it accordingly (see fix plan), not "Purchase/ECG uploaded."

> Note: B1 (fixing the final URL to a live page) is also the mechanical fix for the "Destination not working" disapproval — it belongs to both A3 and B1. Do it once.

---

## Ranked root causes (most impactful first)

1. **🔴 Booking flow silently fails (mailto-only + false "success").** Even with perfect ads, real/mobile patients can't book and Dr Ahmad receives nothing. *(A1)*
2. **🔴 Ads can't serve — all ads disapproved (final URLs 404) and both campaigns paused.** No paid traffic reaches the site. *(A3 / B1)*
3. **🟠 Message/geo mismatch (ECG-test ads incl. Arabic KSA vs in-person London clinic).** Even if served, the paid intent/geography don't match the clinic. *(Part B)*
4. **🟠 No booking conversion action + tracking tags inactive since 16 Jun.** Bookings are invisible; bidding can't optimise; you can't tell what works. *(A4)*
5. **🟡 Analytics beacon 400 + mobile nav overflow.** No first-party analytics; degraded mobile UX. *(A2, A5)*

---

## Fix plan (do NOT rebuild the site — fix the booking submission + realign Ads)

### Site — fix the booking submission only (site is otherwise fine)
1. **⚑ Make submissions actually reach Mahmood, server-side.** Replace/augment the mailto-only handler so the form POSTs to a real destination the clinic controls — e.g. a Cloudflare Pages Function (a sibling to the existing `/api/analytics` function) that emails `drmahmoodclinic@pm.me` and/or stores the lead, **or** a hosted form/booking service (Formspree, Web3Forms, Cal.com/Calendly). *(Buildable in this repo — no third-party approval needed. Small, targeted change; not a rebuild.)*
2. **⚑ Gate the "success" message on an actual successful send.** Only show confirmation after the server responds OK; show a clear error + phone/email fallback otherwise. Removes the false-success trap.
3. Keep `mailto`/phone as a visible *secondary* fallback, never the primary capture.
4. **Fix the analytics `pageview` 400** (send the required `path` field) so first-party traffic is measured — useful to see whether the funnel is recovering.
5. Collapse the nav to a hamburger < ~900px; verify no horizontal scroll at 375px.
6. Re-test the full path on a real phone before enabling ads.

### Google Ads — realign to the clinic (the repositioning work)
1. **⚑ Mahmood — repoint every ad final URL to the live clinic page** (fixes "Destination not working"). *(A3/B1)*
2. **⚑ Mahmood — rewrite ad copy + keywords to the clinic consultation** and add negatives for ECG-report intent. *(B2/B3)*
3. **⚑ Mahmood — fix geo/targeting**: repoint or pause the Saudi Arabia / Arabic campaign for an in-person London clinic. *(B4)*
4. **Create a primary "Lead – Clinic booking" conversion** tied to the new server submission (from fix-plan site step 1) and put it in the Leads goal group; retire/repair the inactive ECG tags. *(A4/B5)*
5. **⚑ Mahmood — request re-review of the disapproved ads, then enable the campaign(s)**; confirm the £10/£5 daily budgets are intended.
6. Scale spend only after the booking submission, tracking, and approvals are all verified working.

### What needs Mahmood's sign-off vs what can be prepped
- **Needs Mahmood (Ads UI + decisions):** repoint final URLs, rewrite copy/keywords, fix geo / pause KSA campaign, request ad re-review, enable campaigns, confirm budgets, approve the conversion-action setup.
- **Can be prepped now (site code, no approval):** the server-side booking submission + gated success state, the analytics `path` fix, and the mobile-nav fix.

---

## Appendix — evidence log (verbatim / measured, 2026-07-04)

- Live site served fresh: `GET https://www.gulfecg.com/?cachebust=… → 200`, `server: cloudflare`; title *"OpenPalp — Private Palpitations Programme in Hampstead | London Cardiology Clinic."*
- Booking handler: whole page has **1 fetch, 0 XHR**; submit handler has **no fetch/XHR/sendBeacon**; builds `mailto:drmahmoodclinic@pm.me` with **name+email+phone+symptom** (`encodeURIComponent`); **success shown unconditionally** after mailto (no ok/try/then check). No console errors, no CORS errors on load.
- Analytics endpoint `/api/analytics/pageview`: `OPTIONS → 200 Allow: POST`; `GET → 404 {"error":"Not found"}`; `POST {diagnostic:true} → 400 {"error":"path required"}`; the page's own pageview POST → **400** in the network log.
- Ads landing pages: `gulfecg.com/تقرير` and `gulfecg.com/ecg-diary/report` → *"Page Not Found."*
- Ads banner: *"None of your ads are running…"*; ad status: *"Not eligible — Disapproved (Destination not working +1 more), Campaign is paused."*
- Campaigns: **GECG_KSA_AR** £10/day Paused "Most ads disapproved"; **LCC | Search | 12-Lead ECG | London** £5/day Paused "Some ads disapproved"; 1 draft.
- Account (2 Jun–4 Jul): Impr **6.11k**, Clicks **197**, CPC **£1.00**, Cost **£197**, Conversions **0.00**.
- Conversion tags: Purchase *"Tag inactive — last activity 16 Jun 2026 (18 days ago)"*; Free read - ECG uploaded *Inactive*; Page view *Inactive*; Leads goal group empty.

*Read-only caveat: I did not submit the form or send any email; the mailto/no-server-call finding comes from reading the page's own submit handler and confirming only one (analytics) network call exists. Endpoint statuses above are from benign OPTIONS/GET probes and one non-booking analytics POST.*

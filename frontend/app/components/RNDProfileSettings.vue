<template>
  <div class="profile-page">
    <!-- COVER + WHO YOU ARE (one card, same as the client profile) -->
    <section class="ps-hero">
      <div class="ps-cover">
        <img class="ps-cover-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="ps-cover-fade" aria-hidden="true"></span>
        <p class="ps-cover-k"><span aria-hidden="true"></span>My profile</p>
      </div>
      <div class="page-header ps-id">
        <div class="ps-id-row">
          <div class="ps-avatar-wrap">
            <!-- the app's own photo uploader, kept out of sight; the camera button opens its file picker -->
            <div ref="photoHost" class="ps-photo-host" aria-hidden="true">
              <ProfileIdentityHeader :name="identityName" :subtitle="identitySubtitle" :editable="true" @photo-changed="fireToast" />
            </div>
            <img v-if="auth.user?.profile_photo" :src="auth.user.profile_photo" class="ps-avatar" alt="" />
            <span v-else class="ps-avatar">{{ myInitials }}</span>
            <button type="button" class="ps-cam" aria-label="Change photo" @click="pickPhoto"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg></button>
          </div>
          <div class="ps-id-main">
            <h2 class="ps-name">{{ identityName }}</h2>
            <div class="ps-chips">
              <span v-if="personalInfo.prcVerified" class="ps-chip role verified-pill"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z" /></svg>PRC verified</span>
              <span v-if="personalInfo.email" class="ps-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg>{{ personalInfo.email }}</span>
              <span v-if="memberSince" class="ps-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>Member since {{ memberSince }}</span>
            </div>
          </div>
          <button v-if="!isEditing" class="ps-edit" type="button" :disabled="!profileLoaded" @click="editFromHero"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg>Edit profile</button>
        </div>
        <div v-if="profileLoaded" class="ps-facts">
          <div class="ps-fact"><span class="ps-fact-ico green"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3v5a4 4 0 0 0 8 0V3" /><path d="M10 12v2a5 5 0 0 0 10 0v-2" /><path d="M18 10a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /></svg></span><div><strong>{{ personalInfo.specialization || 'Not set' }}</strong><small>Specialization</small></div></div>
          <div class="ps-fact"><span class="ps-fact-ico gold"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></span><div><strong>{{ personalInfo.consultationFee === '' ? 'Not set' : `₱${Number(personalInfo.consultationFee).toLocaleString()}` }}</strong><small>Per session</small></div></div>
          <div v-if="ratingInfo" class="ps-fact"><span class="ps-fact-ico blue"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg></span><div><strong>{{ ratingInfo.avg }} ★</strong><small>{{ ratingInfo.count }} {{ ratingInfo.count === 1 ? 'review' : 'reviews' }}</small></div></div>
          <div v-else class="ps-fact"><span class="ps-fact-ico blue"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg></span><div><strong>No rating yet</strong><small>0 reviews</small></div></div>
          <div class="ps-fact"><span class="ps-fact-ico" :class="personalInfo.acceptingNewClients ? 'green' : 'muted'"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><path d="M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M20 8v6M23 11h-6" /></svg></span><div><strong>{{ personalInfo.acceptingNewClients ? 'Taking clients' : 'Not taking clients' }}</strong><small>Status</small></div></div>
        </div>
      </div>
    </section>

    <div class="profile-layout">
      <!-- TABS -->
      <div ref="tabCard" class="tab-card">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" :size="17" />
          {{ tab.label }}
        </button>
      </div>

      <!-- PANEL -->
      <div class="panel-card" :class="{ 'is-cards': activeTab === 'professional', 'is-one': activeTab === 'professional', 'is-editing': isEditing, 'is-plain': ['security', 'reviews', 'history'].includes(activeTab) }">
        <!-- ============ PROFESSIONAL PROFILE ============ -->
        <!-- Same pattern as the client's Personal Info tab: read-only until
             "Edit Profile"; Cancel/Save replace it while editing. -->
        <template v-if="activeTab === 'professional'">
          <!-- CARD: basic details -->
          <section class="ps-card col-basic">
          <header class="ps-card-head"><span class="ps-card-ico green"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg></span><div><h3>Basic details</h3><p>How patients see and contact you.</p></div></header>
          <!-- READ-ONLY VIEW -->
          <template v-if="!isEditing">
            <dl class="info-grid">
              <div class="info-item"><span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg></span><dt>First name</dt><dd :class="{ muted: !personalInfo.firstName }">{{ personalInfo.firstName || 'Not provided' }}</dd></div>
              <div class="info-item"><span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg></span><dt>Last name</dt><dd :class="{ muted: !personalInfo.lastName }">{{ personalInfo.lastName || 'Not provided' }}</dd></div>
              <div class="info-item"><span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg></span><dt>Email address</dt><dd>{{ personalInfo.email }}</dd></div>
              <div class="info-item"><span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" /></svg></span><dt>Mobile number</dt><dd :class="{ muted: !personalInfo.phone }">{{ formatPhone(personalInfo.phone) || 'Not provided' }}</dd></div>
            </dl>
          </template>

          <!-- EDIT FORM -->
          <div v-else class="form-grid">
            <div class="field">
              <label class="field-label" for="rp-first">First name</label>
              <input id="rp-first" v-model="personalInfo.firstName" type="text" class="field-input" :class="{ invalid: fieldErrors.firstName }" maxlength="150" />
              <p v-if="fieldErrors.firstName" class="field-error">{{ fieldErrors.firstName }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="rp-last">Last name</label>
              <input id="rp-last" v-model="personalInfo.lastName" type="text" class="field-input" :class="{ invalid: fieldErrors.lastName }" maxlength="150" />
              <p v-if="fieldErrors.lastName" class="field-error">{{ fieldErrors.lastName }}</p>
            </div>
            <div class="field">
              <label class="field-label">Email address</label>
              <input :value="personalInfo.email" type="email" class="field-input" disabled />
              <p class="field-hint">Email can't be changed here.</p>
            </div>
            <div class="field">
              <label class="field-label" for="rp-phone">Mobile number</label>
              <PhoneInput id="rp-phone" v-model="personalInfo.phone" label="mobile number" rnd :error="fieldErrors.phone" />
              <p v-if="!fieldErrors.phone" class="field-hint">Required. A Philippine mobile number, never shown to clients.</p>
            </div>
          </div>

          </section>

          <!-- PRC LICENSE — always read-only: set at registration, checked by the admin -->
          <section class="ps-card prc-section col-prc">
            <div class="prc-header ps-card-head">
              <span class="ps-card-ico gold"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z" /></svg></span>
              <div class="prc-title"><h3>PRC license</h3><p>Checked by NutriMatch when you applied.</p></div>
              <span class="prc-status" :class="personalInfo.prcVerified ? 'prc-verified' : 'prc-pending'">
                {{ personalInfo.prcVerified ? 'Verified' : 'Waiting for the admin to check' }}
              </span>
            </div>
            <dl class="info-grid">
              <div class="info-item"><span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 9h14M5 15h14M11 4L7 20M17 4l-4 16" /></svg></span><dt>License number</dt><dd :class="{ muted: !personalInfo.prcNumber }">{{ personalInfo.prcNumber || 'Not provided' }}</dd></div>
              <div class="info-item"><span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span><dt>Verified on</dt><dd :class="{ muted: !personalInfo.prcVerifiedOn }">{{ personalInfo.prcVerifiedOn || 'Not yet verified' }}</dd></div>
              <div class="info-item"><span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3v5a4 4 0 0 0 8 0V3" /><path d="M10 12v2a5 5 0 0 0 10 0v-2" /><path d="M18 10a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /></svg></span><dt>Specialization</dt><dd :class="{ muted: !personalInfo.specialization }">{{ personalInfo.specialization || 'Not set' }}</dd></div>
            </dl>
            <button v-if="personalInfo.prcPhotoUrl" type="button" class="prc-photo-link licp" aria-label="Open license photo" aria-haspopup="dialog" @click="licenseOpen = true">
              <span class="licp-img"><img :src="personalInfo.prcPhotoUrl" alt="Your PRC license" loading="lazy" /></span>
              <span class="licp-cap"><FileImage :size="14" aria-hidden="true" /> License photo<em><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" /></svg>Tap to enlarge</em></span>
            </button>
            <p class="field-hint prc-note"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg><span>PRC details can't be edited here. Contact the NutriMatch admin.</span></p>
          </section>

          <!-- CARD: practice -->
          <section class="ps-card col-practice">
          <header class="ps-card-head"><span class="ps-card-ico blue"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18" /></svg></span><div><h3>Practice</h3><p>What patients see on your public profile.</p></div></header>

          <div class="newclients-row">
            <span class="nc-ico" aria-hidden="true"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><path d="M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M20 8v6M23 11h-6" /></svg></span>
            <div class="nc-txt">
              <p class="newclients-label">Taking new clients</p>
              <p class="field-hint">{{ personalInfo.acceptingNewClients
                ? 'New clients can find and book you. Turn it off when your schedule is full.'
                : 'Hidden from new clients on Find an RND. Your current patients can still book you.' }}</p>
            </div>
            <label class="toggle">
              <input v-model="personalInfo.acceptingNewClients" type="checkbox" :disabled="!isEditing" aria-label="Taking new clients" />
              <span class="toggle-track"><span class="toggle-thumb" /></span>
            </label>
          </div>

          <!-- READ-ONLY: bio / fee / formats -->
          <dl v-if="!isEditing" class="info-stack">
            <div class="info-item info-bio">
              <span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10" /></svg></span><dt>Professional bio</dt>
              <dd :class="{ muted: !personalInfo.bio }" class="bio-text">{{ personalInfo.bio || 'Not provided' }}</dd>
            </div>
            <div class="info-item">
              <span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></span><dt>Consultation fee</dt>
              <dd :class="{ muted: personalInfo.consultationFee === '' }">
                {{ personalInfo.consultationFee === '' ? 'Not set' : `₱${Number(personalInfo.consultationFee).toLocaleString()} per session` }}
              </dd>
            </div>
            <div class="info-item">
              <span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="14" height="12" rx="2" /><path d="M22 8l-6 4 6 4z" /></svg></span><dt>Consultation formats</dt>
              <dd>
                <span v-if="!personalInfo.consultationModes.length" class="muted">None offered</span>
                <span v-for="m in MODE_OPTIONS.filter(o => personalInfo.consultationModes.includes(o.value))" :key="m.value" class="mode-chip">
                  <component :is="m.icon" :size="14" /> {{ m.label }}
                </span>
              </dd>
            </div>
            <div v-if="personalInfo.consultationModes.includes('in_person')" class="info-item">
              <span class="fi"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z" /><circle cx="12" cy="9" r="2.5" /></svg></span><dt>Clinic address</dt>
              <dd :class="{ muted: !personalInfo.clinicAddress }">
                {{ personalInfo.clinicAddress || 'Not added yet. Clients can\'t book in-person consultations until you add it.' }}
              </dd>
            </div>
          </dl>

          <template v-else>
            <div class="field field-bio">
              <div class="bio-label-row">
                <label class="field-label" for="rp-bio">Professional bio</label>
                <span class="bio-count" :class="{ 'bio-count-warn': personalInfo.bio.length > 500 }">{{ personalInfo.bio.length }}/500</span>
              </div>
              <textarea
                id="rp-bio"
                v-model="personalInfo.bio"
                maxlength="500"
                rows="4"
                class="field-input bio-textarea"
                :class="{ invalid: fieldErrors.bio }"
                :aria-invalid="!!fieldErrors.bio || undefined"
                placeholder="Tell patients about your background, specialization, and approach to nutrition care..."
              ></textarea>
              <p v-if="fieldErrors.bio" class="field-error">{{ fieldErrors.bio }}</p>
              <p class="field-hint">Optional, at least 50 characters. Shown on Find an RND and your profile, and it helps clients choose you.</p>
            </div>

            <div class="field field-bio fee-field">
              <label class="field-label" for="rp-fee">Consultation fee</label>
              <div class="fee-input-wrap">
                <span class="fee-prefix">₱</span>
                <input id="rp-fee" v-model="personalInfo.consultationFee" type="number" min="100" step="50" class="field-input fee-input" :class="{ invalid: fieldErrors.fee }" :aria-invalid="!!fieldErrors.fee || undefined" placeholder="e.g. 750" />
                <span class="fee-suffix">per session</span>
              </div>
              <p v-if="fieldErrors.fee" class="field-error">{{ fieldErrors.fee }}</p>
              <p class="field-hint">At least ₱100. Shown to patients on Find an RND and your profile. Changes apply to future invoices only.</p>
            </div>

            <div class="field field-bio">
              <label class="field-label">Consultation formats</label>
              <div class="mode-options" role="group" aria-label="Consultation formats" :aria-invalid="!!fieldErrors.modes || undefined">
                <label v-for="m in MODE_OPTIONS" :key="m.value" class="mode-option" :class="{ checked: personalInfo.consultationModes.includes(m.value) }">
                  <input v-model="personalInfo.consultationModes" type="checkbox" :value="m.value" />
                  <component :is="m.icon" :size="15" /> {{ m.label }}
                </label>
              </div>
              <p v-if="fieldErrors.modes" class="field-error">{{ fieldErrors.modes }}</p>
              <p class="field-hint">Patients can only book the formats you offer.</p>
            </div>

            <div v-if="personalInfo.consultationModes.includes('in_person')" class="field field-bio">
              <label class="field-label" for="rp-address">Clinic address</label>
              <input id="rp-address" v-model="personalInfo.clinicAddress" type="text" class="field-input" :class="{ invalid: fieldErrors.clinicAddress }"
                maxlength="255" placeholder="e.g. 2F Bajada Medical Bldg, J.P. Laurel Ave, Bajada, Davao City" />
              <p v-if="fieldErrors.clinicAddress" class="field-error">{{ fieldErrors.clinicAddress }}</p>
              <p v-else class="field-hint">Where clients go for in-person consultations. It's shown on your profile.</p>
            </div>
          </template>

          <!-- Languages change only in Edit profile and save with Save changes -->
          <section class="lang-section" aria-labelledby="rp-lang-title">
            <h4 id="rp-lang-title" class="lang-title"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg>Languages</h4>
            <p class="field-hint lang-hint">Languages you can talk with patients in. Clients filter RNDs by these.</p>
            <div v-if="languages.length" class="language-list">
              <span v-for="lang in languages" :key="lang.id" class="language-pill">
                {{ lang.name }}
                <button v-if="isEditing" class="pill-icon-btn" type="button" :aria-label="`Remove ${lang.name}`" @click="removeLanguage(lang)"><X :size="13" /></button>
              </span>
            </div>
            <p v-else class="empty-note">No languages added yet.</p>
            <div v-if="isEditing && availableLanguageOptions.length" class="language-add-row">
              <select v-model="newLanguage" class="nm-select language-select" aria-label="Add a language">
                <option value="">Pick a language</option>
                <option v-for="opt in availableLanguageOptions" :key="opt.code" :value="opt.code">{{ opt.name }}</option>
              </select>
              <button class="btn-dark" type="button" :disabled="!newLanguage" @click="addLanguage">Add</button>
            </div>
            <p v-if="languageError" class="profile-error lang-error">{{ languageError }}</p>
          </section>

          <p v-if="profileError" class="profile-error">{{ profileError }}</p><!-- only when the profile could not load -->

          <!-- Cancel / Save sit at the end of the form, after everything they save -->
          <div v-if="isEditing" class="edit-actions">
            <button class="outline-btn" type="button" :disabled="isSavingProfile" @click="cancelEdit">Cancel</button>
            <button class="btn-dark" type="button" :disabled="isSavingProfile" @click="saveChanges">
              <Check :size="15" /> {{ isSavingProfile ? 'Saving…' : 'Save changes' }}
            </button>
          </div>
          </section>
        </template>

        <!-- ============ EARNINGS ============ -->
        <!-- ============ AVAILABILITY ============ -->
        <template v-else-if="activeTab === 'availability'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Availability</h3>
              <p class="tab-panel-sub">Set the hours clients can book consultations with you.</p>
            </div>
            <button class="outline-btn" type="button" @click="availabilityRef?.openWeekForm()"><Plus :size="15" aria-hidden="true" /> Add hours for all week</button>
          </div>

          <!-- Real, saved schedule (RndAvailabilitySchedule) — the same one
               clients see on your profile and in the booking calendar. -->
          <Availability ref="availabilityRef" embedded />
        </template>

        <!-- ============ SECURITY ============ -->
        <!-- Change password right here (POST /api/auth/me/password/): current
             password + a new one with the sign-up rules; a confirmation email
             goes out. Sign out lives in the account menu. -->
        <template v-else-if="activeTab === 'notifications'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Notifications</h3>
              <p class="tab-panel-sub">How NutriMatch gets your attention while it's open.</p>
            </div>
          </div>
          <NotificationSoundToggle />
        </template>

        <template v-else-if="activeTab === 'security'">
          <!-- change password on the left, the rules and notes on the right -->
          <div class="sec">
          <form class="pw-form sec-form" novalidate @submit.prevent="changePassword">
            <header class="sec-head"><span class="sec-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg></span><div><p class="pw-title">Change password</p><p class="sec-sub">Use your current password, then pick a new one.</p></div></header>
            <div class="field">
              <label class="field-label" for="rpw-current">Current password</label>
              <div class="sec-in"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="8" cy="15" r="4" /><path d="M10.8 12.2L20 3M17 6l3 3M15 8l2 2" /></svg><input id="rpw-current" v-model="pw.current" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pwErrors.current_password }" autocomplete="current-password" placeholder="Enter your current password" /></div>
              <p v-if="pwErrors.current_password" class="field-error">{{ pwErrors.current_password }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="rpw-new">New password</label>
              <div class="sec-in"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg><input id="rpw-new" v-model="pw.next" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pwErrors.new_password }" autocomplete="new-password" placeholder="Create a new password" /></div>
              <p v-if="pwErrors.new_password" class="field-error">{{ pwErrors.new_password }}</p>
              <div v-if="pw.next" class="sec-meter" :class="pwStrength.cls" aria-hidden="true"><i v-for="n in pwRules.length" :key="n" :class="{ on: n <= pwDone }" /><b>{{ pwStrength.label }}</b></div>
            </div>
            <div class="field">
              <label class="field-label" for="rpw-confirm">Confirm new password</label>
              <div class="sec-in"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg><input id="rpw-confirm" v-model="pw.confirm" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pw.confirm && pw.confirm !== pw.next }" autocomplete="new-password" placeholder="Type it again" /></div>
              <p v-if="pw.confirm && pw.confirm !== pw.next" class="field-error">The passwords don't match.</p>
            </div>
            <label class="pw-show"><input v-model="showPw" type="checkbox" /> Show passwords</label>
            <div class="pw-actions">
              <button type="submit" class="btn-dark sec-go" :disabled="savingPw || !canChangePw"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z" /><path d="M9 12l2 2 4-4" /></svg>{{ savingPw ? 'Changing…' : 'Change password' }}</button>
              <NuxtLink to="/forgot-password" class="pw-forgot">Forgot your current password?</NuxtLink>
            </div>
          </form>

          <aside class="sec-side">
            <header class="sec-head"><span class="sec-ico gold"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z" /><path d="M9 12l2 2 4-4" /></svg></span><div><p class="pw-title">Password rules</p><p class="sec-sub">Your new password needs all {{ pwRules.length }}.</p></div></header>
            <ul class="pw-rules" aria-label="Password rules">
              <li v-for="r in pwRules" :key="r.label" :class="{ ok: r.ok }"><span class="pr-dot"><svg v-if="r.ok" class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg><svg v-else class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3" /></svg></span>{{ r.label }}</li>
            </ul>
            <p class="rules-k">{{ pwDone }} of {{ pwRules.length }} done</p>
            <div class="side-note"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg><div><b>We'll email you</b><small>We'll email you to confirm the change<template v-if="personalInfo.email">, at {{ personalInfo.email }}</template>.</small></div></div>
            <div class="side-note"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14M12 17h.01" /></svg><div><b>Can't remember it?</b><small>Use "Forgot your current password?" to get a reset link.</small></div></div>
          </aside>
          </div>
        </template>

        <!-- ============ REVIEWS (GET /api/rnd/reviews/, same as the Reviews page) ============ -->
        <template v-else-if="activeTab === 'reviews'">
          <div class="rv-wrap"><Reviews embedded /></div>
        </template>

        <!-- ============ HISTORY (GET /api/rnd/activity/, scheduling/rnd_activity.py) ============ -->
        <template v-else-if="activeTab === 'history'">
          <div class="hx">
          <div class="hx-bar">
            <div class="filter-tabs">
              <button v-for="f in HISTORY_FILTERS" :key="f.key" class="filter-tab" :class="{ active: historyFilter === f.key }" type="button" @click="historyFilter = f.key">
                <component :is="HISTORY_KINDS[f.key].icon" v-if="HISTORY_KINDS[f.key]" :size="15" aria-hidden="true" /><template v-else><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg></template>{{ f.label }}
              </button>
            </div>
            <button class="outline-btn print-btn" type="button" @click="printHistory"><Printer :size="16" /> Print</button>
          </div>
          <h3 class="hx-print-title">Your activity</h3>

          <p v-if="historyError" class="profile-error">{{ historyError }}</p>
          <p v-if="isLoadingHistory" class="placeholder-text">Loading…</p>
          <div v-else-if="!filteredHistory.length" class="empty-state">
            <ClipboardList :size="26" class="empty-icon" />
            <p>Nothing here yet.</p>
            <p class="empty-sub">Your consultations, records and meal plans show up here as you work with patients.</p>
          </div>
          <template v-else>
            <section v-for="g in historyGroups" :key="g.key" class="hg">
              <h4><b>{{ g.label }}</b><span>{{ g.date }}</span></h4>
              <div class="hl">
                <NuxtLink v-for="entry in g.items" :key="entry.key" :to="entry.link" class="entry-row">
                  <div class="entry-icon" :class="HIST_TONE[entry.type] || 'tone-green'" aria-hidden="true"><component :is="HISTORY_KINDS[entry.type]?.icon || ClipboardList" :size="17" /></div>
                  <div class="entry-info">
                    <p class="entry-title">{{ entry.title }}</p>
                    <p v-if="entry.detail" class="entry-detail">{{ entry.detail }}</p>
                  </div>
                  <span class="entry-time" :title="formatTimestamp(entry.at)">{{ timeOnly(entry.at) }}</span>
                  <span class="entry-go"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg></span>
                </NuxtLink>
              </div>
            </section>
            <div class="hx-pager"><ListPager v-model:page="historyPage" :pages="historyPages" /></div>
          </template>
          </div>
        </template>

        <!-- ============ OTHER TABS (still placeholder) ============ -->
        <template v-else>
          <p class="placeholder-text">{{ activeTabLabel }} settings go here.</p>
        </template>
      </div>
    </div>

    <!-- LICENSE PHOTO, full size (same pop-up as the admin's) -->
    <div v-if="licenseOpen && personalInfo.prcPhotoUrl" class="nm-modal-overlay" @click.self="licenseOpen = false">
      <div class="nm-modal license-modal" role="dialog" aria-modal="true" aria-labelledby="license-title">
        <div class="lm-head nm-modal-head">
          <span class="lm-icon"><BadgeCheck :size="18" aria-hidden="true" /></span>
          <div style="flex: 1; min-width: 0">
            <h3 id="license-title" class="nm-modal-title" style="margin: 0">Your PRC license</h3>
            <p class="lm-sub">License no. {{ personalInfo.prcNumber || 'not given' }}</p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="licenseOpen = false"><X :size="18" aria-hidden="true" /></button>
        </div>
        <div class="lm-photo"><img :src="personalInfo.prcPhotoUrl" alt="PRC license photo, full size" /></div>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-dark" @click="licenseOpen = false">Done</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import {
  Briefcase, BadgeCheck,
  CalendarClock, X, Shield, History, Printer, ClipboardList,
  CalendarCheck, FileText, UtensilsCrossed, UserRound, Star, Wallet,
  Video, Users, Lock, FileImage, Pencil, Check, Bell, Plus
} from 'lucide-vue-next'
import { formatPhone, rndPhoneError } from '~/utils/phone'
import { fieldsProblemText, focusFirstError } from '~/utils/focusFirstError'
import { apiErrorText, useToast } from '~/composables/useToast'

const { get, patch, post, put } = useApi()

definePageMeta({ layout: 'dashboard', title: 'Profile Settings' })

const tabs = [
  { key: 'professional', label: 'Professional profile', icon: Briefcase },
  { key: 'availability', label: 'Availability', icon: CalendarClock },
  { key: 'notifications', label: 'Notifications', icon: Bell },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'reviews', label: 'Reviews', icon: Star },
  { key: 'history', label: 'History', icon: History },
]

const route = useRoute()
const validTabKeys = tabs.map(t => t.key)

// Earnings moved to its own page (sidebar → Earnings).
if (route.query.tab === 'earnings') navigateTo('/earnings', { replace: true })
const activeTab = ref(validTabKeys.includes(route.query.tab) ? route.query.tab : 'professional')
const activeTabLabel = computed(() => tabs.find(t => t.key === activeTab.value)?.label)
const availabilityRef = ref(null)

/* ---------- PROFESSIONAL PROFILE ---------- */
const auth = useAuthStore()

const MODE_OPTIONS = [
  { value: 'video', label: 'Video', icon: Video },
  { value: 'in_person', label: 'In person', icon: Users },
]

const personalInfo = ref({
  firstName: '', lastName: '', email: '', phone: '', bio: '', consultationFee: '',
  consultationModes: [], clinicAddress: '', initials: '', avatarColor: '#D4A017',
  prcVerified: false, prcNumber: '', prcVerifiedOn: '', prcPhotoUrl: '',
  specialization: '', acceptingNewClients: true,
})
const isSavingProfile = ref(false)
const profileError = ref('')
const isEditing = ref(false)
const licenseOpen = ref(false)
const profileLoaded = ref(false)
// Last loaded profile — Cancel restores the form from it.
const lastLoaded = ref(null)
const fieldErrors = reactive({ firstName: '', lastName: '', phone: '', clinicAddress: '', fee: '', modes: '', bio: '' })

const identityName = computed(() => `RND ${personalInfo.value.firstName} ${personalInfo.value.lastName}`.trim())
const identitySubtitle = computed(() => {
  const since = auth.user?.created_at
    ? new Date(auth.user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    : ''
  return [personalInfo.value.email, since && `Member since ${since}`].filter(Boolean).join(', ')
})

function startEdit() {
  profileError.value = ''
  languageError.value = ''
  newLanguage.value = ''
  Object.keys(fieldErrors).forEach(k => { fieldErrors[k] = '' })
  isEditing.value = true
}
function cancelEdit() {
  if (lastLoaded.value) applyProfile(lastLoaded.value.user, lastLoaded.value.rndProfile)
  profileError.value = ''
  languageError.value = ''
  newLanguage.value = ''
  Object.keys(fieldErrors).forEach(k => { fieldErrors[k] = '' })
  isEditing.value = false
}

// Results go to the app's toast (2026-11-03), seen wherever the page is scrolled.
const toast = useToast()
function fireToast(message = 'Profile saved.') {
  toast.success(message, { id: 'profile' })
}

function applyProfile(user, rndProfile) {
  lastLoaded.value = { user, rndProfile }
  setLanguagesFrom(rndProfile)
  personalInfo.value.firstName = user.first_name || ''
  personalInfo.value.lastName = user.last_name || ''
  personalInfo.value.email = user.email || ''
  personalInfo.value.phone = user.phone || ''
  personalInfo.value.bio = rndProfile.bio || ''
  personalInfo.value.consultationFee = rndProfile.consultation_fee != null ? Number(rndProfile.consultation_fee) : ''
  personalInfo.value.consultationModes = [...(rndProfile.consultation_modes || [])]
  personalInfo.value.clinicAddress = rndProfile.clinic_address || ''
  personalInfo.value.specialization = rndProfile.specialization || ''
  personalInfo.value.acceptingNewClients = rndProfile.available_for_new_clients !== false
  // PRC — read-only. The photo link is signed and short-lived (it's a
  // private upload), so it's refreshed every time the profile loads.
  personalInfo.value.prcVerified = Boolean(rndProfile.is_verified)
  personalInfo.value.prcNumber = rndProfile.prc_license_number || ''
  personalInfo.value.prcVerifiedOn = rndProfile.verified_at
    ? new Date(rndProfile.verified_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : ''
  personalInfo.value.prcPhotoUrl = rndProfile.prc_license_image_url || ''
  personalInfo.value.initials = `${personalInfo.value.firstName[0] ?? ''}${personalInfo.value.lastName[0] ?? ''}`.toUpperCase()
}

async function loadProfessionalProfile() {
  try {
    const rndProfile = await get('/rnd/profile/')
    applyProfile(rndProfile.user, rndProfile)
    profileLoaded.value = true
  } catch {
    profileError.value = 'Could not load your profile. Please try again later.'
  }
}
onMounted(loadProfessionalProfile)

// Real RndLanguage rows (profiles/models.py LANGUAGES). Changed while editing
// and saved with the rest (PATCH /rnd/profile/ {languages: [codes]}); at
// least one language must stay.
const LANGUAGE_OPTIONS = [
  { code: 'en', name: 'English' },
  { code: 'tl', name: 'Filipino (Tagalog)' },
  { code: 'ceb', name: 'Bisaya (Cebuano)' },
  { code: 'ilo', name: 'Ilocano' },
  { code: 'hil', name: 'Hiligaynon (Ilonggo)' },
  { code: 'war', name: 'Waray' },
  { code: 'pam', name: 'Kapampangan' },
  { code: 'bcl', name: 'Bicolano' },
]
const languages = ref([])
const newLanguage = ref('')
const languageError = ref('')
const availableLanguageOptions = computed(() => LANGUAGE_OPTIONS.filter(o => !languages.value.some(l => l.code === o.code)))
function setLanguagesFrom(rndProfile) {
  languages.value = (rndProfile.languages || []).map(l => ({ id: l.language_code, code: l.language_code, name: l.language_name }))
}
function addLanguage() {
  const opt = LANGUAGE_OPTIONS.find(o => o.code === newLanguage.value)
  if (!opt) return
  languageError.value = ''
  languages.value = [...languages.value, { id: opt.code, code: opt.code, name: opt.name }]
  newLanguage.value = ''
}
function removeLanguage(lang) {
  if (languages.value.length === 1) {
    languageError.value = 'Keep at least one language. Clients filter RNDs by language.'
    return
  }
  languageError.value = ''
  languages.value = languages.value.filter(l => l.code !== lang.code)
}

const NAME_RE = /^[A-Za-zÀ-ÖØ-öø-ÿÑñ]+(?:[ '.-][A-Za-zÀ-ÖØ-öø-ÿÑñ]+)*\.?$/

async function saveChanges() {
  profileError.value = ''
  fieldErrors.firstName = fieldErrors.lastName = fieldErrors.phone = fieldErrors.clinicAddress = fieldErrors.fee = fieldErrors.modes = fieldErrors.bio = ''
  personalInfo.value.firstName = personalInfo.value.firstName.trim()
  personalInfo.value.lastName = personalInfo.value.lastName.trim()
  if (!personalInfo.value.firstName) fieldErrors.firstName = 'Enter your first name.'
  else if (!NAME_RE.test(personalInfo.value.firstName)) fieldErrors.firstName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  if (!personalInfo.value.lastName) fieldErrors.lastName = 'Enter your last name.'
  else if (!NAME_RE.test(personalInfo.value.lastName)) fieldErrors.lastName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  fieldErrors.phone = rndPhoneError(personalInfo.value.phone)
  if (!personalInfo.value.consultationModes.length) fieldErrors.modes = 'Offer at least one consultation format.'
  const address = (personalInfo.value.clinicAddress || '').trim()
  if (personalInfo.value.consultationModes.includes('in_person')) {
    if (!address) fieldErrors.clinicAddress = 'Add your clinic address so clients know where to go.'
    else if (address.length < 10) fieldErrors.clinicAddress = 'Enter the full address: building, street, barangay and city.'
  }
  const fee = personalInfo.value.consultationFee
  if (fee === '' || fee === null || Number(fee) < 100) fieldErrors.fee = 'The consultation fee must be at least ₱100.'
  // optional, but a written bio needs 50 characters (same rule as sign-up and the API)
  const bioLength = (personalInfo.value.bio || '').trim().length
  if (bioLength > 0 && bioLength < 50) fieldErrors.bio = `Write at least 50 characters (${bioLength} so far), or leave it empty for now.`
  if (Object.values(fieldErrors).some(Boolean)) {
    toast.problem(fieldsProblemText(await focusFirstError()), { id: 'profile' })
    return
  }
  isSavingProfile.value = true
  try {
    const [user, rndProfile] = await Promise.all([
      patch('/auth/me/', {
        first_name: personalInfo.value.firstName,
        last_name: personalInfo.value.lastName,
        phone: personalInfo.value.phone || null,
      }),
      patch('/rnd/profile/', {
        bio: personalInfo.value.bio,
        consultation_fee: Number(fee).toFixed(2),
        consultation_modes: personalInfo.value.consultationModes,
        clinic_address: personalInfo.value.consultationModes.includes('in_person') ? address : (address || null),
        languages: languages.value.map(l => l.code),
        available_for_new_clients: personalInfo.value.acceptingNewClients,
      }),
    ])
    applyProfile(user, rndProfile)
    await auth.fetchMe()
    isEditing.value = false
    fireToast()
  } catch (error) {
    const data = error?.data || {}
    const first = (v) => (Array.isArray(v) ? v[0] : v) || ''
    fieldErrors.firstName = first(data.first_name)
    fieldErrors.lastName = first(data.last_name)
    fieldErrors.phone = first(data.phone)
    fieldErrors.clinicAddress = first(data.clinic_address)
    fieldErrors.fee = first(data.consultation_fee)
    fieldErrors.modes = first(data.consultation_modes)
    fieldErrors.bio = first(data.bio)
    if (Object.values(fieldErrors).some(Boolean)) toast.problem(fieldsProblemText(await focusFirstError()), { id: 'profile' })
    else toast.error(apiErrorText(error, 'Could not save your changes. Please try again.'), { id: 'profile' })
  } finally {
    isSavingProfile.value = false
  }
}

/* ---------- HISTORY ---------- */
const HISTORY_KINDS = {
  consultation: { icon: CalendarCheck, cls: 'icon-gold' },
  ncp: { icon: FileText },
  meal_plan: { icon: UtensilsCrossed },
  patient: { icon: UserRound },
  review: { icon: Star, cls: 'icon-gold' },
  payout: { icon: Wallet },
}
const HISTORY_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'consultation', label: 'Consultations' },
  { key: 'ncp', label: 'NCP records' },
  { key: 'meal_plan', label: 'Meal plans' },
  { key: 'patient', label: 'Patients' },
  { key: 'review', label: 'Reviews' },
  { key: 'payout', label: 'Payouts' },
]
const historyEntries = ref([])
const historyFilter = ref('all')
const isLoadingHistory = ref(false)
const historyError = ref('')
let historyLoaded = false
const filteredHistory = computed(() =>
  historyFilter.value === 'all' ? historyEntries.value : historyEntries.value.filter(e => e.type === historyFilter.value))
const { page: historyPage, pages: historyPages, paged: pagedHistory } = usePager(filteredHistory, { resetOn: historyFilter })
async function loadHistory() {
  isLoadingHistory.value = true
  historyError.value = ''
  try {
    historyEntries.value = await get('/rnd/activity/')
    historyLoaded = true
  } catch {
    historyError.value = 'Could not load your activity. Please try again.'
  } finally {
    isLoadingHistory.value = false
  }
}
watch(activeTab, (tab) => { if (tab === 'history' && !historyLoaded) loadHistory() }, { immediate: true })
function formatTimestamp(iso) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}
function printHistory() {
  window.print()
}

/* ---------- SECURITY: change password (rules mirror PasswordComplexityValidator) ---------- */
const pw = reactive({ current: '', next: '', confirm: '' })
const pwErrors = ref({})
const savingPw = ref(false)
const showPw = ref(false)
const pwRules = computed(() => [
  { label: 'At least 8 characters', ok: pw.next.length >= 8 },
  { label: 'An uppercase letter', ok: /[A-Z]/.test(pw.next) },
  { label: 'A lowercase letter', ok: /[a-z]/.test(pw.next) },
  { label: 'A number', ok: /\d/.test(pw.next) },
  { label: 'A special character', ok: /[^A-Za-z0-9]/.test(pw.next) },
])
const canChangePw = computed(() => pw.current && pwRules.value.every(r => r.ok) && pw.next === pw.confirm)
async function changePassword() {
  pwErrors.value = {}
  if (!canChangePw.value) return
  savingPw.value = true
  try {
    await post('/auth/me/password/', { current_password: pw.current, new_password: pw.next })
    Object.assign(pw, { current: '', next: '', confirm: '' })
    showPw.value = false
    toast.success('Password changed. We emailed you a confirmation.', { id: 'password' })
  } catch (e) {
    const d = e?.data || {}
    const out = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]))
    pwErrors.value = out
    if (out.current_password || out.new_password) toast.problem(fieldsProblemText(await focusFirstError(), 'changing it'), { id: 'password' })
    else toast.error(apiErrorText(e, 'Could not change your password. Please try again.'), { id: 'password' })
  } finally {
    savingPw.value = false
  }
}

/* ---------- phones: keep the selected tab in view in the sideways strip ---------- */
const tabCard = ref(null)
function showActiveTab() {
  nextTick(() => {
    const strip = tabCard.value
    const btn = strip?.querySelector('.tab-item.active')
    if (!strip || !btn || strip.scrollWidth <= strip.clientWidth) return
    strip.scrollLeft = Math.min(Math.max(0, btn.offsetLeft - (strip.clientWidth - btn.offsetWidth) / 2), strip.scrollWidth - strip.clientWidth)
  })
}
watch(activeTab, showActiveTab)
onMounted(showActiveTab)


/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const myInitials = computed(() =>
  `${(personalInfo.value.firstName || '').charAt(0)}${(personalInfo.value.lastName || '').charAt(0)}`.toUpperCase() || 'RD'
)
const memberSince = computed(() => auth.user?.created_at
  ? new Date(auth.user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
  : '')
// hero Edit profile: open the Professional profile tab, then the same edit mode
function editFromHero() {
  activeTab.value = 'professional'
  startEdit()
}
// camera button: open the uploader's own file picker straight away
const photoHost = ref(null)
function pickPhoto() {
  const host = photoHost.value
  if (!host) return
  const input = host.querySelector('input[type="file"]')
  if (input) input.click()
  else host.querySelector('button, label')?.click()
}
// rating for the hero: uses the profile's own numbers if it sends them,
// otherwise counts the same reviews list the Reviews tab shows (read only)
const reviewStats = ref(null)
const ratingInfo = computed(() => {
  const p = lastLoaded.value?.rndProfile || {}
  const avg = p.average_rating ?? p.avg_rating ?? p.rating
  const count = p.review_count ?? p.reviews_count ?? p.total_reviews
  if (avg != null && Number(count) > 0) return { avg: Number(avg).toFixed(1), count: Number(count) }
  return reviewStats.value
})
onMounted(async () => {
  try {
    const res = await get('/rnd/reviews/')
    const list = Array.isArray(res) ? res : (res?.results || res?.reviews || [])
    const stars = list.map(r => Number(r.rating ?? r.stars ?? r.score)).filter(n => n > 0)
    if (stars.length) reviewStats.value = { avg: (stars.reduce((a, b) => a + b, 0) / stars.length).toFixed(1), count: stars.length }
  } catch { /* no reviews to show */ }
})
// security tab: how many password rules are met, for the meter and the count
const pwDone = computed(() => pwRules.value.filter(r => r.ok).length)
const pwStrength = computed(() => {
  const n = pwDone.value, all = pwRules.value.length
  if (n >= all) return { label: 'Strong', cls: 'strong' }
  if (n >= all - 2) return { label: 'Fair', cls: 'fair' }
  return { label: 'Weak', cls: 'weak' }
})
// history: entries on this page, grouped by day (newest first, as loaded)
const HIST_TONE = { consultation: 'tone-gold', meal_plan: 'tone-green', ncp: 'tone-blue', patient: 'tone-violet', review: 'tone-gold', payout: 'tone-teal' }
const dayKey = d => d.toLocaleDateString('en-CA')
function timeOnly(iso) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}
const historyGroups = computed(() => {
  const today = new Date()
  const yest = new Date(); yest.setDate(today.getDate() - 1)
  const groups = []
  for (const entry of pagedHistory.value) {
    const d = new Date(entry.at)
    const key = dayKey(d)
    let g = groups.find(x => x.key === key)
    if (!g) {
      const label = key === dayKey(today) ? 'Today'
        : key === dayKey(yest) ? 'Yesterday'
          : d.toLocaleDateString('en-US', { weekday: 'long' })
      g = { key, label, date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }), items: [] }
      groups.push(g)
    }
    g.items.push(entry)
  }
  return groups
})
</script>

<style scoped>
* { box-sizing: border-box; }

.profile-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.verified-pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: #e3efe7; color: #1e4a26; font-size: 0.8rem; font-weight: 600;
  padding: 6px 12px; border-radius: 999px; white-space: nowrap;
}

/* LAYOUT */
.profile-layout { display: grid; grid-template-columns: 280px 1fr; gap: 20px; align-items: start; }

.tab-card {
  background: #fff; border-radius: 14px; border: 1px solid #d9e3dc;
  box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09);
  padding: 8px; display: flex; flex-direction: column; gap: 2px;
}
.tab-item {
  display: flex; align-items: center; gap: 10px; text-align: left;
  border: none; background: none; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; font-weight: 600; color: #4a5a4a; cursor: pointer;
}
.tab-item:hover { background: #f4f7f5; }
.tab-item.active { background: #e3efe7; color: #0a4a37; }
.tab-item:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }

.panel-card {
  background: #fff; border-radius: 14px; border: 1px solid #d9e3dc; padding: 28px;
  box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09);
}

/* Buttons + read-only view — same as ClientProfileSettings.vue. */
.btn-dark {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  background: #0a4a37; color: #fff; border: none;
  padding: 9px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
  white-space: nowrap; font-family: inherit;
}
.btn-dark:hover:not(:disabled) { background: #00382a; }
.btn-dark:disabled { opacity: 0.5; cursor: not-allowed; }
.outline-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex-shrink: 0;
  border: none; background: #e3efe7; color: #0a4a37; border-radius: 8px;
  padding: 9px 16px; font-weight: 600; font-size: 0.82rem; cursor: pointer; white-space: nowrap; font-family: inherit;
}
.outline-btn:hover:not(:disabled) { background: #d3e7da; }
.outline-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; margin: 0 0 24px; }
.info-stack { margin: 0 0 8px; }
.info-item { padding: 14px 0; border-top: 1px solid #d9e3dc; min-width: 0; }
.info-grid .info-item:nth-child(-n + 2), .info-stack .info-item:first-child { border-top: none; padding-top: 0; }
.info-item dt { font-size: 0.78rem; font-weight: 600; color: #4a5a4a; margin: 0 0 4px; }
.info-item dd { font-size: 0.92rem; font-weight: 500; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.info-item dd.muted, .info-item .muted { color: #8a9a8a; font-weight: 400; }
.bio-text { white-space: pre-line; line-height: 1.55; font-weight: 400 !important; }
.mode-chip {
  display: inline-flex; align-items: center; gap: 6px; margin: 2px 8px 2px 0;
  background: #e3efe7; border: none; color: #1e4a26; border-radius: 999px;
  padding: 5px 12px; font-size: 0.8rem; font-weight: 600;
}
.field-error { font-size: 0.76rem; color: #c0392b; margin: 4px 0 0; }
.field-input.invalid { border-color: #c0392b; }
.prc-section .info-grid { margin-bottom: 12px; }


/* FORM */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 24px; margin-bottom: 24px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; margin: 0 0 8px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input {
  width: 100%; border: 1px solid #d9e3dc; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; color: #1a3a1a; font-family: inherit; background: #fff;
}
.field-input:focus { outline: none; border-color: #D4A017; }

.field-bio { margin-bottom: 24px; }
.bio-label-row { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 8px; }
.bio-label-row .field-label { margin: 0; }
.bio-count { font-size: 0.74rem; color: #9aaa9a; }
.bio-count-warn { color: #c0483a; font-weight: 600; }
.bio-textarea { resize: vertical; min-height: 90px; line-height: 1.55; font-family: inherit; }
.field-hint { font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; margin: 6px 0 0; }
.field-input:disabled { background: #f4f5f3; color: #8a9a8a; }

.prc-section { border: 1px solid #d9e3dc; border-radius: 12px; padding: 18px 20px; margin-bottom: 24px; background: #fff; }
.prc-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.prc-title { display: inline-flex; align-items: center; gap: 6px; margin: 0; }
.prc-status { font-size: 0.76rem; font-weight: 600; padding: 3px 10px; border-radius: 999px; white-space: nowrap; }
.prc-verified { background: #e3efe7; color: #1e4a26; }
.prc-pending { background: #fdf1d6; color: #b8860b; }
.prc-section .form-grid { margin-bottom: 12px; }
.prc-photo-link {
  display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; font-weight: 600;
  color: #0a4a37; text-decoration: none; background: #e3efe7; border-radius: 8px; min-height: 36px; padding: 0 14px;
}
.prc-photo-link { border: 0; cursor: pointer; font-family: inherit; }
.prc-photo-link:hover { background: #d3e7da; }
.license-modal { max-width: 900px; }
.lm-head { display: flex; gap: 12px; align-items: flex-start; }
.lm-icon { width: 36px; height: 36px; border-radius: 9px; background: #e3efe7; color: #0a4a37; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.lm-sub { margin: 2px 0 0; font-size: 0.82rem; color: #6b7a70; }
.lm-photo { margin-top: 16px; border: 1px solid #d9e3dc; border-radius: 12px; overflow: auto; background: #f7faf8; display: flex; justify-content: center; }
.lm-photo img { display: block; max-width: 100%; max-height: 70vh; object-fit: contain; }
@media (max-width: 640px) {
  .license-modal { max-width: none; height: 100%; max-height: none; border-radius: 0; display: flex; flex-direction: column; }
  .lm-photo { flex: 1; align-items: center; }
}
.fee-input-wrap { display: flex; align-items: center; gap: 8px; max-width: 320px; margin-top: 8px; }
.fee-prefix { font-weight: 700; color: #1a3a1a; }
.fee-input { flex: 1; min-width: 0; }
.fee-suffix { font-size: 0.8rem; color: #9aaa9a; white-space: nowrap; }
.mode-options { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
.mode-option {
  display: inline-flex; align-items: center; gap: 7px; border: 1.5px solid #d9e3dc; border-radius: 10px;
  padding: 9px 14px; font-size: 0.84rem; font-weight: 600; color: #4a5a4a; cursor: pointer; background: #fff;
}
.mode-option input { accent-color: #1f8f5c; margin: 0; }
.mode-option.checked { border-color: #1f8f5c; background: #e3efe7; color: #1a3a1a; }
.profile-error { font-size: 0.82rem; color: #a12525; margin: 0 0 12px; }
.profile-saved { font-size: 0.82rem; color: #1f8f5c; font-weight: 600; margin: 0 0 12px; }

.save-btn {
  display: flex; align-items: center; gap: 6px;
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 12px 22px; font-weight: 700; font-size: 0.88rem; cursor: pointer; white-space: nowrap;
}
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* LANGUAGES (inside Professional profile) */
.lang-section { border-top: 1px solid #d9e3dc; padding-top: 18px; margin-top: 8px; }
.lang-title { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.lang-hint { margin: 2px 0 12px; }
.lang-error { margin-top: 10px; }
.language-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.language-pill { display: flex; align-items: center; gap: 6px; background: #e3efe7; color: #1e4a26; font-size: 0.8rem; font-weight: 600; padding: 6px 10px 6px 14px; border-radius: 20px; }
.language-add-row { display: flex; gap: 10px; align-items: center; }
.language-select { max-width: 260px; cursor: pointer; }

.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }
.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}

/* SHARED TAB PANEL HEADER */
.tab-panel-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; gap: 16px; }
.tab-panel-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 4px; }
.tab-panel-sub { font-size: 0.85rem; color: #6a7a6a; margin: 0; }
.empty-note { font-size: 0.85rem; color: #6a7a6a; margin: 0 0 16px; padding: 12px 14px; border: 1.5px dashed #3f9a6b; border-radius: 10px; }

.pill-icon-btn { background: none; border: none; color: #4a8a5a; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 2px; }
.pill-icon-btn:hover { color: #1a5a2a; }

/* MOBILE — same as the client settings page (ClientProfileSettings.vue):
   tabs become a sideways-scrolling strip above the panel. */
@media (max-width: 900px) {
  .profile-layout { grid-template-columns: 1fr; }
  .tab-card { position: relative; flex-direction: row; overflow-x: auto; scrollbar-width: none; }
  .tab-card::-webkit-scrollbar { display: none; }
  .tab-item { flex-shrink: 0; padding: 10px 12px; white-space: nowrap; }
  .panel-card { min-width: 0; }
}
@media (max-width: 640px) {
  .page-header { flex-direction: column; gap: 10px; }
  .page-title { font-size: 1.4rem; }
  .panel-card { padding: 20px 16px; }
  .form-grid, .info-grid { grid-template-columns: 1fr; }
  .info-grid .info-item:nth-child(2) { border-top: 1px solid #d9e3dc; padding-top: 14px; }
  .tab-panel-header { flex-direction: column; }
  .language-add-row { flex-wrap: wrap; }
}

.edit-actions { display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #d9e3dc; padding-top: 18px; margin-top: 20px; }
@media (max-width: 640px) { .edit-actions > * { flex: 1; } }

/* Taking new clients */
.newclients-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 16px 0 20px; padding: 14px 16px; border: 1px solid #d9e3dc; border-radius: 12px; background: #fff; }
.newclients-row .field-hint { margin: 2px 0 0; }
.newclients-label { margin: 0; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.toggle { position: relative; flex-shrink: 0; width: 42px; height: 24px; cursor: pointer; }
.toggle input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; }
.toggle-track { position: absolute; inset: 0; border-radius: 999px; background: #d5dad5; transition: background 0.2s; }
.toggle-thumb { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2); transition: transform 0.2s; }
.toggle input:checked + .toggle-track { background: #1f8f5c; }
.toggle input:checked + .toggle-track .toggle-thumb { transform: translateX(18px); }
.toggle input:focus-visible + .toggle-track { box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.25); }
.toggle input:disabled + .toggle-track { opacity: 0.6; }

/* Security — change password */
.pw-form { display: flex; flex-direction: column; gap: 14px; max-width: 440px; }
.pw-title { margin: 0; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.pw-rules { list-style: none; padding: 0; margin: 4px 0 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px 12px; }
.pw-rules li { display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: #8a9a8a; }
.pw-rules li.ok { color: #1f8f5c; }
.pw-dot { width: 6px; height: 6px; border-radius: 50%; border: 1px solid #b0bab0; margin: 0 3px; }
.pw-show { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #4a5a4a; cursor: pointer; }
.pw-actions { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.pw-forgot { font-size: 0.82rem; color: #0a4a37; font-weight: 600; text-decoration: underline; }
@media (max-width: 480px) { .pw-rules { grid-template-columns: 1fr; } }

/* History — mirrors ClientProfileSettings.vue */
.filter-tabs { display: inline-flex; gap: 4px; background: #f2f6f3; border-radius: 999px; padding: 3px; margin-bottom: 14px; flex-wrap: wrap; }
.filter-tab { border: none; background: none; padding: 6px 12px; border-radius: 999px; font-size: 0.76rem; font-weight: 600; color: #6a7a6a; cursor: pointer; font-family: inherit; }
.filter-tab.active { background: #0a4a37; color: #fff; }
.entry-row { display: flex; align-items: center; gap: 14px; padding: 13px 0; border-top: 1px solid #d9e3dc; text-decoration: none; color: inherit; }
.entry-row:hover .entry-title { text-decoration: underline; }
.entry-icon { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #e3efe7; color: #1e4a26; }
.entry-icon.icon-gold { background: #fdf1d6; color: #b8860b; }
.entry-info { flex: 1; min-width: 0; }
.entry-title { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.entry-detail { font-size: 0.78rem; color: #6a7a6a; margin: 2px 0 0; overflow-wrap: anywhere; }
.entry-time { font-size: 0.76rem; color: #6a7a6a; white-space: nowrap; }
.empty-state { padding: 30px; text-align: center; color: #6a7a6a; font-size: 0.85rem; }
.empty-state p { margin: 0; }
.empty-icon { color: #9ec4ad; margin-bottom: 8px; }
.empty-sub { font-size: 0.78rem; margin-top: 4px !important; }
.print-btn { display: inline-flex; align-items: center; gap: 6px; }
@media (max-width: 640px) {
  .entry-row { flex-wrap: wrap; }
  .entry-time { width: 100%; padding-left: 48px; }
}
@media print {
  .page-header, .tab-card, .print-btn, .filter-tabs { display: none !important; }
  .profile-layout { grid-template-columns: 1fr; }
}

/* =========================================================
   UI refresh — same look as the client profile settings
   ========================================================= */
.profile-page { font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }

/* hero */
.ps-hero { margin-bottom: 22px; border-radius: 24px; background: #fff; border: 1px solid #e4ebe6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 18px 36px -22px rgba(16, 35, 27, 0.35); }
.ps-cover { position: relative; overflow: hidden; height: 170px; border-radius: 24px 24px 0 0; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); }
.ps-cover-plate { position: absolute; right: -60px; top: 50%; width: 380px; height: 380px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.55; pointer-events: none; }
.ps-cover-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004d3a 0%, #004d3a 45%, rgba(0, 77, 58, 0.7) 65%, rgba(0, 70, 52, 0.1) 100%); pointer-events: none; }
.ps-cover-k { position: relative; z-index: 1; margin: 0; padding: 28px 34px; display: flex; align-items: center; gap: 10px; font-size: 12.5px; font-weight: 800; color: #efbf04; }
.ps-cover-k span { width: 26px; height: 2px; border-radius: 2px; background: #efbf04; }
.page-header.ps-id { display: block; margin: 0; padding: 0 34px 22px; }
.ps-id-row { display: flex; align-items: flex-end; gap: 24px; }
.ps-avatar-wrap { position: relative; flex-shrink: 0; margin-top: -58px; }
.ps-photo-host { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; clip: rect(0, 0, 0, 0); }
.ps-avatar { width: 124px; height: 124px; border-radius: 50%; display: flex; align-items: center; justify-content: center; object-fit: cover; background: linear-gradient(135deg, #f5cb1f, #c49102); color: #004d3a; font-family: 'Playfair Display', Georgia, serif; font-size: 40px; font-weight: 700; border: 5px solid #fff; box-shadow: 0 18px 34px -18px rgba(0, 0, 0, 0.5); }
.ps-cam { position: absolute; right: 2px; bottom: 6px; width: 38px; height: 38px; padding: 0; border-radius: 50%; border: 3px solid #fff; background: #004d3a; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ps-cam:hover { background: #0a5c46; }
.ps-id-main { flex: 1; min-width: 0; padding-top: 12px; }
.ps-name { margin: 0 0 10px; font-family: 'Playfair Display', Georgia, serif; font-size: 32px; font-weight: 700; line-height: 1.15; color: #0e3a2c; overflow-wrap: anywhere; }
.ps-id .page-sub { margin: 0 0 10px; font-size: 13.5px; color: #6b7d73; }
.ps-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.ps-chip { display: inline-flex; align-items: center; gap: 7px; min-height: 30px; padding: 4px 12px; border-radius: 999px; background: #f3f6f4; color: #3e5046; font-size: 13px; font-weight: 600; overflow-wrap: anywhere; }
.ps-chip .ic { color: #1f7a4d; }
.ps-chip.role, .ps-chip.verified-pill { margin: 0; background: #fbf3d2; color: #8a6400; box-shadow: none; }
.ps-chip.role .ic { color: #9a7300; }
.ps-edit { flex-shrink: 0; align-self: center; display: inline-flex; align-items: center; gap: 8px; height: 46px; padding: 0 22px; border: none; border-radius: 12px; background: #004d3a; color: #fff; font-family: inherit; font-size: 14.5px; font-weight: 700; cursor: pointer; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.ps-edit .ic { color: #efbf04; }
.ps-edit:hover:not(:disabled) { background: #035a45; }
.ps-edit:disabled { opacity: 0.6; cursor: default; }
.ps-facts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 18px; padding-top: 16px; border-top: 1px solid #eef2ef; }
.ps-fact { display: flex; align-items: center; gap: 12px; min-width: 0; }
.ps-fact-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; display: inline-flex; align-items: center; justify-content: center; }
.ps-fact-ico.green, .ps-card-ico.green { background: #e3efe7; color: #004d3a; }
.ps-fact-ico.gold, .ps-card-ico.gold { background: #fbf3d2; color: #9a7300; }
.ps-fact-ico.blue, .ps-card-ico.blue { background: #eef1fa; color: #3b5ba5; }
.ps-fact-ico.muted { background: #f3f6f4; color: #8a9a91; }
.ps-fact div { min-width: 0; }
.ps-fact strong { display: block; font-size: 15px; font-weight: 800; color: #0e3a2c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ps-fact small { font-size: 12.5px; color: #6b7d73; }

/* nav */
.profile-layout { grid-template-columns: 250px minmax(0, 1fr); gap: 22px; }
.tab-card { position: sticky; top: 96px; gap: 4px; padding: 10px; border: 1px solid #e4ebe6; border-radius: 20px; background: #fff; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.tab-item { height: 46px; padding: 0 14px; border-radius: 12px; font-family: inherit; font-size: 14.5px; font-weight: 600; color: #3e5046; transition: background-color 0.15s; }
.tab-item svg { color: #6b7d73; }
.tab-item:hover { background: #f3f6f4; }
.tab-item.active { background: #004d3a; color: #fff; }
.tab-item.active svg { color: #efbf04; }

/* panel: other tabs = one card; Professional profile = a stack of cards */
.panel-card { padding: 28px 30px; border: 1px solid #e4ebe6; border-radius: 22px; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.panel-card.is-cards { display: flex; flex-direction: column; gap: 18px; padding: 0; border: none; background: transparent; box-shadow: none; }
.ps-card { margin: 0; padding: 24px 26px; border: 1px solid #e4ebe6; border-radius: 22px; background: #fff; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.ps-card-head { display: flex; align-items: center; gap: 14px; margin: 0 0 18px; }
.ps-card-head > div { flex: 1; min-width: 0; }
.ps-card-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; }
.ps-card-head h3 { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; color: #0e3a2c; }
.ps-card-head p { margin: 4px 0 0; font-size: 13.5px; color: #6b7d73; }

/* read-only values: tiles with an icon */
.info-grid { gap: 12px; margin: 0; }
.info-stack { display: flex; flex-direction: column; gap: 12px; margin: 16px 0 0; }
.info-item,
.info-grid .info-item:nth-child(-n + 2),
.info-stack .info-item:first-child { display: grid; grid-template-columns: 40px minmax(0, 1fr); column-gap: 14px; align-items: center; padding: 14px 16px; border: 1px solid #edf2ee; border-radius: 16px; background: #f7faf8; }
.info-item .fi { grid-row: span 2; width: 40px; height: 40px; border-radius: 12px; background: #fff; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px -3px rgba(16, 35, 27, 0.25); }
.info-item.info-bio { align-items: start; }
.info-item dt { margin: 0 0 3px; font-size: 12.5px; font-weight: 600; color: #6b7d73; }
.info-item dd { font-size: 15px; font-weight: 700; color: #0e3a2c; }
.info-item dd.muted, .info-item .muted { color: #8a9a91; font-weight: 500; }
.bio-text { font-size: 14.5px !important; font-weight: 500 !important; line-height: 1.6; color: #3e5046 !important; }
.mode-chip { padding: 6px 12px; background: #fff; box-shadow: 0 2px 6px -3px rgba(16, 35, 27, 0.25); color: #004d3a; font-weight: 700; }

/* form */
.field-label { font-size: 13px; font-weight: 700; color: #22362c; }
.field-input { min-height: 46px; border: 1.5px solid #c9d8cf; border-radius: 12px; font-size: 14.5px; color: #14261e; }
.field-input:focus { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.field-input:disabled { border-color: #e3ebe6; background: #f3f6f4; color: #6b7d73; }
.mode-option { border-radius: 12px; }
.mode-option.checked { border-color: #004d3a; background: #f1f8f4; }
.btn-dark { height: 44px; padding: 0 20px; border-radius: 12px; background: #004d3a; font-size: 14px; font-weight: 800; }
.outline-btn { height: 42px; padding: 0 16px; border: 1px solid #dce8e0; border-radius: 12px; background: #fff; color: #004d3a; font-size: 13.5px; font-weight: 800; }
.edit-actions { border-top-color: #eef2ef; }

/* PRC card */
.prc-section { margin: 0; }
.prc-header.ps-card-head { justify-content: flex-start; }
.prc-header .prc-title { display: block; flex: 1; min-width: 0; margin: 0; }
.prc-status { display: inline-flex; align-items: center; padding: 5px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 800; }
.prc-verified { background: #e3f4ea; color: #1f7a4d; }
.prc-section .info-grid { margin: 0 0 12px; }
.prc-photo-link { display: flex; align-items: center; gap: 14px; width: 100%; max-width: 420px; height: auto; padding: 12px 16px; border: 1.5px dashed #cfe0d5; border-radius: 16px; background: #fff; color: #0e3a2c; font-family: inherit; text-align: left; cursor: pointer; }
.prc-photo-link:hover { border-color: #004d3a; background: #f7faf8; }
.lic-ico { flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.lic-txt { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.lic-txt b { font-size: 14.5px; font-weight: 800; color: #0e3a2c; }
.lic-txt small { font-size: 12.5px; color: #6b7d73; }
.prc-photo-link > .ic { color: #1f7a4d; }
.prc-note { display: flex; gap: 10px; align-items: flex-start; margin: 14px 0 0; padding: 12px 14px; border-radius: 14px; background: #fbf8ec; border: 1px solid #f1e6bd; font-size: 13px; color: #6b5400; }
.prc-note .ic { margin-top: 1px; color: #9a7300; }

/* taking new clients */
.newclients-row { gap: 14px; justify-content: flex-start; margin: 0; padding: 14px 16px; border: 1.5px solid #cfe6d7; border-radius: 16px; background: #f1f8f4; }
.nc-ico { flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; background: #fff; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.nc-txt { flex: 1; min-width: 0; }
.newclients-label { font-size: 15px; font-weight: 800; color: #0e3a2c; }
.toggle input:checked + .toggle-track { background: #004d3a; }
.toggle input:checked + .toggle-track .toggle-thumb { background: #efbf04; }

/* languages */
.lang-section { margin-top: 18px; padding-top: 18px; border-top: 1px solid #eef2ef; }
.lang-title { display: flex; align-items: center; gap: 8px; font-family: 'Playfair Display', Georgia, serif; font-size: 18px; color: #0e3a2c; }
.lang-title .ic { color: #3b5ba5; }
.language-pill { padding: 7px 12px 7px 14px; background: #fff; color: #004d3a; font-size: 13px; font-weight: 700; box-shadow: 0 0 0 1px #dce8e0; }

/* other tabs */
.tab-panel-title { font-family: 'Playfair Display', Georgia, serif; font-size: 21px; color: #0e3a2c; }
.tab-panel-sub { font-size: 13.5px; color: #6b7d73; }
.pw-rules { display: flex; flex-wrap: wrap; gap: 6px; }
.pw-rules li { padding: 4px 10px; border-radius: 999px; background: #f3f6f4; font-size: 12.5px; font-weight: 600; color: #6b7d73; }
.pw-rules li.ok { background: #e3f4ea; color: #1f7a4d; }
.filter-tab.active { background: #004d3a; }

@media (max-width: 1100px) { .ps-facts { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 900px) {
  .profile-layout { grid-template-columns: minmax(0, 1fr); }
  .tab-card { position: static; flex-direction: row; overflow-x: auto; padding: 6px; }
  .tab-item { flex-shrink: 0; height: 40px; }
}
@media (max-width: 760px) {
  .profile-page { padding-bottom: 110px; }
  .ps-cover { height: 90px; border-radius: 22px 22px 0 0; }
  .ps-cover-plate { width: 200px; height: 200px; right: -50px; }
  .ps-cover-k { padding: 16px 18px; }
  .page-header.ps-id { padding: 0 16px 18px; }
  .ps-id-row { flex-direction: column; align-items: center; gap: 10px; text-align: center; }
  .ps-avatar-wrap { margin-top: -56px; }
  .ps-avatar { width: 104px; height: 104px; font-size: 34px; border-width: 4px; }
  .ps-chips { justify-content: center; }
  .ps-name { font-size: 24px; }
  .ps-edit { align-self: stretch; justify-content: center; }
  .info-grid { grid-template-columns: minmax(0, 1fr); }
  .ps-card, .panel-card { padding: 20px 16px; }
}

/* =========================================================
   Tabs on top + one card (view mode)
   ========================================================= */
.profile-layout { display: block; }
.tab-card { position: sticky; top: 12px; z-index: 5; display: flex; flex-direction: row; align-items: center; gap: 6px; margin: 0 0 18px; padding: 8px; border-radius: 999px; overflow-x: auto; scrollbar-width: none; }
.tab-card::-webkit-scrollbar { display: none; }
.tab-item { flex-shrink: 0; width: auto; height: 42px; padding: 0 18px; border-radius: 999px; font-size: 14px; white-space: nowrap; }

/* license photo shown right in the card */
.prc-photo-link.licp { display: block; max-width: none; width: 100%; padding: 0; border: 1px solid #edf2ee; border-radius: 14px; background: #f7faf8; overflow: hidden; cursor: zoom-in; text-align: left; }
.licp-img { display: block; height: 130px; background: #e9f1ec; }
.licp-img img { display: block; width: 100%; height: 100%; object-fit: cover; }
.licp-cap { display: flex; align-items: center; gap: 7px; padding: 9px 12px; font-size: 13px; font-weight: 800; color: #0e3a2c; }
.licp-cap svg { color: #9a7300; }
.licp-cap em { margin-left: auto; display: inline-flex; align-items: center; gap: 5px; font-style: normal; font-size: 12px; font-weight: 600; color: #6b7d73; }
.licp-cap em svg { color: #6b7d73; }
.prc-photo-link.licp:hover { border-color: #004d3a; background: #f7faf8; }

/* view mode: Basic | Practice | PRC in one card */
.panel-card.is-one { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0; padding: 22px 8px; border: 1px solid #e4ebe6; border-radius: 22px; background: #fff; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.is-one > .ps-card { display: flex; flex-direction: column; gap: 8px; min-width: 0; margin: 0; padding: 0 20px; border: none; border-radius: 0; background: transparent; box-shadow: none; }
.is-one > .col-basic { order: 1; }
.is-one > .col-practice { order: 2; border-left: 1px solid #eef2ef; }
.is-one > .col-prc { order: 3; border-left: 1px solid #eef2ef; }
.is-one > .profile-error { order: 4; grid-column: 1 / -1; margin: 12px 20px 0; }
.is-one .ps-card-head { gap: 10px; margin: 0 0 6px; }
.is-one .ps-card-ico { width: 34px; height: 34px; border-radius: 11px; }
.is-one .ps-card-ico .ic { width: 17px; height: 17px; }
.is-one .ps-card-head h3 { font-size: 18px; }
.is-one .ps-card-head p { display: none; }
.is-one .info-grid, .is-one .info-stack { display: flex; flex-direction: column; gap: 8px; margin: 0; }
.is-one .info-item,
.is-one .info-grid .info-item:nth-child(-n + 2),
.is-one .info-stack .info-item:first-child { grid-template-columns: 32px minmax(0, 1fr); column-gap: 12px; padding: 9px 12px; border-radius: 13px; }
.is-one .info-item .fi { width: 32px; height: 32px; border-radius: 10px; }
.is-one .info-item .fi .ic { width: 16px; height: 16px; }
.is-one .info-item dt { margin: 0; font-size: 11.5px; }
.is-one .info-item dd { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.is-one .info-bio { order: 9; grid-template-columns: minmax(0, 1fr) !important; }
.is-one .info-bio .fi { display: none; }
.is-one .bio-text { white-space: normal !important; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; font-size: 13px !important; line-height: 1.5; }
.is-one .mode-chip { padding: 0; background: none; box-shadow: none; font-size: 14px; }
.is-one .mode-chip svg { display: none; }
.is-one .mode-chip + .mode-chip::before { content: ', '; }
.is-one .newclients-row { padding: 9px 12px; border-radius: 13px; }
.is-one .nc-ico { width: 32px; height: 32px; border-radius: 10px; }
.is-one .newclients-label { font-size: 13.5px; }
.is-one .newclients-row .field-hint { font-size: 12.5px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.is-one .prc-header .prc-status { padding: 4px 10px; font-size: 12px; }
.is-one .prc-section .info-grid { margin: 0; }
.is-one .prc-note { margin: 0; padding: 0; border: none; background: none; font-size: 12px; color: #6b7d73; align-items: center; }
.is-one .lang-section { margin: 4px 0 0; padding: 10px 12px; border: 1px solid #edf2ee; border-top: 1px solid #edf2ee; border-radius: 13px; background: #f7faf8; }
.is-one .lang-title { margin: 0 0 6px; font-family: inherit; font-size: 11.5px; font-weight: 600; color: #6b7d73; }
.is-one .lang-title .ic { width: 14px; height: 14px; }
.is-one .lang-hint { display: none; }
.is-one .language-pill { padding: 4px 10px; font-size: 12.5px; }

@media (max-width: 1100px) {
  .panel-card.is-one { grid-template-columns: minmax(0, 1fr); gap: 18px; }
  .is-one > .col-practice, .is-one > .col-prc { border-left: none; padding-top: 18px; border-top: 1px solid #eef2ef; }
}
@media (max-width: 760px) {
  .tab-card { top: 8px; border-radius: 16px; padding: 6px; }
  .tab-item { height: 38px; padding: 0 14px; font-size: 13.5px; }
  .is-one > .ps-card { padding: 0 14px; }
  .is-one > .col-practice, .is-one > .col-prc { padding-top: 18px; }
}

/* edit mode keeps the same one-card, three-column layout */
.is-one.is-editing { align-items: start; }
.is-one .form-grid { display: flex; flex-direction: column; gap: 10px; margin: 0; }
.is-one .field { gap: 4px; }
.is-one .field-bio { margin: 0; }
.is-one .field-label { font-size: 12px; }
.is-one .field-input { min-height: 40px; padding-top: 8px; padding-bottom: 8px; font-size: 14px; border-radius: 11px; }
.is-one .bio-label-row { margin-bottom: 4px; }
.is-one .bio-textarea { min-height: 84px; height: 84px; resize: vertical; font-size: 13.5px; line-height: 1.5; }
.is-one .field-hint { margin: 2px 0 0; font-size: 11.5px; line-height: 1.4; }
.is-one .field-error { margin: 2px 0 0; font-size: 12px; }
.is-one .fee-input-wrap { max-width: none; margin-top: 0; }
.is-one .mode-options { gap: 6px; margin-top: 0; }
.is-one .mode-option { padding: 7px 11px; font-size: 13px; }
.is-one.is-editing .col-practice { gap: 10px; }
.is-one .language-add-row { gap: 8px; margin-top: 8px; }
.is-one .language-select { flex: 1; min-width: 0; min-height: 38px; }
.is-one .language-add-row .btn-dark { height: 38px; padding: 0 14px; }
.is-one .edit-actions { margin: 6px 0 0; padding: 12px 0 0; border-top: 1px solid #eef2ef; }
.is-one .edit-actions .btn-dark, .is-one .edit-actions .outline-btn { flex: 1; justify-content: center; height: 42px; }

/* =========================================================
   Security tab: form left, rules right, no card
   ========================================================= */
.panel-card.is-plain { margin-top: 12px; padding: 0 56px; border: none; background: transparent; box-shadow: none; }
.sec { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
.sec-form { max-width: none; gap: 16px; padding: 8px 48px 8px 0; }
.sec-side { display: flex; flex-direction: column; padding: 8px 0 8px 48px; border-left: 1.5px solid #d3e0d8; }
.sec-head { display: flex; align-items: center; gap: 14px; margin-bottom: 4px; }
.sec-ico { flex-shrink: 0; width: 46px; height: 46px; border-radius: 14px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.sec-ico.gold { background: #fbf3d2; color: #9a7300; }
.sec .pw-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #0e3a2c; }
.sec-sub { margin: 3px 0 0; font-size: 14px; color: #4a5a52; }
.sec .field-label { font-size: 14px; }
.sec-in { position: relative; }
.sec-in > .ic { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #4a5a52; pointer-events: none; }
.sec-in .field-input { width: 100%; min-height: 50px; padding-left: 44px; border: 1.5px solid #b9c9bf; border-radius: 12px; font-size: 15px; background: #fff; }
.sec-meter { display: flex; align-items: center; gap: 6px; margin-top: 8px; }
.sec-meter i { flex: 1; height: 6px; border-radius: 3px; background: #e3ebe6; }
.sec-meter b { margin-left: 6px; font-size: 13px; }
.sec-meter.weak i.on { background: #d9534f; } .sec-meter.weak b { color: #b4384a; }
.sec-meter.fair i.on { background: #efbf04; } .sec-meter.fair b { color: #8a6400; }
.sec-meter.strong i.on { background: #1f7a4d; } .sec-meter.strong b { color: #1f7a4d; }
.sec .pw-show { gap: 10px; font-size: 14px; font-weight: 600; color: #22362c; }
.sec .pw-show input { width: 18px; height: 18px; accent-color: #004d3a; }
.sec .pw-actions { gap: 16px; margin-top: 4px; }
.sec-go { display: inline-flex; align-items: center; gap: 8px; height: 48px; padding: 0 24px; font-size: 15px; }
.sec-go .ic { color: #efbf04; }
.sec-go:disabled { background: #b9cdbf; opacity: 1; }
.sec-go:disabled .ic { color: #fff; }
.sec .pw-forgot { font-size: 14px; font-weight: 700; color: #004d3a; }
.sec-side .sec-head { margin-bottom: 14px; }
.sec-side .pw-rules { display: flex; flex-direction: column; gap: 12px; margin: 0; }
.sec-side .pw-rules li { display: flex; align-items: center; gap: 10px; padding: 0; border-radius: 0; background: none; font-size: 15px; font-weight: 600; color: #4a5a52; }
.pr-dot { flex-shrink: 0; width: 24px; height: 24px; border-radius: 50%; background: #eef2ef; color: #9aa8a0; display: inline-flex; align-items: center; justify-content: center; }
.sec-side .pw-rules li.ok { background: none; color: #0e3a2c; }
.sec-side .pw-rules li.ok .pr-dot { background: #1f7a4d; color: #fff; }
.rules-k { margin: 14px 0 20px; font-size: 13px; font-weight: 700; color: #1f7a4d; }
.side-note { display: flex; gap: 12px; align-items: flex-start; padding: 16px 0; border-top: 1.5px solid #dce7e0; }
.side-note:last-child { padding-bottom: 0; }
.side-note > .ic { margin-top: 2px; color: #9a7300; }
.side-note b { display: block; font-size: 14.5px; color: #0e3a2c; }
.side-note small { font-size: 13.5px; line-height: 1.45; color: #4a5a52; overflow-wrap: anywhere; }

@media (max-width: 960px) {
  .panel-card.is-plain { padding: 0 2px; }
  .sec { grid-template-columns: minmax(0, 1fr); }
  .sec-form { padding: 4px 0 22px; }
  .sec-side { padding: 22px 0 4px; border-left: none; border-top: 1.5px solid #d3e0d8; }
  .sec-go { width: 100%; justify-content: center; }
}

/* Reviews tab: no card, same side space as Security */
.rv-wrap { padding-top: 18px; }

/* =========================================================
   History tab: filters, day groups, timeline
   ========================================================= */
.hx { padding-top: 14px; }
.hx-bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 22px; }
.hx .filter-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin: 0; padding: 0; border-radius: 0; background: none; }
.hx .filter-tab { display: inline-flex; align-items: center; gap: 7px; height: 40px; padding: 0 16px; border: 1.5px solid #c9d8cf; border-radius: 999px; background: #fff; color: #22362c; font-size: 14px; font-weight: 700; }
.hx .filter-tab svg { color: #4a5a52; }
.hx .filter-tab:hover { border-color: #004d3a; }
.hx .filter-tab.active { background: #004d3a; border-color: #004d3a; color: #fff; }
.hx .filter-tab.active svg { color: #efbf04; }
.hx .print-btn { flex-shrink: 0; display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 18px; border: 1.5px solid #004d3a; border-radius: 12px; font-size: 14px; }
.hx-print-title { display: none; }
.hg { margin-bottom: 22px; }
.hg h4 { display: flex; align-items: baseline; gap: 10px; margin: 0 0 10px; }
.hg h4 b { font-family: 'Playfair Display', Georgia, serif; font-size: 19px; color: #0e3a2c; }
.hg h4 span { font-size: 13.5px; font-weight: 600; color: #4a5a52; }
.hl { position: relative; display: flex; flex-direction: column; gap: 6px; }
.hl::before { content: ''; position: absolute; left: 21px; top: 24px; bottom: 24px; width: 2px; background: #d3e0d8; }
.hx .entry-row { position: relative; display: grid; grid-template-columns: 44px minmax(0, 1fr) auto 18px; align-items: center; gap: 16px; padding: 12px 14px 12px 0; border-top: none; border-radius: 16px; }
.hx .entry-row:hover { background: #fff; box-shadow: 0 10px 22px -18px rgba(16, 35, 27, 0.45); }
.hx .entry-row:hover .entry-title { text-decoration: none; }
.hx .entry-icon { position: relative; z-index: 1; width: 44px; height: 44px; border: 3px solid #f4f7f5; }
.entry-icon.tone-gold { background: #fbf3d2; color: #9a7300; }
.entry-icon.tone-green { background: #ddefe4; color: #1f7a4d; }
.entry-icon.tone-blue { background: #e6ecf8; color: #3b5ba5; }
.entry-icon.tone-violet { background: #eee8f7; color: #6a4ba0; }
.entry-icon.tone-teal { background: #dff1ef; color: #1f7a72; }
.hx .entry-title { font-size: 15.5px; font-weight: 800; line-height: 1.35; color: #0e3a2c; }
.hx .entry-detail { margin-top: 3px; font-size: 13.5px; line-height: 1.45; color: #4a5a52; }
.hx .entry-time { font-size: 13.5px; font-weight: 700; color: #22362c; }
.entry-go { display: inline-flex; color: #9aa8a0; }
.hx .entry-row:hover .entry-go { color: #004d3a; }
.hx-pager { margin-top: 8px; padding-top: 18px; border-top: 1.5px solid #d3e0d8; }
.hx .empty-state { padding: 40px 20px; border: 1.5px dashed #c6d9cd; border-radius: 18px; background: #fff; font-size: 14.5px; color: #4a5a52; }

@media (max-width: 960px) {
  .hx-bar { flex-direction: column; align-items: stretch; }
  .hx .filter-tabs { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; }
  .hx .filter-tab { flex-shrink: 0; }
  .hx .print-btn { align-self: flex-end; }
  .hx .entry-row { grid-template-columns: 44px minmax(0, 1fr); row-gap: 4px; flex-wrap: nowrap; }
  .hx .entry-time { grid-column: 2; width: auto; padding: 0; }
  .entry-go { display: none; }
}
@media print {
  .hx-print-title { display: block; margin: 0 0 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; }
  .hl::before, .entry-go { display: none; }
}
</style>
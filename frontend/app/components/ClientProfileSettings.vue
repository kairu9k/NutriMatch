<template>
  <!-- Same layout as the RND Profile Settings (RNDProfileSettings.vue): page
       header, tab list on the left, one panel on the right. -->
  <div class="profile-page">
    <!-- COVER + WHO YOU ARE (one card) -->
    <section class="ps-hero">
      <div class="ps-cover">
        <img class="ps-cover-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="ps-cover-fade" aria-hidden="true"></span>
        <p class="ps-cover-k"><span aria-hidden="true"></span>MY PROFILE</p>
      </div>
      <div class="page-header ps-id">
        <div class="ps-id-row">
          <div class="ps-avatar-wrap">
            <!-- the app's own photo uploader, kept out of sight; the camera button opens its file picker -->
            <div ref="photoHost" class="ps-photo-host" aria-hidden="true">
              <ProfileIdentityHeader :name="displayName" :subtitle="identitySubtitle" :editable="true" @photo-changed="fireToast" />
            </div>
            <img v-if="auth.user?.profile_photo" :src="auth.user.profile_photo" class="ps-avatar" alt="" />
            <span v-else class="ps-avatar">{{ initials }}</span>
            <button type="button" class="ps-cam" aria-label="Change photo" @click="pickPhoto"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg></button>
          </div>
          <div class="ps-id-main">
            <h2 class="ps-name">{{ displayName }}</h2>
            <p class="page-sub">Manage your personal details, health profile, and account preferences.</p>
            <div class="ps-chips">
              <span class="ps-chip role"><User :size="14" /> Patient</span>
              <span v-if="auth.user?.email" class="ps-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg>{{ auth.user.email }}</span>
              <span v-if="memberSince" class="ps-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>Member since {{ memberSince }}</span>
            </div>
          </div>
        </div>
        <div v-if="profileLoaded" class="ps-facts">
          <div class="ps-fact"><span class="ps-fact-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-8a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8" /><path d="M4 16s1.5-2 4-2 4 2 4 2 1.5-2 4-2 4 2 4 2M2 21h20M7 8v3M12 8v3M17 8v3" /></svg></span><div><strong>{{ ageYears ?? '—' }}</strong><small>Years old</small></div></div>
          <div class="ps-fact"><span class="ps-fact-ico" style="background: #FBF3D2; color: #9A7300"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="9" r="5" /><path d="M12 14v7M9 18h6" /></svg></span><div><strong>{{ sexLabel || '—' }}</strong><small>Sex</small></div></div>
          <div class="ps-fact"><span class="ps-fact-ico" style="background: #EEF1FA; color: #3B5BA5"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z" /></svg></span><div><strong>{{ languageLabel || '—' }}</strong><small>Language</small></div></div>
          <div class="ps-fact"><span class="ps-fact-ico" style="background: #FDECEC; color: #B4384A"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg></span><div><strong>{{ conditionLabel || 'None' }}</strong><small>Primary condition</small></div></div>
        </div>
      </div>
    </section>

    <p v-if="loadError" class="form-error">{{ loadError }}</p>

    <div class="profile-layout">
      <!-- TABS -->
      <div ref="tabCard" class="tab-card">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          type="button"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" :size="17" />
          {{ tab.label }}
        </button>
      </div>

      <!-- PANEL -->
      <div class="panel-card" :class="{ bare: activeTab === 'personal' && !isEditing }">
        <!-- ============ PERSONAL INFO ============ -->
        <!-- Read-only until "Edit profile"; Cancel / Save changes sit at the bottom while editing. -->
        <template v-if="activeTab === 'personal'">

          <!-- READ-ONLY VIEW -->
          <div v-if="!isEditing" class="ps-cards">
          <section class="ps-card">
            <header class="ps-card-head"><span class="ps-card-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg></span><div><h3>Basic details</h3><p>How your RND knows and addresses you.</p></div><button class="ps-card-edit" type="button" :disabled="!profileLoaded" @click="editCategory('basic')"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg>Edit</button></header>
            <dl class="info-grid">
              <div class="info-item ps-f"><span class="ps-f-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg></span><div><dt>First name</dt><dd>{{ form.firstName || '—' }}</dd></div></div>
              <div class="info-item ps-f"><span class="ps-f-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg></span><div><dt>Last name</dt><dd>{{ form.lastName || '—' }}</dd></div></div>
              <div class="info-item ps-f"><span class="ps-f-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-8a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8" /><path d="M4 16s1.5-2 4-2 4 2 4 2 1.5-2 4-2 4 2 4 2M2 21h20M7 8v3M12 8v3M17 8v3" /></svg></span><div><dt>Date of birth</dt><dd :class="{ muted: !form.dateOfBirth }">{{ dobLabel || 'Not provided' }}</dd></div></div>
              <div class="info-item ps-f"><span class="ps-f-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="9" r="5" /><path d="M12 14v7M9 18h6" /></svg></span><div><dt>Sex</dt><dd :class="{ muted: !form.sex }">{{ sexLabel || 'Not provided' }}</dd></div></div>
              <div class="info-item ps-f"><span class="ps-f-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z" /></svg></span><div><dt>Preferred language</dt><dd :class="{ muted: !form.languageCode }">{{ languageLabel || 'Not provided' }}</dd></div></div>
              <div class="info-item ps-f"><span class="ps-f-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2v6M9 5h6" /><path d="M5 22V12l7-4 7 4v10" /><path d="M10 22v-4a2 2 0 0 1 4 0v4" /></svg></span><div><dt>Religion</dt><dd :class="{ muted: !background.religion }">{{ background.religion || 'Not provided' }}</dd></div></div>
            </dl>
          </section>
          <section class="ps-card">
            <header class="ps-card-head"><span class="ps-card-ico" style="background: #EEF1FA; color: #3B5BA5"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg></span><div><h3>Contact</h3><p>Where we send booking updates and receipts.</p></div><button class="ps-card-edit" type="button" :disabled="!profileLoaded" @click="editCategory('contact')"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg>Edit</button></header>
            <dl class="info-grid">
              <div class="info-item ps-f"><span class="ps-f-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg></span><div><dt>Email address</dt><dd>{{ auth.user?.email || '—' }}</dd></div></div>
              <div class="info-item ps-f"><span class="ps-f-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="3" /><path d="M11 18h2" /></svg></span><div><dt>Mobile number</dt><dd :class="{ muted: !form.phone }">{{ formatPhone(form.phone) || 'Not provided' }}</dd></div></div>
            </dl>
          </section>
          <section class="ps-card">
            <header class="ps-card-head"><span class="ps-card-ico" style="background: #FDECEC; color: #B4384A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" /></svg></span><div><h3>Health at a glance</h3><p>Your RND sees this before every consultation.</p></div><button class="ps-card-edit" type="button" :disabled="!profileLoaded" @click="editCategory('health')"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg>Edit</button></header>
            <div class="ps-hgrid">
              <div class="ps-h t-green">
                <p class="ps-h-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg>Primary health condition</p>
                <div class="ps-tags"><span v-if="conditionLabel" class="ps-tag green">{{ conditionLabel }}</span><span v-else class="ps-tag none">None / not sure</span></div>
              </div>
              <div class="ps-h t-red">
                <p class="ps-h-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>Food allergies <em v-if="background.allergiesList.length">Avoid</em></p>
                <div class="ps-tags">
                  <span v-for="a in background.allergiesList" :key="a" class="ps-tag red">{{ a }}</span>
                  <span v-if="!background.allergiesList.length" class="ps-tag none">{{ background.allergiesAnswered ? 'None' : 'Not answered yet' }}</span>
                </div>
              </div>
              <div class="ps-h t-gold">
                <p class="ps-h-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 20A7 7 0 0 1 4 13c0-6 7-9 16-9 0 9-3 16-9 16z" /><path d="M4 20c4-4 7-6 11-8" /></svg>Dietary restrictions</p>
                <div class="ps-tags">
                  <span v-for="d in background.dietList" :key="d" class="ps-tag gold">{{ d }}</span>
                  <span v-if="!background.dietList.length" class="ps-tag none">None</span>
                </div>
              </div>
            </div>
            <p class="ps-lock"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg>Only you and your RND can see your health details.</p>
          </section>
          </div>

          <!-- EDIT FORM -->
          <template v-else>
            <div class="ef-title">
              <span class="ef-title-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg></span>
              <div>
                <h3 class="tab-panel-title">Edit {{ EDIT_TITLES[editSection] }}</h3>
                <p class="tab-panel-sub">Changes are saved to your profile and shared with your RND.</p>
              </div>
            </div>
            <section v-show="editSection === 'basic' || fieldErrors.firstName || fieldErrors.lastName || fieldErrors.dateOfBirth" class="ef-sec">
              <header class="ef-head"><span class="ps-card-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg></span><div><h3>Basic details</h3><p>How your RND knows and addresses you.</p></div></header>
              <div class="form-grid">
              <div class="field">
                <label class="field-label" for="pi-first">First name</label>
                <input id="pi-first" v-model="form.firstName" type="text" class="field-input" :class="{ invalid: fieldErrors.firstName }" maxlength="150" />
                <p v-if="fieldErrors.firstName" class="field-error">{{ fieldErrors.firstName }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-last">Last name</label>
                <input id="pi-last" v-model="form.lastName" type="text" class="field-input" :class="{ invalid: fieldErrors.lastName }" maxlength="150" />
                <p v-if="fieldErrors.lastName" class="field-error">{{ fieldErrors.lastName }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-dob">Date of birth</label>
                <DateField id="pi-dob" v-model="form.dateOfBirth" :max="latestBirthDate" min="1900-01-01" year-select :invalid="!!fieldErrors.dateOfBirth" placeholder="Select date" />
                <p v-if="fieldErrors.dateOfBirth" class="field-error">{{ fieldErrors.dateOfBirth }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-sex">Sex</label>
                <select id="pi-sex" v-model="form.sex" class="nm-select block">
                  <option value="">Prefer not to say</option>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </div>
              <div class="field">
                <label class="field-label" for="pi-lang">Preferred language</label>
                <select id="pi-lang" v-model="form.languageCode" class="nm-select block">
                  <option value="">Select</option>
                  <option v-for="l in languageOptions" :key="l.code" :value="l.code">{{ l.label }}</option>
                </select>
              </div>
              <div class="field">
                <label class="field-label" for="pi-religion">Religion</label>
                <select id="pi-religion" v-model="background.religion" class="nm-select block">
                  <option value="">Prefer not to say</option>
                  <option v-for="r in RELIGION_OPTIONS" :key="r" :value="r">{{ r }}</option>
                </select>
              </div>
              </div>
            </section>
            <section v-show="editSection === 'contact' || fieldErrors.phone" class="ef-sec">
              <header class="ef-head"><span class="ps-card-ico" style="background: #EEF1FA; color: #3B5BA5"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg></span><div><h3>Contact</h3><p>Where we send booking updates and receipts.</p></div></header>
              <div class="form-grid">
              <div class="field">
                <label class="field-label">Email address</label>
                <input :value="auth.user?.email" type="email" class="field-input" disabled />
                <p class="field-hint">Email can't be changed here.</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-phone">Mobile number</label>
                <PhoneInput id="pi-phone" v-model="form.phone" label="mobile number" :error="fieldErrors.phone" />
              </div>
              </div>
            </section>
            <section v-show="editSection === 'health' || fieldErrors.condition" class="ef-sec">
              <header class="ef-head"><span class="ps-card-ico" style="background: #FDECEC; color: #B4384A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" /></svg></span><div><h3>Health</h3><p>Your RND plans your meals around these.</p></div></header>
              <div class="form-grid">
              <div class="field">
                <label class="field-label" for="pi-condition">Primary health condition</label>
                <select id="pi-condition" v-model="conditionChoice" class="nm-select block">
                  <option value="">None / not sure</option>
                  <option v-for="c in CONDITION_OPTIONS" :key="c" :value="c">{{ c }}</option>
                  <option value="__other">Other</option>
                </select>
                <p class="field-hint">Your RND sees this on your patient record.</p>
              </div>
              <div v-if="conditionChoice === '__other'" class="field">
                <label class="field-label" for="pi-condition-other">Please specify</label>
                <input id="pi-condition-other" v-model="conditionOther" type="text" maxlength="100" class="field-input" :class="{ invalid: fieldErrors.condition }" placeholder="e.g. High cholesterol" />
                <p v-if="fieldErrors.condition" class="field-error">{{ fieldErrors.condition }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-allergies">Food allergies</label>
                <input id="pi-allergies" v-model="background.allergiesText" type="text" maxlength="300" class="field-input" placeholder="e.g. Shrimp, peanuts. Leave empty if none" />
                <p class="field-hint">Separate with commas. Your RND plans your meals around these.</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-diet">Dietary restrictions</label>
                <input id="pi-diet" v-model="background.dietText" type="text" maxlength="300" class="field-input" placeholder="e.g. Halal, Low sodium" />
                <p class="field-hint">Separate with commas.</p>
              </div>
              </div>
            </section>
          </template>

          <div v-if="isEditing" class="edit-foot">
            <p class="edit-foot-note"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01M11 12h1v5h1" /></svg>You're editing {{ EDIT_TITLES[editSection] }}.</p>
            <button class="nm-btn-soft" type="button" :disabled="isSaving" @click="cancelEdit">Cancel</button>
            <button class="nm-btn-dark" type="button" :disabled="isSaving" @click="saveProfile">
              <Check :size="15" aria-hidden="true" /> {{ isSaving ? 'Saving…' : 'Save changes' }}
            </button>
          </div>
        </template>

        <!-- ============ HEALTH PROFILE ============ -->
        <template v-else-if="activeTab === 'health'">
          <div class="tab-panel-header hp-head">
            <span class="ef-title-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" /><path d="M3.5 12h4l2-3 3 6 2-3h6" /></svg></span>
            <div class="hp-head-text">
              <h3 class="tab-panel-title">Health profile</h3>
              <p class="tab-panel-sub">Your screening on file. Your progress is measured from it.</p>
            </div>
            <button class="nm-btn-soft" type="button" @click="screeningOpen = true"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></svg>View screening</button>
          </div>

          <dl v-if="screening" class="figs">
            <div class="fig" style="--c: #004D3A; --bg: #E3EFE7">
              <div class="fig-top">
                <span class="fig-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="4.5" r="2" /><path d="M8 22l1-8-3-1 2-6h8l2 6-3 1 1 8" /></svg></span>
                <span v-if="screening.bmi_category" class="fig-pill">{{ screening.bmi_category }}</span>
              </div>
              <dd>{{ screening.bmi != null ? Number(screening.bmi).toFixed(1) : '—' }}</dd>
              <dt>Body mass index (BMI)</dt>
            </div>
            <div class="fig" style="--c: #9A7300; --bg: #FBF3D2">
              <div class="fig-top">
                <span class="fig-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2c1 3 4 5 4 9a4 4 0 0 1-8 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 0-8z" /><path d="M8 18a4 4 0 0 0 8 0" /></svg></span>
                <span class="fig-pill">per day</span>
              </div>
              <dd>{{ screening.tdee_kcal ? Math.round(screening.tdee_kcal).toLocaleString() : '—' }} <span class="fig-unit">kcal</span></dd>
              <dt>Energy needs a day (TER)</dt>
            </div>
            <div class="fig" :class="{ risk: (screening.nrs_score ?? 0) >= 3 }" :style="(screening.nrs_score ?? 0) >= 3 ? '--c: #B42318; --bg: #FDECEC' : '--c: #3B5BA5; --bg: #EEF1FA'">
              <div class="fig-top">
                <span class="fig-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3" /><path d="M7 15h10" /></svg></span>
                <span v-if="nrsLabel(screening.nrs_risk)" class="fig-pill">{{ nrsLabel(screening.nrs_risk) }}</span>
              </div>
              <dd>{{ screening.nrs_score ?? '—' }} <span class="fig-unit">score</span></dd>
              <dt>Nutrition risk (NRS-2002)</dt>
            </div>
          </dl>
          <div v-else class="hp-empty">
            <span class="hp-empty-ico"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3" /></svg></span>
            <p class="empty-note">No screening on file yet.</p>
          </div>

          <p class="field-hint health-note">
            <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01M11 12h1v5h1" /></svg>
            <span>Your primary health condition is under</span>
            <button class="nm-btn-soft nm-btn-sm" type="button" @click="activeTab = 'personal'">Personal info</button>.
          </p>
        </template>

        <!-- ============ CARE TEAM ============ -->
        <template v-else-if="activeTab === 'care'">
          <div class="tab-panel-header hp-head">
            <span class="ef-title-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3v5a4 4 0 0 0 8 0V3" /><path d="M10 12v2a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="10" r="2" /></svg></span>
            <div class="hp-head-text">
              <h3 class="tab-panel-title">Care team</h3>
              <p class="tab-panel-sub">The RND currently handling your nutrition care.</p>
            </div>
          </div>

          <div v-if="careRnd" class="ct-card">
            <span class="ct-cover" aria-hidden="true"></span>
            <div class="rnd-row">
              <div class="rnd-avatar">{{ careRndInitials }}</div>
              <div class="ct-main">
                <span class="ct-k"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg>Your RND</span>
                <NuxtLink :to="`/rnd-profile-view/${careRnd.user.id}`" class="rnd-name">RND {{ careRnd.user.first_name }} {{ careRnd.user.last_name }}</NuxtLink>
                <p class="rnd-specialty">{{ careRnd.specialization || 'General Practice' }}</p>
                <p v-if="careRnd.review_count" class="rnd-rating">★ {{ Number(careRnd.average_rating).toFixed(1) }} ({{ careRnd.review_count }} review{{ careRnd.review_count === 1 ? '' : 's' }})</p>
              </div>
            </div>
            <div class="ct-actions">
              <NuxtLink :to="`/rnd-profile-view/${careRnd.user.id}`" class="nm-btn-soft"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></svg>View profile</NuxtLink>
              <button class="nm-btn-dark" type="button" @click="navigateTo('/messages')"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>Send a message</button>
            </div>
          </div>

          <!-- Ending care (2026-10-19): one RND at a time, so the client can ask
               to end it; the RND has 3 days to discharge them, then it ends on
               its own (scheduling/discharge_requests.py). -->
          <template v-if="careRnd && careRel">
            <div v-if="careRel.discharge_request" class="dr-pending" role="status">
              <p class="dr-title"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>You asked to end your care</p>
              <p class="dr-text">
                Asked on {{ drDate(careRel.discharge_request.requested_at) }}: {{ careRel.discharge_request.reason_label }}.
                RND {{ careRnd.user.first_name }} can close your care with a final note until
                <strong>{{ drDate(careRel.discharge_request.ends_at) }}</strong>. After that it ends automatically and you can book any RND.
                Your records stay in your account.
              </p>
              <p v-if="drError" class="field-error">{{ drError }}</p>
              <button class="nm-btn-soft" type="button" :disabled="drBusy" @click="withdrawDischarge">{{ drBusy ? 'Saving…' : 'Keep my RND' }}</button>
            </div>
            <div v-else class="setting-row ct-end">
              <span class="row-ico red"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5M21 12H9" /></svg></span>
              <div class="row-main">
                <p class="setting-label">End care with this RND</p>
                <p class="setting-detail">Want to switch RNDs or finished your care? Ask to end it. Your RND gets {{ DR_DAYS }} days to close it, then it ends automatically.</p>
              </div>
              <button class="nm-btn-soft danger" type="button" @click="openDischarge">Request discharge</button>
            </div>
          </template>
          <div v-else class="ct-none">
            <span class="ct-none-ico"><svg class="ic" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c.6-3.6 3.2-6 6.5-6s5.9 2.4 6.5 6" /><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.4c2 .8 3.2 2.8 3.5 5.6" /></svg></span>
            <p class="setting-label">No RND yet</p>
            <p class="setting-detail">You're not connected with an RND yet.</p>
            <button class="nm-btn-dark" type="button" @click="navigateTo('/find-rnd')"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>Find an RND</button>
          </div>
        </template>

        <!-- ============ SECURITY ============ -->
        <template v-else-if="activeTab === 'security'">
          <div class="tab-panel-header hp-head">
            <span class="ef-title-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /></svg></span>
            <div class="hp-head-text">
              <h3 class="tab-panel-title">Security</h3>
              <p class="tab-panel-sub">Keep your account safe.</p>
            </div>
          </div>

          <div class="sec-grid">
          <!-- Change password right here (POST /api/auth/me/password/): current
               password + a new one with the sign-up rules; a confirmation
               email goes out. Sign out lives in the account menu. -->
          <form class="pw-form" novalidate @submit.prevent="changePassword">
            <p class="setting-label"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="7.5" cy="15.5" r="4.5" /><path d="M10.7 12.3L21 2M17 6l3 3M14 9l2 2" /></svg>Change password</p>
            <div class="field">
              <label class="field-label" for="pw-current">Current password</label>
              <input id="pw-current" v-model="pw.current" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pwErrors.current_password }" autocomplete="current-password" />
              <p v-if="pwErrors.current_password" class="field-error">{{ pwErrors.current_password }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="pw-new">New password</label>
              <input id="pw-new" v-model="pw.next" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pwErrors.new_password }" autocomplete="new-password" />
              <p v-if="pwErrors.new_password" class="field-error">{{ pwErrors.new_password }}</p>
              <div class="pw-meter" aria-hidden="true"><span v-for="(r, i) in pwRules" :key="i" :class="{ on: pwRules.filter(x => x.ok).length > i }"></span></div>
              <ul class="pw-rules" aria-label="Password rules">
                <li v-for="r in pwRules" :key="r.label" :class="{ ok: r.ok }"><Check v-if="r.ok" :size="12" /><span v-else class="pw-dot" />{{ r.label }}</li>
              </ul>
            </div>
            <div class="field">
              <label class="field-label" for="pw-confirm">Confirm new password</label>
              <input id="pw-confirm" v-model="pw.confirm" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pw.confirm && pw.confirm !== pw.next }" autocomplete="new-password" />
              <p v-if="pw.confirm && pw.confirm !== pw.next" class="field-error">The passwords don't match.</p>
            </div>
            <label class="pw-show"><input v-model="showPw" type="checkbox" /> Show passwords</label>
            <div class="pw-actions">
              <button type="submit" class="nm-btn-dark" :disabled="savingPw || !canChangePw">{{ savingPw ? 'Changing…' : 'Change password' }}</button>
              <NuxtLink to="/forgot-password" class="pw-forgot">Forgot your current password?</NuxtLink>
            </div>
            <p class="setting-detail">We'll email you to confirm the change.</p>
          </form>
          <aside class="sec-aside">
            <span class="sec-aside-ico"><svg class="ic" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg></span>
            <p class="sec-aside-title">A strong password keeps your health records safe</p>
            <ul class="sec-tips">
              <li><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>Use one you don't use anywhere else.</li>
              <li><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>Mix words, numbers and symbols.</li>
              <li><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>Never share it, even with your RND.</li>
            </ul>
          </aside>
          </div>
        </template>

        <!-- ============ NOTIFICATIONS ============ -->
        <template v-else-if="activeTab === 'notifications'">
          <div class="tab-panel-header hp-head">
            <span class="ef-title-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" /></svg></span>
            <div class="hp-head-text">
              <h3 class="tab-panel-title">Notifications and reminders</h3>
              <p class="tab-panel-sub">NutriMatch reminds you automatically. You always get them in the app. Choose which ones, and whether to get emails too.</p>
            </div>
          </div>

          <p v-if="reminderError" class="form-error">{{ reminderError }}</p>
          <p v-if="!reminderPrefs" class="placeholder-text">Loading…</p>
          <template v-else>
            <div class="nt-sound"><NotificationSoundToggle /></div>
            <p class="nt-group"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" /></svg>Reminders in the app</p>
            <div class="nt-list">
              <div v-for="opt in REMINDER_OPTIONS" :key="opt.key" class="setting-row">
                <span class="row-ico" v-html="REMINDER_ICONS[opt.key] || REMINDER_ICONS.appointments"></span>
                <div class="row-main">
                  <p class="setting-label">{{ opt.label }}</p>
                  <p class="setting-detail">{{ opt.detail }}</p>
                </div>
                <label class="toggle">
                  <input :checked="reminderPrefs[opt.key]" type="checkbox" :disabled="!!prefSaving" @change="savePref(opt.key, $event.target.checked)" />
                  <span class="toggle-track"><span class="toggle-thumb"></span></span>
                </label>
              </div>
            </div>
            <p class="nt-group"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" /></svg>Also send them to</p>
            <div class="nt-list">
              <div class="setting-row">
                <span class="row-ico blue"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg></span>
                <div class="row-main">
                  <p class="setting-label">Also send reminders by email</p>
                  <p class="setting-detail">To {{ auth.user?.email }}. Off by default. In-app notifications are always on.</p>
                </div>
                <label class="toggle">
                  <input :checked="reminderPrefs.email" type="checkbox" :disabled="!!prefSaving" @change="savePref('email', $event.target.checked)" />
                  <span class="toggle-track"><span class="toggle-thumb"></span></span>
                </label>
              </div>
              <div class="setting-row">
                <span class="row-ico gold"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="3" /><path d="M11 18h2" /></svg></span>
                <div class="row-main">
                  <p class="setting-label">Also send reminders by text (SMS)</p>
                  <p v-if="reminderPrefs.sms_number" class="setting-detail">To {{ reminderPrefs.sms_number }}. Only the important ones: booking confirmed, payment due, your consultation starting in 1 hour, and a cancelled consultation. Short texts with no health details.</p>
                  <p v-else-if="auth.user?.phone" class="setting-detail">SMS reminders are only available for Philippine mobile numbers (+63). Yours is {{ formatPhone(auth.user.phone) }}.</p>
                  <p v-else class="setting-detail">Add your mobile number (e.g. 0917 123 4567) in Personal Info first.</p>
                </div>
                <label class="toggle">
                  <input :checked="reminderPrefs.sms" :disabled="!!prefSaving || (!reminderPrefs.sms_number && !reminderPrefs.sms)" type="checkbox" @change="savePref('sms', $event.target.checked)" />
                  <span class="toggle-track"><span class="toggle-thumb"></span></span>
                </label>
              </div>
            </div>

          </template>
        </template>

        <!-- ============ PRIVACY & DATA ============ -->
        <template v-else-if="activeTab === 'privacy'">
          <div class="tab-panel-header hp-head">
            <span class="ef-title-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg></span>
            <div class="hp-head-text">
              <h3 class="tab-panel-title">Privacy and data</h3>
              <p class="tab-panel-sub">How your information is handled.</p>
            </div>
          </div>

          <div class="pv-hero">
            <span class="pv-hero-ico"><svg class="ic" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg></span>
            <div>
              <p class="pv-hero-title">Your health data stays between you and your RND</p>
              <p class="setting-detail">Protected under RA 10173, the Data Privacy Act of 2012.</p>
            </div>
          </div>
          <div class="setting-row">
            <span class="row-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c.6-3.6 3.2-6 6.5-6s5.9 2.4 6.5 6" /><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.4c2 .8 3.2 2.8 3.5 5.6" /></svg></span>
            <div class="row-main">
              <p class="setting-label">Data sharing</p>
              <p class="setting-detail">Your health data is only shared with your assigned RND under RA 10173 (Data Privacy Act of 2012).</p>
            </div>
            <!-- TODO: no data-export endpoint exists yet. -->
            <button class="nm-btn-soft" type="button" disabled title="Coming soon"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12M7 10l5 5 5-5M5 21h14" /></svg>Download my data <span class="soon">Soon</span></button>
          </div>
        </template>

        <!-- ============ HISTORY ============ -->
        <template v-else-if="activeTab === 'history'">
          <div class="tab-panel-header hp-head">
            <span class="ef-title-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 8v4l3 2" /></svg></span>
            <div class="hp-head-text">
              <h3 class="tab-panel-title">Your activity</h3>
              <p class="tab-panel-sub">Every screening, appointment, and meal log on your account.</p>
            </div>
            <button class="nm-btn-soft print-btn" type="button" @click="printHistory"><Printer :size="15" /> Print</button>
          </div>

          <div class="filter-tabs">
            <button v-for="f in historyFilters" :key="f.key" class="filter-tab" :class="{ active: historyFilter === f.key }" type="button" @click="historyFilter = f.key">{{ f.label }}</button>
          </div>

          <p v-if="isLoadingHistory" class="placeholder-text">Loading…</p>
          <div v-else-if="!filteredHistory.length" class="empty-state">
            <ClipboardList :size="26" class="empty-icon" />
            <p>Nothing saved yet.</p>
            <p class="empty-sub">Complete a screening, book an appointment or log a meal, and it shows up here.</p>
          </div>
          <div v-else class="timeline">
          <div v-for="entry in pagedHistory" :key="entry.key" class="entry-row">
            <div class="entry-icon" :class="entry.iconClass"><component :is="entry.icon" :size="17" /></div>
            <div class="entry-info">
              <p class="entry-title">{{ entry.title }}</p>
              <p class="entry-detail">{{ entry.detail }}</p>
            </div>
            <span class="entry-time">{{ formatTimestamp(entry.at) }}</span>
          </div>
          </div>
          <div v-if="!isLoadingHistory && historyPages > 1" class="pager">
            <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="historyPage === 1" @click="historyPage--">Previous</button>
            <span class="pager-num">Page {{ historyPage }} of {{ historyPages }}</span>
            <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="historyPage === historyPages" @click="historyPage++">Next</button>
          </div>
        </template>
      </div>
    </div>

    <ScreeningModal v-if="screeningOpen" @close="screeningOpen = false" />

    <div v-if="drOpen" class="nm-modal-overlay" @click.self="drOpen = false" @keydown.esc="drOpen = false">
      <div class="nm-modal dr-modal" role="dialog" aria-modal="true" aria-labelledby="dr-heading">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="drOpen = false"><X :size="18" aria-hidden="true" /></button>
        <h3 id="dr-heading" class="nm-modal-title">Request discharge</h3>
        <p class="dr-text">
          You're asking to end your care with <strong>RND {{ careRnd?.user.first_name }} {{ careRnd?.user.last_name }}</strong>.
          They'll be told right away and have <strong>{{ DR_DAYS }} days</strong> to close your care with a final note.
          If they don't, it ends automatically on <strong>{{ drDate(drEndsPreview) }}</strong>.
        </p>
        <ul class="dr-points">
          <li>Your consultations, meal plans and progress stay in your account (read-only).</li>
          <li>Your meal plan and RND reminders stop when your care ends.</li>
          <li>You can then book any RND, including RND {{ careRnd?.user.first_name }} again.</li>
        </ul>
        <div class="field">
          <label class="field-label" for="dr-reason">Why are you ending care?</label>
          <select id="dr-reason" v-model="dr.reason" class="nm-select block" :class="{ invalid: drFieldErrors.reason }">
            <option value="" disabled>Choose a reason</option>
            <option v-for="r in DR_REASONS" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
          <p v-if="drFieldErrors.reason" class="field-error">{{ drFieldErrors.reason }}</p>
        </div>
        <div class="field">
          <label class="field-label" for="dr-note">Anything to add? <span class="optional-tag">{{ dr.reason === 'other' ? 'Required' : 'Optional' }}</span></label>
          <textarea id="dr-note" v-model="dr.note" class="field-input" rows="3" maxlength="500" data-allow-emoji
            :class="{ invalid: drFieldErrors.note }" placeholder="Your RND will see this." />
          <p v-if="drFieldErrors.note" class="field-error">{{ drFieldErrors.note }}</p>
        </div>
        <p v-if="drError" class="field-error">{{ drError }}
          <NuxtLink v-if="/upcoming consultation/i.test(drError)" to="/appointments" class="nm-btn-soft nm-btn-sm dr-link">Open My Appointments</NuxtLink>
        </p>
        <div class="nm-modal-actions">
          <button class="nm-btn-soft" type="button" :disabled="drBusy" @click="drOpen = false">Keep my RND</button>
          <button class="nm-btn-dark" type="button" :disabled="drBusy || !dr.reason || (dr.reason === 'other' && !dr.note.trim())" @click="requestDischarge">
            {{ drBusy ? 'Sending…' : 'Request discharge' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { Bell, CalendarCheck, Check, ClipboardList, FileText, HeartPulse, History as HistoryIcon, Pencil, Printer, Shield, ShieldCheck, Stethoscope, User, UtensilsCrossed, X } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'
import { formatPhone, phoneError } from '~/utils/phone'
import { fieldsProblemText, focusFirstError } from '~/utils/focusFirstError'
import { apiErrorText, useToast } from '~/composables/useToast'

const auth = useAuthStore()
const { get, patch, post, put, del } = useApi()

const tabs = [
  { key: 'personal', label: 'Personal info', icon: User },
  { key: 'health', label: 'Health profile', icon: HeartPulse },
  { key: 'care', label: 'Care team', icon: Stethoscope },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'notifications', label: 'Notifications', icon: Bell },
  { key: 'privacy', label: 'Privacy and data', icon: FileText },
  { key: 'history', label: 'History', icon: HistoryIcon },
]
// ?tab=health etc. opens a tab directly, like the RND settings page.
const route = useRoute()
const screeningOpen = ref(false) // View Screening pop-up
const activeTab = ref(tabs.some(t => t.key === route.query.tab) ? route.query.tab : 'personal')

const languageOptions = [
  { code: 'tl', label: 'Filipino (Tagalog)' },
  { code: 'ceb', label: 'Bisaya (Cebuano)' },
  { code: 'ilo', label: 'Ilocano' },
  { code: 'en', label: 'English' },
]

const loadError = ref('')
const displayName = computed(() => `${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim())
const initials = computed(() => `${auth.user?.first_name?.[0] || ''}${auth.user?.last_name?.[0] || ''}`.toUpperCase())
const identitySubtitle = computed(() =>
  [auth.user?.email, memberSince.value && `Member since ${memberSince.value}`].filter(Boolean).join(', ')
)
const memberSince = computed(() =>
  auth.user?.created_at ? new Date(auth.user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : ''
)

/* ---------- Personal info (read-only until Edit Profile) ---------- */
const form = reactive({ firstName: '', lastName: '', phone: '', dateOfBirth: '', sex: '', languageCode: '' })
const isSaving = ref(false)
const isEditing = ref(false)
const profileLoaded = ref(false)
// Last profile from the API — Cancel restores the form from it.
const lastProfile = ref(null)
const fieldErrors = reactive({ firstName: '', lastName: '', phone: '', dateOfBirth: '', condition: '' })

// Same rules the API enforces (accounts/validators.py): clients are 18+.
const MIN_CLIENT_AGE = 18
const latestBirthDate = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - MIN_CLIENT_AGE)
  return d.toISOString().slice(0, 10)
})
const NAME_RE = /^[A-Za-zÀ-ÖØ-öø-ÿÑñ]+(?:[ '.-][A-Za-zÀ-ÖØ-öø-ÿÑñ]+)*\.?$/

const sexLabel = computed(() => ({ female: 'Female', male: 'Male' }[form.sex] || ''))
const languageLabel = computed(() => languageOptions.find(l => l.code === form.languageCode)?.label || '')
const dobLabel = computed(() => {
  if (!form.dateOfBirth) return ''
  const d = new Date(`${form.dateOfBirth}T00:00:00`)
  const now = new Date()
  let age = now.getFullYear() - d.getFullYear()
  if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) age--
  return `${d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })} (${age} years old)`
})
const conditionLabel = computed(() =>
  conditionChoice.value === '__other' ? conditionOther.value.trim() : conditionChoice.value
)

function clearFieldErrors() {
  Object.keys(fieldErrors).forEach(k => { fieldErrors[k] = '' })
}
function startEdit() {
  clearFieldErrors()
  isEditing.value = true
}
function cancelEdit() {
  if (lastProfile.value) {
    fillForm(lastProfile.value)
    fillCondition(lastProfile.value)
  }
  clearFieldErrors()
  isEditing.value = false
}

function fillForm(profile) {
  form.firstName = profile.user.first_name || ''
  form.lastName = profile.user.last_name || ''
  form.phone = profile.user.phone || ''
  form.dateOfBirth = profile.date_of_birth || ''
  form.sex = profile.sex || ''
  form.languageCode = profile.language_code || ''
}

function validatePersonal() {
  clearFieldErrors()
  form.firstName = form.firstName.trim()
  form.lastName = form.lastName.trim()
  if (!form.firstName) fieldErrors.firstName = 'Enter your first name.'
  else if (!NAME_RE.test(form.firstName)) fieldErrors.firstName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  if (!form.lastName) fieldErrors.lastName = 'Enter your last name.'
  else if (!NAME_RE.test(form.lastName)) fieldErrors.lastName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  fieldErrors.phone = phoneError(form.phone)
  if (!form.dateOfBirth) fieldErrors.dateOfBirth = 'Enter your date of birth.'
  else if (form.dateOfBirth > latestBirthDate.value) fieldErrors.dateOfBirth = `You must be at least ${MIN_CLIENT_AGE} years old.`
  else if (form.dateOfBirth < '1900-01-01') fieldErrors.dateOfBirth = 'Enter a valid date of birth.'
  if (conditionChoice.value === '__other' && !conditionOther.value.trim()) fieldErrors.condition = 'Please type your condition, or pick one from the list.'
  return !Object.values(fieldErrors).some(Boolean)
}

// One Save for everything on the tab, including the primary condition.
async function saveProfile() {
  if (!validatePersonal()) {
    toast.problem(fieldsProblemText(await focusFirstError()), { id: 'profile' })
    return
  }
  isSaving.value = true
  const primary = conditionChoice.value === '__other' ? conditionOther.value.trim() : conditionChoice.value
  try {
    const [, profile] = await Promise.all([
      patch('/auth/me/', { first_name: form.firstName, last_name: form.lastName, phone: form.phone || null }),
      patch('/client/profile/', {
        date_of_birth: form.dateOfBirth || null,
        sex: form.sex || null,
        language_code: form.languageCode || null,
        medical_conditions: primary ? [primary, ...otherConditions.value] : otherConditions.value,
        // Health background (also asked during onboarding). An empty allergy
        // list means "no food allergies".
        allergies: splitList(background.allergiesText),
        dietary_restrictions: splitList(background.dietText),
        religion: background.religion,
      }),
    ])
    await auth.fetchMe()
    loadReminders() // the SMS setting shows the (new) number
    // The API capitalizes names; show exactly what was saved.
    const saved = await get('/client/profile/').catch(() => profile)
    lastProfile.value = saved
    fillForm(saved)
    fillCondition(saved)
    isEditing.value = false
    fireToast()
  } catch (error) {
    const data = error?.data || {}
    const first = (v) => (Array.isArray(v) ? v[0] : v) || ''
    fieldErrors.firstName = first(data.first_name)
    fieldErrors.lastName = first(data.last_name)
    fieldErrors.phone = first(data.phone)
    fieldErrors.dateOfBirth = first(data.date_of_birth)
    const shown = fieldErrors.firstName || fieldErrors.lastName || fieldErrors.phone || fieldErrors.dateOfBirth
    if (shown) toast.problem(fieldsProblemText(await focusFirstError()), { id: 'profile' })
    else toast.error(apiErrorText(error, 'Could not save your changes. Please try again.'), { id: 'profile' })
  } finally {
    isSaving.value = false
  }
}

// Results go to the app's toast (2026-11-03), seen wherever the page is scrolled.
const toast = useToast()
function fireToast(message = 'Profile updated.') {
  toast.success(message, { id: 'profile' })
}

/* ---------- Health profile ---------- */
const screening = ref(null)

// Same choices as the sign-up form's "Primary Health Concern".
// same spelling as sign-up (RegisterFlow.vue); matched ignoring case so older
// "Renal Nutrition"-style values still land on their option
const CONDITION_OPTIONS = ['Hypertension', 'Type 2 Diabetes', 'Obesity management', 'Renal nutrition']
const conditionOption = v => CONDITION_OPTIONS.find(c => c.toLowerCase() === String(v || '').trim().toLowerCase())
const conditionChoice = ref('')
const conditionOther = ref('')
// medical_conditions[0] is the primary condition; anything after it is kept.
const otherConditions = ref([])

/* ---------- Health background (allergies / diet / religion) ---------- */
const RELIGION_OPTIONS = ['Roman Catholic', 'Christian', 'Islam', 'Iglesia ni Cristo', 'Seventh-day Adventist', 'Other']
const background = reactive({ allergiesAnswered: false, allergiesList: [], dietList: [], religion: '', allergiesText: '', dietText: '' })
function splitList(text) {
  const seen = new Set()
  return text.split(',').map(x => x.trim()).filter(x => x && !seen.has(x.toLowerCase()) && seen.add(x.toLowerCase()))
}
function fillBackground(profile) {
  const hp = profile.health_profile || {}
  background.allergiesAnswered = Array.isArray(hp.allergies)
  background.allergiesList = [...(hp.allergies || [])]
  background.dietList = [...(hp.dietary_restrictions || [])]
  background.religion = hp.religion || ''
  background.allergiesText = background.allergiesList.join(', ')
  background.dietText = background.dietList.join(', ')
}

function fillCondition(profile) {
  fillBackground(profile)
  const conditions = profile.health_profile?.medical_conditions || []
  const primary = conditions[0] || ''
  otherConditions.value = conditions.slice(1)
  conditionOther.value = ''
  if (!primary) {
    conditionChoice.value = ''
  } else if (conditionOption(primary)) {
    conditionChoice.value = conditionOption(primary)
  } else {
    conditionChoice.value = '__other'
    conditionOther.value = primary
  }
}

function nrsLabel(risk) {
  return { no_risk: 'no risk', at_risk: 'at risk', high_risk: 'high risk' }[risk] || ''
}

// TODO: mock/local only — no notification-preference field on User/ClientProfile.
/* ---------- NOTIFICATIONS & REMINDERS ---------- */
const REMINDER_OPTIONS = [
  { key: 'appointments', label: 'Consultation reminders', detail: '24 hours and 1 hour before each confirmed consultation.' },
  { key: 'payments', label: 'Payment reminders', detail: "If a consultation is still unpaid the day before. Unpaid ones are cancelled 15 minutes before the start." },
  { key: 'meal_logging', label: 'Meal logging reminders', detail: "At each meal time in your meal plan, if you haven't logged that meal yet." },
  { key: 'rnd_reminders', label: 'Reminders from your RND', detail: 'Medication and habit reminders your RND sets for you.' },
]
const reminderPrefs = ref(null)
const reminderError = ref('')
async function loadReminders() {
  try {
    reminderPrefs.value = await get('/client/reminder-settings/')
  } catch {
    reminderError.value = 'Could not load your reminder settings. Please refresh.'
  }
}
// One switch saves at a time (2026-11-03): fast flips could arrive out of order.
const prefSaving = ref('')
async function savePref(key, value) {
  if (prefSaving.value) return
  prefSaving.value = key
  const before = reminderPrefs.value[key]
  reminderPrefs.value[key] = value
  reminderError.value = ''
  try {
    reminderPrefs.value = await put('/client/reminder-settings/', { [key]: value })
    fireReminderToast(value ? 'Turned on.' : 'Turned off.')
  } catch (error) {
    reminderPrefs.value[key] = before
    toast.error(error?.data?.[key]?.[0] || 'Could not save this setting. Please try again.', { id: 'reminder-pref' })
  } finally {
    prefSaving.value = ''
  }
}
function fireReminderToast(text) {
  fireToast(text)
}
onMounted(loadReminders)

/* ---------- Care team ---------- */
const careRnd = ref(null)
const careRel = ref(null) // the active care relationship (id + any discharge request)

/* ---------- request discharge (Care Team) ---------- */
const DR_DAYS = 3 // scheduling/discharge_requests.py DISCHARGE_REQUEST_DAYS
const DR_REASONS = [
  { value: 'different_rnd', label: 'I want a different RND' },
  { value: 'goal_reached', label: 'I reached my goal' },
  { value: 'moved', label: "I'm moving or no longer available" },
  { value: 'schedule', label: "The schedule doesn't work for me" },
  { value: 'cost', label: 'Cost' },
  { value: 'other', label: 'Other' },
]
const drOpen = ref(false)
const drBusy = ref(false)
const drError = ref('')
const drFieldErrors = reactive({ reason: '', note: '' })
const dr = reactive({ reason: '', note: '' })
const drEndsPreview = computed(() => new Date(Date.now() + DR_DAYS * 86400000).toISOString())
const drDate = (iso) => new Date(iso).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
function openDischarge() {
  Object.assign(dr, { reason: '', note: '' })
  Object.assign(drFieldErrors, { reason: '', note: '' })
  drError.value = ''
  drOpen.value = true
}
async function requestDischarge() {
  drBusy.value = true
  drError.value = ''
  Object.assign(drFieldErrors, { reason: '', note: '' })
  try {
    const res = await post(`/client/relationships/${careRel.value.id}/discharge-request/`, { reason: dr.reason, note: dr.note.trim() })
    careRel.value = { ...careRel.value, discharge_request: res.discharge_request }
    drOpen.value = false
    fireToast(`Request sent. RND ${careRnd.value.user.first_name} has been told.`)
  } catch (e) {
    const d = e?.data || {}
    drFieldErrors.reason = Array.isArray(d.reason) ? d.reason[0] : ''
    drFieldErrors.note = Array.isArray(d.note) ? d.note[0] : ''
    drError.value = d.detail || (drFieldErrors.reason || drFieldErrors.note ? '' : 'Could not send your request. Please try again.')
  } finally {
    drBusy.value = false
  }
}
async function withdrawDischarge() {
  drBusy.value = true
  drError.value = ''
  try {
    await del(`/client/relationships/${careRel.value.id}/discharge-request/`)
    careRel.value = { ...careRel.value, discharge_request: null }
    fireToast(`You're continuing your care with RND ${careRnd.value.user.first_name}.`)
  } catch (e) {
    drError.value = e?.data?.detail || 'Could not cancel your request. Please try again.'
  } finally {
    drBusy.value = false
  }
}
const careRndInitials = computed(() =>
  careRnd.value ? `${careRnd.value.user.first_name?.[0] || ''}${careRnd.value.user.last_name?.[0] || ''}`.toUpperCase() : ''
)

/* ---------- History (real screenings, appointments, meal logs) ---------- */
const historyFilters = [
  { key: 'all', label: 'All' },
  { key: 'screening', label: 'Screenings' },
  { key: 'appointment', label: 'Appointments' },
  { key: 'mealLog', label: 'Meal logs' },
]
const historyFilter = ref('all')
const historyEntries = ref([])
const isLoadingHistory = ref(false)
let historyLoaded = false

const APPT_TYPE = { video: 'Video', chat: 'Chat', in_person: 'In person' }
const APPT_STATUS = { pending: 'Pending', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }
const MEAL_LABELS = { breakfast: 'Breakfast', am_snack: 'AM Snack', lunch: 'Lunch', pm_snack: 'PM Snack', dinner: 'Dinner', bedtime_snack: 'Bedtime Snack' }
const LOG_STATUS = { followed: 'Followed the plan', partially_followed: 'Partly followed', not_followed: 'Did not follow' }

async function loadHistory() {
  isLoadingHistory.value = true
  try {
    const [screenings, appointments, mealLogs, mealPlans] = await Promise.all([
      get('/client/screening/').catch(() => []),
      get('/client/appointments/').catch(() => []),
      get('/client/meal-logs/').catch(() => []),
      get('/client/meal-plans/').catch(() => []),
    ])
    // meal_plan_meal is just an id on MealLog — resolve its meal_time from the plans.
    const mealTimeById = {}
    for (const p of mealPlans) for (const m of p.meals) mealTimeById[m.id] = m.meal_time

    historyEntries.value = [
      ...screenings.map(s => ({
        key: `s${s.id}`, type: 'screening', at: s.created_at, icon: ShieldCheck, iconClass: 'icon-blue',
        title: 'Health screening completed',
        detail: `BMI ${Number(s.bmi).toFixed(1)} (${s.bmi_category}), NRS-2002 ${s.nrs_score ?? '—'}`,
      })),
      ...appointments.map(a => ({
        key: `a${a.id}`, type: 'appointment', at: a.created_at, icon: CalendarCheck, iconClass: 'icon-gold',
        title: `${APPT_TYPE[a.type] || a.type} appointment with RND ${a.relationship.rnd.first_name} ${a.relationship.rnd.last_name}`,
        detail: `${APPT_STATUS[a.status] || a.status}, scheduled ${formatTimestamp(a.scheduled_at)}`,
      })),
      ...mealLogs.map(l => ({
        key: `m${l.id}`, type: 'mealLog', at: l.updated_at, icon: UtensilsCrossed, iconClass: 'icon-green',
        title: `${MEAL_LABELS[mealTimeById[l.meal_plan_meal]] || 'Meal'} logged`,
        detail: `${LOG_STATUS[l.status] || 'Waiting for your RND to rate it'}, ${drDate(`${l.log_date}T00:00:00`)}${l.reason_notes ? `, ${l.reason_notes}` : ''}`,
      })),
    ].sort((x, y) => new Date(y.at) - new Date(x.at))
    historyLoaded = true
  } finally {
    isLoadingHistory.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'history' && !historyLoaded) loadHistory()
}, { immediate: true })

// Phones: the tabs are a sideways-scrolling strip — keep the selected one in
// view (centred), also when the page opens on ?tab=… .
const tabCard = ref(null)
function showActiveTab() {
  nextTick(() => {
    const strip = tabCard.value
    const btn = strip?.querySelector('.tab-item.active')
    if (!strip || !btn || strip.scrollWidth <= strip.clientWidth) return
    // Clamped: Chrome ignores a smooth scroll to a negative position (the first tab).
    const left = Math.min(Math.max(0, btn.offsetLeft - (strip.clientWidth - btn.offsetWidth) / 2), strip.scrollWidth - strip.clientWidth)
    strip.scrollLeft = left
  })
}
watch(activeTab, () => showActiveTab())
onMounted(showActiveTab)

const filteredHistory = computed(() =>
  historyFilter.value === 'all' ? historyEntries.value : historyEntries.value.filter(e => e.type === historyFilter.value)
)
// 20 a page (Print still prints the whole filtered list); a new filter starts at page 1.
const HISTORY_PER_PAGE = 20
const historyPage = ref(1)
const historyPages = computed(() => Math.max(1, Math.ceil(filteredHistory.value.length / HISTORY_PER_PAGE)))
const pagedHistory = computed(() => filteredHistory.value.slice((historyPage.value - 1) * HISTORY_PER_PAGE, historyPage.value * HISTORY_PER_PAGE))
watch(historyFilter, () => { historyPage.value = 1 })

function formatTimestamp(iso) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}
function printHistory() {
  window.print()
}

/* ---------- change password (Security tab; rules mirror PasswordComplexityValidator) ---------- */
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

onMounted(async () => {
  try {
    const [profile, latestScreening, relationships] = await Promise.all([
      get('/client/profile/'),
      get('/client/screening/latest/').catch(() => null),
      get('/client/relationships/').catch(() => []),
    ])
    lastProfile.value = profile
    fillForm(profile)
    fillCondition(profile)
    profileLoaded.value = true
    screening.value = latestScreening
    const active = relationships.find(r => r.status === 'active')
    careRel.value = active || null
    if (active) careRnd.value = await get(`/client/rnds/${active.rnd.id}/`).catch(() => null)
  } catch {
    loadError.value = 'Could not load your profile. Please try again later.'
  }
})
// Care team stays current (a discharge, a new RND) without a reload. Only that
// part refreshes: the profile form is never touched.
async function refreshCare() {
  const relationships = await get('/client/relationships/')
  const active = relationships.find(r => r.status === 'active')
  careRel.value = active || null
  if (active && careRnd.value?.id !== active.rnd.id) careRnd.value = await get(`/client/rnds/${active.rnd.id}/`).catch(() => null)
  if (!active) careRnd.value = null
}
useAutoRefresh(refreshCare)
/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// age for the quick facts under the name
const ageYears = computed(() => {
  if (!form.dateOfBirth) return null
  const d = new Date(`${form.dateOfBirth}T00:00:00`)
  const now = new Date()
  let age = now.getFullYear() - d.getFullYear()
  if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) age--
  return age
})
// one card at a time: the card's Edit button opens only its fields
const editSection = ref('basic')
const EDIT_TITLES = { basic: 'basic details', contact: 'contact', health: 'health details' }
function editCategory(key) {
  editSection.value = key
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
// an icon for each reminder row
const REMINDER_ICONS = {
  appointments: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>',
  payments: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20M6 15h4" /></svg>',
  meal_logging: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" /></svg>',
  rnd_reminders: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v5a4 4 0 0 0 8 0V3" /><path d="M10 12v2a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="10" r="2" /></svg>',
}
</script>

<style scoped>
/* =========================================================
   Profile settings (client): brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.profile-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }

/* ---------- COVER + IDENTITY (one card) ---------- */
.ps-hero { margin-bottom: 22px; border-radius: 24px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 18px 36px -22px rgba(16, 35, 27, 0.35); }
.ps-cover {
  position: relative;
  overflow: hidden;
  height: 110px;
  border-radius: 24px 24px 0 0;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
}
.ps-cover-plate { position: absolute; right: -60px; top: 50%; width: 380px; height: 380px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.55; pointer-events: none; }
.ps-cover-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004D3A 0%, #004D3A 45%, rgba(0, 77, 58, 0.7) 65%, rgba(0, 70, 52, 0.1) 100%); pointer-events: none; }
.ps-cover-k { position: relative; z-index: 1; margin: 0; padding: 22px 30px; display: flex; align-items: center; gap: 10px; font-size: 12.5px; font-weight: 800; letter-spacing: 2.4px; color: #EFBF04; }
.ps-cover-k span { width: 26px; height: 2px; border-radius: 2px; background: #EFBF04; }
.ps-id { padding: 0 30px 18px; }
.ps-id-row { display: flex; align-items: flex-end; gap: 24px; }
.ps-avatar-wrap { position: relative; flex-shrink: 0; margin-top: -70px; }
.ps-avatar { width: 128px; height: 128px; border-radius: 50%; display: flex; align-items: center; justify-content: center; object-fit: cover; background: linear-gradient(135deg, #F5CB1F, #C49102); color: #004D3A; font-family: 'Playfair Display', Georgia, serif; font-size: 42px; font-weight: 700; border: 5px solid #FFFFFF; box-shadow: 0 18px 34px -18px rgba(0, 0, 0, 0.5); }
.ps-cam { position: absolute; right: 2px; bottom: 6px; width: 38px; height: 38px; padding: 0; border-radius: 50%; border: 3px solid #FFFFFF; background: #004D3A; color: #FFFFFF; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background-color .15s; }
.ps-cam:hover:not(:disabled) { background: #0A5C46; }
.ps-cam:disabled { opacity: .6; cursor: default; }
.ps-cam:focus-visible { outline: 3px solid rgba(239, 191, 4, 0.7); outline-offset: 2px; }
.ps-id-main { flex: 1; min-width: 0; padding-top: 12px; }
.ps-name { margin: 0 0 2px; font-family: 'Playfair Display', Georgia, serif; font-size: 28px; font-weight: 700; line-height: 1.1; color: #0E3A2C; overflow-wrap: anywhere; }
.page-sub { margin: 0 0 10px; font-size: 13.5px; color: #6B7D73; }
.ps-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.ps-chip { display: inline-flex; align-items: center; gap: 7px; min-height: 30px; padding: 4px 12px; border-radius: 999px; background: #F3F6F4; color: #3E5046; font-size: 13px; font-weight: 600; overflow-wrap: anywhere; }
.ps-chip .ic,
.ps-chip :deep(svg) { color: #1F7A4D; }
.ps-chip.role { background: #FBF3D2; color: #8A6400; }
.ps-chip.role :deep(svg) { color: #9A7300; }
.ps-facts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #EEF2EF; }
.ps-fact { display: flex; align-items: center; gap: 12px; min-width: 0; }
.ps-fact-ico { flex-shrink: 0; width: 38px; height: 38px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; }
.ps-fact div { display: flex; flex-direction: column; min-width: 0; }
.ps-fact strong { font-size: 15.5px; font-weight: 800; color: #0E3A2C; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ps-fact small { font-size: 12px; color: #6B7D73; }
.ps-photo-host { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; clip: rect(0, 0, 0, 0); }
.ps-cam:hover:not(:disabled) { transform: scale(1.06); }
.ps-cam { transition: background-color .15s, transform .15s; }

.form-error { margin: 0 0 16px; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }
.placeholder-text { font-size: 14px; color: #6B7D73; }

/* ---------- LAYOUT: tabs on top, panel below ---------- */
.profile-layout { display: grid; grid-template-columns: minmax(0, 1fr); gap: 18px; align-items: start; }
.tab-card {
  position: relative;
  top: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  padding: 8px;
  border-radius: 999px;
  overflow-x: auto;
  scrollbar-width: none;
  background: #FFFFFF;
  border: 1px solid #E4EBE6;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3);
}
.tab-card::-webkit-scrollbar { display: none; }
.tab-item { flex-shrink: 0; display: flex; align-items: center; gap: 10px; height: 44px; padding: 0 20px; border: none; border-radius: 999px; background: none; font-family: inherit; font-size: 14.5px; font-weight: 600; color: #3E5046; text-align: left; white-space: nowrap; cursor: pointer; transition: background-color .15s, color .15s; }
.tab-item :deep(svg) { color: #6B7D73; }
.tab-item:hover:not(.active) { background: #F3F6F4; }
.tab-item.active { background: #004D3A; color: #FFFFFF; }
.tab-item.active :deep(svg) { color: #EFBF04; }
.tab-item:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }

.panel-card { min-width: 0; padding: 26px 28px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.panel-card.bare { padding: 0; background: none; border: none; box-shadow: none; }

/* ---------- PERSONAL INFO: cards ---------- */
.ps-cards { display: flex; flex-direction: column; gap: 18px; }
.ps-card { padding: 24px 26px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.ps-card-head { display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.ps-card-head > div { flex: 1; min-width: 0; }
.ps-card-head h3 { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; color: #0E3A2C; }
.ps-card-head p { margin: 4px 0 0; font-size: 13.5px; color: #6B7D73; }
.ps-card-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; }
.ps-card-edit { flex-shrink: 0; display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border-radius: 10px; background: #F1F6F2; border: 1px solid #DCE8E0; color: #004D3A; font-family: inherit; font-size: 13px; font-weight: 700; cursor: pointer; }
.ps-card-edit:hover:not(:disabled) { background: #E3EFE7; }
.ps-card-edit:disabled { opacity: .5; cursor: not-allowed; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 0; }
.info-item { min-width: 0; }
.ps-f { display: flex; align-items: center; gap: 14px; padding: 14px 16px; border-radius: 16px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.ps-f-ico { flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; background: #FFFFFF; color: #1F5C45; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px -6px rgba(16, 35, 27, 0.3); }
.ps-f > div { min-width: 0; }
.info-item dt { margin: 0; font-size: 12.5px; font-weight: 600; color: #6B7D73; }
.info-item dd { margin: 2px 0 0; font-size: 15px; font-weight: 700; color: #0E3A2C; overflow-wrap: anywhere; }
.info-item dd.muted { color: #9AAEA3; font-weight: 500; }
.ps-hgrid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.ps-h { min-width: 0; padding: 16px; border-radius: 16px; }
.ps-h.t-green { background: #F0F7F2; }
.ps-h.t-red { background: #FEF5F4; }
.ps-h.t-gold { background: #FFFAEB; }
.ps-h-k { margin: 0 0 12px; display: flex; align-items: center; gap: 8px; font-size: 12.5px; font-weight: 700; letter-spacing: .3px; color: #4A5A52; }
.t-green .ps-h-k .ic { color: #1F7A4D; }
.t-red .ps-h-k .ic { color: #B42318; }
.t-gold .ps-h-k .ic { color: #9A7300; }
.ps-h-k em { margin-left: auto; padding: 2px 8px; border-radius: 999px; background: #B42318; color: #FFFFFF; font-style: normal; font-size: 10.5px; font-weight: 800; letter-spacing: .6px; text-transform: uppercase; }
.ps-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.ps-tag { display: inline-flex; align-items: center; min-height: 32px; padding: 4px 14px; border-radius: 999px; background: #FFFFFF; font-size: 13.5px; font-weight: 700; box-shadow: 0 2px 6px -3px rgba(16, 35, 27, 0.25); overflow-wrap: anywhere; }
.ps-tag.green { color: #004D3A; }
.ps-tag.red { color: #B42318; }
.ps-tag.gold { color: #8A6400; }
.ps-tag.none { color: #8A9A91; font-weight: 500; box-shadow: none; background: rgba(255, 255, 255, 0.7); }
.ps-lock { margin: 16px 0 0; display: flex; align-items: center; gap: 8px; font-size: 13px; color: #6B7D73; }
.ps-lock .ic { color: #1F7A4D; }

/* ---------- SHARED PANEL HEADER ---------- */
.tab-panel-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 22px; padding-bottom: 18px; border-bottom: 1px solid #EEF2EF; }
.tab-panel-title { margin: 0 0 4px; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #0E3A2C; }
.tab-panel-sub { margin: 0; font-size: 13.5px; line-height: 1.5; color: #6B7D73; }
.empty-note { margin: 0; padding: 30px 0; text-align: center; font-size: 14px; color: #6B7D73; }

/* ---------- FORM ---------- */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 22px; margin-bottom: 8px; }
.field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.field-label { display: block; margin: 0 0 2px; font-size: 13px; font-weight: 700; color: #22362C; }
.field-input { width: 100%; padding: 12px 14px; border: 1.5px solid #DCE5DF; border-radius: 12px; background: #FFFFFF; font-family: inherit; font-size: 14.5px; color: #14261E; transition: border-color .15s, box-shadow .15s; }
.field-input:focus { outline: none; border-color: #004D3A; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.field-input:disabled { background: #F3F6F4; color: #8A9A91; }
.field-input.invalid { border-color: #C0392B; }
.field select { min-height: 48px; border-radius: 12px; font-size: 14.5px; }
.field-hint { margin: 2px 0 0; font-size: 12.5px; color: #8A9A91; }
.field-error { margin: 2px 0 0; font-size: 12.5px; font-weight: 600; color: #C0392B; }
.edit-foot { display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; margin-top: 22px; padding-top: 18px; border-top: 1px solid #EEF2EF; }

/* buttons on this page */
.profile-page .nm-btn-dark,
.profile-page .nm-btn-soft { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 18px; border-radius: 12px; font-family: inherit; font-size: 14px; font-weight: 700; white-space: nowrap; cursor: pointer; text-decoration: none; transition: background-color .15s; }
.profile-page .nm-btn-dark { border: none; background: #004D3A; color: #FFFFFF; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.profile-page .nm-btn-dark:hover:not(:disabled) { background: #0A5C46; }
.profile-page .nm-btn-soft { border: 1px solid #DCE8E0; background: #F1F6F2; color: #004D3A; }
.profile-page .nm-btn-soft:hover:not(:disabled) { background: #E3EFE7; }
.profile-page .nm-btn-dark:disabled,
.profile-page .nm-btn-soft:disabled { opacity: .5; cursor: not-allowed; }
.profile-page .nm-btn-sm { height: 34px; padding: 0 12px; font-size: 13px; }

/* ---------- HEALTH FIGURES ---------- */
.hp-head { align-items: center; }
.hp-head-text { flex: 1; min-width: 0; }
.figs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin: 0; }
.fig { --c: #004D3A; --bg: #E3EFE7; position: relative; overflow: hidden; display: flex; flex-direction: column; min-width: 0; padding: 20px; border-radius: 18px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 12px 26px -20px rgba(16, 35, 27, 0.35); }
.fig::after { content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 4px; background: var(--c); opacity: .85; }
.fig-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 16px; }
.fig-ico { width: 44px; height: 44px; border-radius: 14px; background: var(--bg); color: var(--c); display: inline-flex; align-items: center; justify-content: center; }
.fig-pill { height: 26px; padding: 0 12px; border-radius: 999px; background: var(--bg); color: var(--c); font-size: 12px; font-weight: 800; text-transform: capitalize; display: inline-flex; align-items: center; white-space: nowrap; }
.fig dd { order: 2; margin: 0; display: flex; align-items: baseline; gap: 6px; font-family: 'Playfair Display', Georgia, serif; font-size: 36px; font-weight: 700; line-height: 1; color: #0E3A2C; font-variant-numeric: lining-nums; }
.fig dt { order: 3; margin-top: 8px; font-size: 13.5px; font-weight: 600; color: #4A5A52; }
.fig-unit { font-family: 'DM Sans', Arial, sans-serif; font-size: 13px; font-weight: 600; color: #6B7D73; }
.fig.risk dd { color: #B42318; }
.hp-empty { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 24px 16px; border-radius: 16px; border: 1.5px dashed #CFDDD4; background: #F8FBF9; }
.hp-empty-ico { width: 52px; height: 52px; border-radius: 50%; background: #FFFFFF; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px -14px rgba(0, 77, 58, 0.6); }
.hp-empty .empty-note { padding: 8px 0 0; }
.health-note { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 18px !important; padding: 12px 14px; border-radius: 14px; background: #F7FAF8; border: 1px solid #EDF2EE; font-size: 13.5px !important; color: #4A5A52 !important; }
.health-note .ic { color: #1F7A4D; }

/* ---------- SETTING ROWS (care team, notifications, privacy) ---------- */
.setting-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 0 0 10px; padding: 16px 18px; border-radius: 16px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.setting-label { margin: 0; font-size: 14.5px; font-weight: 700; color: #0E3A2C; }
.setting-detail { margin: 4px 0 0; font-size: 13px; line-height: 1.5; color: #6B7D73; }
.toggle { position: relative; display: inline-block; flex-shrink: 0; cursor: pointer; }
.toggle input { display: none; }
.toggle-track { position: relative; display: block; width: 46px; height: 26px; border-radius: 999px; background: #D5DED8; transition: background .2s; }
.toggle input:checked + .toggle-track { background: #004D3A; }
.toggle input:disabled + .toggle-track { opacity: .5; }
.toggle-thumb { position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%; background: #FFFFFF; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); transition: transform .2s; }
.toggle input:checked + .toggle-track .toggle-thumb { transform: translateX(20px); }

/* ---------- CARE TEAM ---------- */
.rnd-row { display: flex; align-items: center; gap: 14px; min-width: 0; }
.rnd-avatar { flex-shrink: 0; width: 56px; height: 56px; border-radius: 50%; background: #004D3A; color: #EFBF04; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; box-shadow: 0 0 0 4px #FFFFFF, 0 8px 18px -10px rgba(0, 0, 0, 0.4); }
.rnd-name { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: #0E3A2C; text-decoration: none; }
.rnd-name:hover { text-decoration: underline; text-underline-offset: 3px; }
.rnd-specialty { margin: 2px 0 0; font-size: 13.5px; font-weight: 600; color: #1F7A4D; }
.rnd-rating { margin: 2px 0 0; font-size: 13px; font-weight: 700; color: #9A7300; }

/* ---------- HISTORY ---------- */
.filter-tabs { display: inline-flex; flex-wrap: wrap; gap: 4px; margin-bottom: 14px; padding: 5px; border-radius: 999px; background: #FFFFFF; border: 1px solid #E4EBE6; }
.filter-tab { height: 34px; padding: 0 14px; border: none; border-radius: 999px; background: none; font-family: inherit; font-size: 13px; font-weight: 700; color: #3E5046; cursor: pointer; }
.filter-tab.active { background: #004D3A; color: #FFFFFF; }
.entry-row { display: flex; align-items: center; gap: 14px; padding: 14px 4px; border-top: 1px solid #F0F3F1; }
.entry-icon { flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.icon-blue { background: #E3EFE7; color: #004D3A; }
.icon-gold { background: #FBF3D2; color: #9A7300; }
.icon-green { background: #EAF4EE; color: #1F7A4C; }
.entry-info { flex: 1; min-width: 0; }
.entry-title { margin: 0; font-size: 14.5px; font-weight: 700; color: #0E3A2C; }
.entry-detail { margin: 3px 0 0; font-size: 13px; color: #6B7D73; }
.entry-time { padding: 4px 10px; border-radius: 999px; background: #F3F6F4; font-size: 12px; font-weight: 600; color: #4A5A52; white-space: nowrap; }
.empty-state { padding: 36px 20px; text-align: center; font-size: 14px; color: #6B7D73; }
.empty-state p { margin: 0; }
.empty-icon { margin-bottom: 10px; color: #B5C2BA; }
.empty-sub { margin-top: 4px !important; font-size: 13px; }
.pager { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 16px; }
.pager-num { font-size: 13.5px; color: #4A5A52; font-variant-numeric: tabular-nums; }

/* ---------- SECURITY ---------- */
.pw-form { display: flex; flex-direction: column; gap: 16px; max-width: 460px; }
.pw-form > .setting-label { margin: 0; font-size: 16px; }
.pw-rules { list-style: none; margin: 6px 0 0; padding: 12px 14px; border-radius: 12px; background: #F7FAF8; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 12px; }
.pw-rules li { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #8A9A91; }
.pw-rules li.ok { color: #1F7A4C; font-weight: 600; }
.pw-dot { width: 7px; height: 7px; margin: 0 3px; border-radius: 50%; border: 1.5px solid #B0BAB0; }
.pw-show { display: flex; align-items: center; gap: 8px; font-size: 13.5px; color: #3E5046; cursor: pointer; }
.pw-actions { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.pw-forgot { font-size: 13.5px; font-weight: 700; color: #004D3A; text-decoration: underline; text-underline-offset: 3px; }

/* ---------- DISCHARGE ---------- */
.dr-pending { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; margin-top: 12px; padding: 16px 18px; border-radius: 16px; background: #FFFAEB; border: 1px solid #F1DE97; }
.dr-title { margin: 0; font-size: 15px; font-weight: 700; color: #6A5410; }
.dr-text { margin: 0; font-size: 13.5px; line-height: 1.55; color: #4A5A52; }
.dr-modal { max-width: 500px; border-radius: 22px !important; }
.dr-modal > * + * { margin-top: 14px; }
.dr-points { margin: 0; padding: 12px 14px 12px 30px; border-radius: 12px; background: #F7FAF8; font-size: 13.5px; line-height: 1.6; color: #4A5A52; }
.dr-link { margin-left: 6px; }
.optional-tag { margin-left: 4px; font-weight: 500; color: #8A9A91; }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 1100px) {
  .ps-hgrid { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .profile-page { padding-bottom: 96px; }
  .profile-layout { grid-template-columns: 1fr; gap: 14px; }
  .tab-card { position: relative; top: 0; flex-direction: row; overflow-x: auto; padding: 6px; border-radius: 16px; scrollbar-width: none; }
  .tab-card::-webkit-scrollbar { display: none; }
  .tab-item { flex-shrink: 0; height: 40px; padding: 0 12px; font-size: 13.5px; }
}
@media (max-width: 640px) {
  .ps-hero { margin-bottom: 14px; border-radius: 22px; }
  .ps-cover { height: 90px; border-radius: 22px 22px 0 0; }
  .ps-cover-plate { width: 200px; height: 200px; right: -50px; }
  .ps-cover-k { padding: 16px 18px; }
  .ps-id { padding: 0 16px 18px; }
  .ps-id-row { flex-direction: column; align-items: center; gap: 10px; text-align: center; }
  .ps-avatar-wrap { margin-top: -56px; }
  .ps-avatar { width: 104px; height: 104px; font-size: 34px; border-width: 4px; }
  .ps-cam { width: 34px; height: 34px; right: 0; bottom: 2px; }
  .ps-id-main { padding-top: 0; }
  .ps-name { font-size: 24px; }
  .ps-chips { justify-content: center; }
  .ps-facts { grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 16px; padding-top: 16px; }
  .ps-fact { padding: 10px; border-radius: 14px; background: #F7FAF8; }
  .ps-fact-ico { width: 34px; height: 34px; border-radius: 11px; }
  .ps-fact strong { font-size: 14px; }
  .panel-card { padding: 18px 16px; border-radius: 18px; }
  .ps-card { padding: 18px 16px; border-radius: 18px; }
  .ps-card-ico { width: 40px; height: 40px; }
  .ps-card-head h3 { font-size: 19px; }
  .form-grid,
  .info-grid { grid-template-columns: 1fr; gap: 10px; }
  .ps-f { padding: 12px; }
  .figs { grid-template-columns: 1fr; gap: 10px; }
  .fig { padding: 16px; }
  .fig dd { font-size: 30px; }
  .hp-head { flex-direction: row !important; flex-wrap: wrap; align-items: center !important; }
  .hp-head .nm-btn-soft { width: 100%; }
  .edit-foot > * { flex: 1; }
  .tab-panel-header { flex-direction: column; align-items: stretch; }
  .entry-row { flex-wrap: wrap; }
  .entry-time { margin-left: 54px; }
}
@media (max-width: 480px) { .pw-rules { grid-template-columns: 1fr; } }

@media print {
  .ps-hero, .tab-card, .print-btn, .filter-tabs { display: none !important; }
  .profile-layout { grid-template-columns: 1fr; }
  .panel-card { border: none; padding: 0; box-shadow: none; }
}

/* ---------- EDIT FORM (grouped) ---------- */
.ef-title { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; padding-bottom: 18px; border-bottom: 1px solid #EEF2EF; }
.ef-title-ico { flex-shrink: 0; width: 46px; height: 46px; border-radius: 14px; background: #004D3A; color: #EFBF04; display: inline-flex; align-items: center; justify-content: center; }
.ef-title .tab-panel-title { margin: 0 0 2px; }
.ef-sec { margin-bottom: 14px; padding: 20px; border-radius: 18px; background: #F7FAF8; border: 1px solid #EDF2EE; }

.ef-head { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.ef-head .ps-card-ico { width: 40px; height: 40px; border-radius: 12px; }
.ef-head h3 { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: #0E3A2C; }
.ef-head p { margin: 2px 0 0; font-size: 13px; color: #6B7D73; }
.ef-sec .form-grid { align-items: start; gap: 16px 18px; margin: 0; }
.ef-sec .field { gap: 6px; }
.ef-sec .field-input,
.ef-sec .field select,
.ef-sec .field :deep(input),
.ef-sec .field :deep(select) { background-color: #FFFFFF; }
.ef-sec .field-input { height: 48px; }
.ef-sec .field-input:disabled { background: #EEF2EF; }
.edit-foot { position: sticky; bottom: 16px; z-index: 5; align-items: center; margin-top: 18px !important; padding: 12px 12px 12px 18px !important; border: 1px solid #E4EBE6 !important; border-radius: 16px; background: rgba(255, 255, 255, 0.96); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); box-shadow: 0 16px 32px -18px rgba(16, 35, 27, 0.45); }
.edit-foot-note { margin: 0 auto 0 0; display: flex; align-items: center; gap: 8px; font-size: 13.5px; font-weight: 600; color: #4A5A52; }
.edit-foot-note .ic { color: #9A7300; }
@media (max-width: 640px) {
  .ef-sec { padding: 16px 14px; }
  .edit-foot { bottom: 84px; padding: 10px !important; }
  .edit-foot-note { display: none; }
}

/* ---------- TABS: shared row look ---------- */
.setting-row { align-items: center; }
.row-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; background: #E3EFE7; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.row-ico.blue { background: #EEF1FA; color: #3B5BA5; }
.row-ico.gold { background: #FBF3D2; color: #9A7300; }
.row-ico.red { background: #FDECEC; color: #B42318; }
.row-main { flex: 1; min-width: 0; }
.setting-row { background: #FFFFFF; border: 1px solid #E7EDE9; transition: border-color .15s, box-shadow .15s; }
.setting-row:hover { border-color: #D3E1D8; box-shadow: 0 8px 20px -16px rgba(16, 35, 27, 0.4); }
.profile-page .nm-btn-soft.danger { background: #FEF3F2; border-color: #F6CFCB; color: #B42318; }
.profile-page .nm-btn-soft.danger:hover { background: #FAD9D6; }

/* care team */
.ct-card { position: relative; overflow: hidden; display: flex; align-items: center; justify-content: space-between; gap: 18px; flex-wrap: wrap; margin-bottom: 12px; padding: 22px; border-radius: 18px; background: linear-gradient(120deg, #F0F7F2 0%, #FFFFFF 60%); border: 1px solid #DCEBE1; }
.ct-cover { position: absolute; right: -40px; top: -40px; width: 160px; height: 160px; border-radius: 50%; background: radial-gradient(circle, rgba(239, 191, 4, 0.18), rgba(239, 191, 4, 0) 70%); pointer-events: none; }
.ct-card .rnd-row { position: relative; gap: 18px; }
.ct-card .rnd-avatar { width: 72px; height: 72px; font-size: 22px; }
.ct-main { min-width: 0; }
.ct-k { display: inline-flex; align-items: center; gap: 5px; margin-bottom: 4px; padding: 3px 10px; border-radius: 999px; background: #004D3A; color: #EFBF04; font-size: 11.5px; font-weight: 800; letter-spacing: .4px; }
.ct-card .rnd-name { display: block; font-size: 21px; }
.ct-actions { position: relative; display: flex; gap: 10px; flex-wrap: wrap; }
.ct-none { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 30px 20px; border-radius: 18px; border: 1.5px dashed #CFDDD4; background: #F8FBF9; text-align: center; }
.ct-none .setting-detail { margin-bottom: 10px; }
.ct-none-ico { width: 60px; height: 60px; margin-bottom: 6px; border-radius: 50%; background: #FFFFFF; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px -14px rgba(0, 77, 58, 0.6); }
.dr-title { display: flex; align-items: center; gap: 8px; }
.dr-title .ic { color: #9A7300; }

/* security */
.sec-grid { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 24px; align-items: start; }
.pw-form { max-width: none; padding: 22px; border-radius: 18px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.pw-form > .setting-label { display: flex; align-items: center; gap: 10px; }
.pw-form > .setting-label .ic { color: #9A7300; }
.pw-form .field-input { height: 48px; }
.pw-meter { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-top: 6px; }
.pw-meter span { height: 5px; border-radius: 999px; background: #DCE5DF; transition: background-color .2s; }
.pw-meter span.on { background: #1F9D55; }
.pw-rules { background: #FFFFFF; }
.sec-aside { position: sticky; top: 96px; padding: 22px; border-radius: 18px; background: linear-gradient(160deg, #004D3A 0%, #035A45 100%); color: #FFFFFF; }
.sec-aside-ico { width: 56px; height: 56px; margin-bottom: 14px; border-radius: 16px; background: rgba(255, 255, 255, 0.12); color: #EFBF04; display: inline-flex; align-items: center; justify-content: center; }
.sec-aside-title { margin: 0 0 14px; font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; line-height: 1.3; }
.sec-tips { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 10px; }
.sec-tips li { display: flex; align-items: flex-start; gap: 10px; font-size: 13.5px; line-height: 1.45; color: rgba(255, 255, 255, 0.88); }
.sec-tips .ic { margin-top: 2px; color: #EFBF04; }

/* notifications */
.nt-sound { margin-bottom: 18px; padding: 16px 18px; border-radius: 16px; background: linear-gradient(120deg, #F0F7F2 0%, #FFFFFF 70%); border: 1px solid #DCEBE1; }
.nt-group { margin: 6px 0 10px; display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; color: #9A7300; }
.nt-list { margin-bottom: 14px; }
.nt-list .setting-row { margin-bottom: 8px; }

/* privacy */
.pv-hero { display: flex; align-items: center; gap: 16px; margin-bottom: 14px; padding: 20px 22px; border-radius: 18px; background: linear-gradient(120deg, #004D3A 0%, #035A45 100%); color: #FFFFFF; }
.pv-hero-ico { flex-shrink: 0; width: 56px; height: 56px; border-radius: 16px; background: rgba(255, 255, 255, 0.12); color: #EFBF04; display: inline-flex; align-items: center; justify-content: center; }
.pv-hero-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; }
.pv-hero .setting-detail { color: rgba(255, 255, 255, 0.8); }
.soon { margin-left: 4px; padding: 2px 8px; border-radius: 999px; background: #FBF3D2; color: #8A6400; font-size: 11px; font-weight: 800; }

/* history: a timeline */
.timeline { position: relative; padding-left: 4px; }
.timeline::before { content: ''; position: absolute; left: 24px; top: 20px; bottom: 20px; width: 2px; background: #E3EBE6; }
.timeline .entry-row { position: relative; margin-bottom: 10px; padding: 14px 16px 14px 0; border-top: none; }
.timeline .entry-icon { position: relative; z-index: 1; width: 42px; height: 42px; border-radius: 50%; box-shadow: 0 0 0 5px #FFFFFF; }
.timeline .entry-info { padding: 12px 16px; border-radius: 14px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.timeline .entry-time { align-self: flex-start; margin-top: 12px; }

@media (max-width: 1000px) {
  .sec-grid { grid-template-columns: 1fr; }
  .sec-aside { position: static; order: -1; }
}
@media (max-width: 640px) {
  .hp-head { flex-direction: row !important; flex-wrap: wrap; align-items: center !important; }
  .hp-head .print-btn { width: 100%; }
  .setting-row { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; gap: 12px; padding: 14px; }
  .setting-row > .nm-btn-soft,
  .setting-row > .nm-btn-dark { grid-column: 1 / -1; }
  .ct-card { padding: 18px 16px; }
  .ct-card .rnd-avatar { width: 60px; height: 60px; font-size: 19px; }
  .ct-actions { width: 100%; }
  .ct-actions > * { flex: 1; }
  .pw-form { padding: 16px; }
  .pv-hero { padding: 16px; }
  .pv-hero-ico { width: 46px; height: 46px; }
  .timeline::before { left: 20px; }
  .timeline .entry-row { flex-wrap: nowrap; align-items: flex-start; padding-right: 0; }
  .timeline .entry-icon { width: 36px; height: 36px; }
  .timeline .entry-time { display: none; }
}
</style>
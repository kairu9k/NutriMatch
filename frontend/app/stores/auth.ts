import { defineStore } from 'pinia'

export interface NutriMatchUser {
  id: number
  email: string
  first_name: string
  last_name: string
  role: 'client' | 'rnd' | 'admin'
  phone: string | null
  profile_photo: string | null
  is_active: boolean
  created_at: string
}

interface LoginResponse {
  access: string
  refresh: string
  user: NutriMatchUser
}

export interface RndProfile {
  id: number
  prc_license_number: string
  prc_expiry_date: string | null
  specialization: string | null
  language_codes: string[] | null
  bio: string | null
  consultation_fee: string
  available_for_new_clients: boolean
  is_verified: boolean
  verified_at: string | null
}

const STORAGE_KEY = 'nutrimatch_auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as NutriMatchUser | null,
    rndProfile: null as RndProfile | null,
    accessToken: null as string | null,
    refreshToken: null as string | null,
    hydrated: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
  },

  actions: {
    // Runs once on app start (see app.vue) — restores the session from
    // localStorage so a page refresh doesn't log the user out.
    hydrate() {
      if (this.hydrated || import.meta.server) return
      this.hydrated = true
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      try {
        const saved = JSON.parse(raw)
        this.user = saved.user ?? null
        this.rndProfile = saved.rndProfile ?? null
        this.accessToken = saved.accessToken ?? null
        this.refreshToken = saved.refreshToken ?? null
      } catch {
        localStorage.removeItem(STORAGE_KEY)
      }
      if (this.user?.role === 'rnd' && !this.rndProfile) {
        this.fetchRndProfile().catch(() => {})
      }
    },

    persist() {
      if (import.meta.server) return
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          user: this.user,
          rndProfile: this.rndProfile,
          accessToken: this.accessToken,
          refreshToken: this.refreshToken,
        })
      )
    },

    setSession(data: LoginResponse) {
      this.user = data.user
      this.accessToken = data.access
      this.refreshToken = data.refresh
      this.persist()
    },

    async login(email: string, password: string) {
      const { post } = useApi()
      const data = await post<LoginResponse>('/auth/login/', { email, password }, { skipAuth: true })
      this.setSession(data)
      if (data.user.role === 'rnd') {
        await this.fetchRndProfile().catch(() => {})
      }
      return data.user
    },

    async fetchRndProfile() {
      const { get } = useApi()
      this.rndProfile = await get<RndProfile>('/rnd/profile/')
      this.persist()
      return this.rndProfile
    },

    async registerClient(payload: {
      first_name: string
      last_name: string
      email: string
      password: string
      date_of_birth?: string
      sex?: string
      primary_health_concern?: string
    }) {
      const { post } = useApi()
      return await post<NutriMatchUser>('/auth/register/client/', payload, { skipAuth: true })
    },

    async registerRnd(payload: {
      first_name: string
      last_name: string
      email: string
      password: string
      prc_license_number: string
      specialization?: string
    }) {
      const { post } = useApi()
      return await post<NutriMatchUser>('/auth/register/rnd/', payload, { skipAuth: true })
    },

    async fetchMe() {
      const { get } = useApi()
      this.user = await get<NutriMatchUser>('/auth/me/')
      this.persist()
      return this.user
    },

    async refreshAccessToken() {
      if (!this.refreshToken) return false
      try {
        const data = await $fetch<{ access: string }>('/auth/refresh/', {
          baseURL: useRuntimeConfig().public.apiBase,
          method: 'POST',
          body: { refresh: this.refreshToken },
        })
        this.accessToken = data.access
        this.persist()
        return true
      } catch {
        return false
      }
    },

    logout() {
      this.user = null
      this.rndProfile = null
      this.accessToken = null
      this.refreshToken = null
      if (!import.meta.server) localStorage.removeItem(STORAGE_KEY)
    },
  },
})

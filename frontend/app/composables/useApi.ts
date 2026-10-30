import { useAuthStore } from '~/stores/auth'

type ApiOptions = Parameters<typeof $fetch>[1] & { skipAuth?: boolean }

// Thin wrapper around $fetch: injects the Django API base URL and the JWT
// access token, and retries once via /auth/refresh/ on a 401 before giving up.
export function useApi() {
  const config = useRuntimeConfig()
  const { $syncServerClock } = useNuxtApp() as any
  // Every reply carries the server's time (plugins/00.ph-time.client.ts).
  const onResponse = ({ response }: { response: Response }) => {
    if (import.meta.client && $syncServerClock) $syncServerClock(response.headers.get('x-server-time'))
  }

  async function request<T>(path: string, options: ApiOptions = {}): Promise<T> {
    const auth = useAuthStore()
    const { skipAuth, ...fetchOptions } = options

    const headers: Record<string, string> = {
      ...(fetchOptions.headers as Record<string, string> | undefined),
    }
    if (!skipAuth && auth.accessToken) {
      headers.Authorization = `Bearer ${auth.accessToken}`
    }

    try {
      return await $fetch<T>(path, {
        baseURL: config.public.apiBase,
        onResponse,
        ...fetchOptions,
        headers,
      })
    } catch (error: any) {
      if (error?.response?.status === 401 && !skipAuth && auth.refreshToken) {
        const refreshed = await auth.refreshAccessToken()
        if (refreshed) {
          return await $fetch<T>(path, {
            baseURL: config.public.apiBase,
            onResponse,
            ...fetchOptions,
            headers: { ...headers, Authorization: `Bearer ${auth.accessToken}` },
          })
        }
        // The session has really ended (the refresh token expired too): sign
        // out and go to sign-in with a note, instead of leaving the page
        // half-loaded with no user (role-switching pages showed the wrong view).
        const wasAdmin = auth.user?.role === 'admin'
        auth.logout()
        if (import.meta.client && !/\/login$/.test(window.location.pathname)) {
          window.location.assign(wasAdmin ? '/admin/login?expired=1' : '/login?expired=1')
        }
      }
      throw error
    }
  }

  return {
    get: <T>(path: string, options?: ApiOptions) => request<T>(path, { ...options, method: 'GET' }),
    post: <T>(path: string, body?: unknown, options?: ApiOptions) =>
      request<T>(path, { ...options, method: 'POST', body }),
    patch: <T>(path: string, body?: unknown, options?: ApiOptions) =>
      request<T>(path, { ...options, method: 'PATCH', body }),
    put: <T>(path: string, body?: unknown, options?: ApiOptions) =>
      request<T>(path, { ...options, method: 'PUT', body }),
    del: <T>(path: string, options?: ApiOptions) => request<T>(path, { ...options, method: 'DELETE' }),
  }
}

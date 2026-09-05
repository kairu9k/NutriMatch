import { useAuthStore } from '~/stores/auth'

type ApiOptions = Parameters<typeof $fetch>[1] & { skipAuth?: boolean }

// Thin wrapper around $fetch: injects the Django API base URL and the JWT
// access token, and retries once via /auth/refresh/ on a 401 before giving up.
export function useApi() {
  const config = useRuntimeConfig()

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
        ...fetchOptions,
        headers,
      })
    } catch (error: any) {
      if (error?.response?.status === 401 && !skipAuth && auth.refreshToken) {
        const refreshed = await auth.refreshAccessToken()
        if (refreshed) {
          return await $fetch<T>(path, {
            baseURL: config.public.apiBase,
            ...fetchOptions,
            headers: { ...headers, Authorization: `Bearer ${auth.accessToken}` },
          })
        }
        auth.logout()
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
    del: <T>(path: string, options?: ApiOptions) => request<T>(path, { ...options, method: 'DELETE' }),
  }
}

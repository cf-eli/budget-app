import type { CreateClientConfig } from './api/client.gen'

export const createClientConfig: CreateClientConfig = (config) => {
  const baseUrl = process.env.VITE_GATEWAY_URL
  if (!baseUrl) {
    throw new Error('VITE_GATEWAY_URL environment variable is not set')
  }

  return {
    ...config,
    baseUrl,
    throwOnError: true,
  }
}

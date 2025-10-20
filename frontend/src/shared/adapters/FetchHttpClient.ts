import type { HttpClient, RequestConfig } from 'src/shared/ports'

export class FetchHttpClient implements HttpClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private buildUrl(url: string): string {
    return `${this.baseUrl}${url}`
  }

  private async request<T>(
    method: string,
    url: string,
    config?: RequestConfig | undefined,
    data?: unknown,
  ): Promise<T> {
    const headers = config?.headers || {}
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: data ? JSON.stringify(data) : null,
    }

    const response = await fetch(this.buildUrl(url), options)

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`)
    }

    return (await response.json()) as T
  }

  async get<T>(url: string, config?: RequestConfig | undefined): Promise<T> {
    return this.request<T>('GET', url, config)
  }

  async delete<T>(url: string, config?: RequestConfig | undefined): Promise<T> {
    return this.request<T>('DELETE', url, config)
  }

  async post<T, D>(
    url: string,
    data?: D | undefined,
    config?: RequestConfig | undefined,
  ): Promise<T> {
    return this.request<T>('POST', url, config, data)
  }

  async put<T, D>(
    url: string,
    data?: D | undefined,
    config?: RequestConfig | undefined,
  ): Promise<T> {
    return this.request<T>('PUT', url, config, data)
  }
}

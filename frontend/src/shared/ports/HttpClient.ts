export type RequestUrl = string

export interface RequestConfig {
  params?: Record<string, any> // More explicit typing for better support
  headers?: Record<string, string>
}

/* eslint-disable no-unused-vars */
export interface HttpClient {
  get<T>(url: RequestUrl, config?: RequestConfig): Promise<T>
  delete<T>(url: RequestUrl, config?: RequestConfig): Promise<T>
  post<T, D>(url: RequestUrl, data?: D, config?: RequestConfig): Promise<T>
  put<T, D>(url: RequestUrl, data?: D, config?: RequestConfig): Promise<T>
  // patch<T, D>(url: RequestUrl, data?: D, config?: RequestConfig): Promise<T>
}

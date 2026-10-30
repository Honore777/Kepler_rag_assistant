import axios from 'axios'

// Central API client so every page/component uses consistent base URL and auth.
const baseURL = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export const api = axios.create({
  baseURL,
  withCredentials: true,
})

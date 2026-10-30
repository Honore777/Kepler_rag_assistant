/** Shared frontend types aligned with backend response models. */

export type DocumentItem = {
  id: string
  name: string
  active: boolean
  uploaded_at?: string | null
  indexing_state?: string | null
  indexing_message?: string | null
  indexed_at?: string | null
}

export type SourceItem = {
  id: string
  metadata: Record<string, unknown>
  text: string
  score?: number | null
}

export type QueryResponse = {
  answer: string
  sources: SourceItem[]
}

export type LoginResponse = {
  access_token: string
  token_type: string
}

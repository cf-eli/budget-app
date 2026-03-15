export interface LineItem {
  id?: number
  description: string
  amount: number
  quantity?: number | null
  unit_price?: number | null
  category?: string | null
  budget_id?: number | null
  notes?: string | null
}

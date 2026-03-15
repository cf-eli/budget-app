import { ref, watch, onMounted } from 'vue'
import { useBudgetStore } from '../stores/budgetStore'

export interface LineItem {
  description: string
  amount: number
  quantity?: number
  unit_price?: number
  category?: string
  budget_id?: number
  notes?: string
}

function createEmptyItem(): LineItem {
  return {
    description: '',
    amount: 0,
    quantity: 1,
    category: '',
    notes: '',
  }
}

export function useLineItemForm(getItem: () => LineItem | null | undefined) {
  const budgetStore = useBudgetStore()
  const formData = ref<LineItem>(createEmptyItem())
  const autoCalculate = ref(true)

  watch(
    getItem,
    (newItem) => {
      if (newItem) {
        formData.value = { ...newItem }
      }
    },
    { immediate: true },
  )

  // Auto-calculate amount from quantity × unit_price
  watch([() => formData.value.quantity, () => formData.value.unit_price], () => {
    if (autoCalculate.value && formData.value.quantity && formData.value.unit_price) {
      formData.value.amount = formData.value.quantity * formData.value.unit_price
    }
  })

  function resetForm() {
    formData.value = createEmptyItem()
  }

  onMounted(() => {
    budgetStore.fetchBudgets()
  })

  return { formData, budgetStore, resetForm }
}

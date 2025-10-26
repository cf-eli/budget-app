import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiV1BudgetsNamesGetBudgetsNames } from 'src/api'

interface BudgetOption {
  label: string
  value: number | null
}

export const useBudgetStore = defineStore('budget', () => {
  const budgetOptions = ref<BudgetOption[]>([])
  const loading = ref(false)
  const lastFetched = ref<Date | null>(null)
  const fetchPromise = ref<Promise<void> | null>(null)

  async function fetchBudgets(force = false) {
    // If already cached and not forcing refresh, use cache
    if (budgetOptions.value.length > 0 && !force) {
      return
    }

    // If already fetching, wait for that request
    if (fetchPromise.value) {
      await fetchPromise.value
      return
    }

    loading.value = true
    fetchPromise.value = (async () => {
      try {
        const response = await apiV1BudgetsNamesGetBudgetsNames()

        if (response.data) {
          budgetOptions.value = [
            { label: 'None', value: null },
            ...response.data.map((budget) => ({
              label: budget.name,
              value: budget.id,
            })),
          ]
          lastFetched.value = new Date()
        }
      } catch (error) {
        console.error('Error fetching budgets:', error)
        throw error
      } finally {
        loading.value = false
        fetchPromise.value = null
      }
    })()

    await fetchPromise.value
  }

  function clearCache() {
    budgetOptions.value = []
    lastFetched.value = null
  }

  function getBudgetNameById(id: number | null): string | null {
    if (id === null) return null
    const budget = budgetOptions.value.find((option) => option.value === id)
    return budget?.label || null
  }

  return {
    budgetOptions,
    loading,
    lastFetched,
    fetchBudgets,
    clearCache,
    getBudgetNameById,
  }
})

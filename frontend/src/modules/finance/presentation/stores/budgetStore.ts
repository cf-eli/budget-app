import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  apiV1BudgetsNamesGetBudgetsNames,
  apiV1BudgetsCopyFromPreviousCopyBudgetsFromPrevious,
  type CopyBudgetsResponse,
} from 'src/api'

interface BudgetOption {
  label: string
  value: number | null
}

export const useBudgetStore = defineStore('budget', () => {
  const budgetOptions = ref<BudgetOption[]>([])
  const loading = ref(false)
  const lastFetched = ref<Date | null>(null)
  const fetchPromise = ref<Promise<void> | null>(null)
  const currentMonth = ref<number | undefined>(undefined)
  const currentYear = ref<number | undefined>(undefined)

  async function fetchBudgets(force = false, month?: number, year?: number) {
    // If month/year changed, force refresh
    if (month !== currentMonth.value || year !== currentYear.value) {
      force = true
      currentMonth.value = month
      currentYear.value = year
    }

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
        const response = await apiV1BudgetsNamesGetBudgetsNames({
          query: {
            month: currentMonth.value,
            year: currentYear.value,
          },
        })

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

  async function copyFromPreviousMonth(
    targetMonth: number,
    targetYear: number,
    sourceMonth?: number,
    sourceYear?: number,
  ): Promise<CopyBudgetsResponse | null> {
    try {
      loading.value = true
      const response = await apiV1BudgetsCopyFromPreviousCopyBudgetsFromPrevious({
        body: {
          target_month: targetMonth,
          target_year: targetYear,
          source_month: sourceMonth,
          source_year: sourceYear,
        },
      })

      if (response.data) {
        // Clear cache to force refetch of budget names
        clearCache()
        return response.data
      }

      return null
    } catch (error) {
      console.error('Error copying budgets:', error)
      throw error
    } finally {
      loading.value = false
    }
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
    currentMonth,
    currentYear,
    fetchBudgets,
    copyFromPreviousMonth,
    clearCache,
    getBudgetNameById,
  }
})

import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import {
  apiV1BudgetsFundsFundIdCombineCombineFundToMaster,
  apiV1BudgetsNamesGetBudgetsNames,
  type BudgetNameResponse,
} from 'src/api'

interface MergeMasterOptions {
  fundId: number
  currentMasterId: number
  currentMonth: number
  currentYear: number
  onClose: () => void
  onRefresh: () => void
}

export function useMergeMaster(options: MergeMasterOptions) {
  const $q = useQuasar()

  const visible = ref(true)
  const loading = ref(false)
  const searchMonth = ref(options.currentMonth)
  const searchYear = ref(options.currentYear)
  const availableFunds = ref<BudgetNameResponse[]>([])
  const selectedFund = ref<number | null>(null)

  const selectedFundDetails = computed(() => {
    if (!selectedFund.value) return null
    return availableFunds.value.find((f) => f.id === selectedFund.value)
  })

  const formatCurrency = (value: number | null | undefined) =>
    value !== null && value !== undefined
      ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      : 'N/A'

  async function searchFunds() {
    loading.value = true
    try {
      const response = await apiV1BudgetsNamesGetBudgetsNames({
        query: { month: searchMonth.value, year: searchYear.value },
      })

      // Filter out: current fund, non-fund budgets, funds on same master
      availableFunds.value = (response.data || []).filter(
        (budget) =>
          budget.id !== options.fundId &&
          (budget as any).master_id !== null &&
          (budget as any).master_id !== options.currentMasterId,
      )
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to load funds',
        caption: error instanceof Error ? error.message : 'Unknown error',
      })
    } finally {
      loading.value = false
    }
  }

  async function confirmCombine() {
    if (!selectedFund.value) {
      $q.notify({
        type: 'warning',
        message: 'Please select a fund to combine with',
      })
      return
    }

    loading.value = true
    try {
      await apiV1BudgetsFundsFundIdCombineCombineFundToMaster({
        path: { fund_id: options.fundId },
        body: { target_fund_id: selectedFund.value },
      })

      $q.notify({
        type: 'positive',
        message: 'Fund masters combined successfully',
        caption: 'The two fund masters have been combined into one',
        icon: 'merge_type',
      })

      close()
      options.onRefresh()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to combine fund masters',
        caption: error instanceof Error ? error.message : 'Unknown error',
      })
    } finally {
      loading.value = false
    }
  }

  function close() {
    visible.value = false
    options.onClose()
  }

  onMounted(() => {
    searchFunds()
  })

  return {
    visible,
    loading,
    searchMonth,
    searchYear,
    availableFunds,
    selectedFund,
    selectedFundDetails,
    formatCurrency,
    searchFunds,
    confirmCombine,
    close,
  }
}

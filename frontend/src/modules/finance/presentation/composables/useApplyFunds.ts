import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import {
  apiV1BudgetsFundsApplyIncrementsApplyFundIncrementsEndpoint,
  type ApplyFundIncrementsResponse,
} from 'src/api'

export function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) return '$0.00'
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function useApplyFunds(props: { month: number; year: number }, onApplied: () => void) {
  const $q = useQuasar()

  const loading = ref(false)
  const safeMode = ref(false)
  const result = ref<ApplyFundIncrementsResponse | null>(null)
  const showResult = ref(false)

  const wouldGoNegative = computed(() => {
    if (!result.value) return false
    return result.value.would_go_negative
  })

  async function applyFunds() {
    loading.value = true
    try {
      const response = await apiV1BudgetsFundsApplyIncrementsApplyFundIncrementsEndpoint({
        body: {
          month: props.month,
          year: props.year,
          safe_mode: safeMode.value,
        },
      })

      if (!response.data) {
        throw new Error('No data received from server')
      }

      result.value = response.data as ApplyFundIncrementsResponse

      if (
        result.value.applied_funds === undefined ||
        result.value.skipped_funds === undefined ||
        result.value.balance_before === undefined ||
        result.value.balance_after === undefined ||
        result.value.total_applied === undefined ||
        result.value.would_go_negative === undefined
      ) {
        throw new Error('Invalid response structure from server')
      }

      showResult.value = true

      $q.notify({
        type: 'positive',
        message: `Applied ${formatCurrency(result.value.total_applied)} to ${result.value.applied_funds.length} funds`,
        icon: 'savings',
      })

      onApplied()
    } catch (error) {
      console.error('Error applying fund increments:', error)
      $q.notify({
        type: 'negative',
        message: 'Failed to apply fund increments',
        caption: error instanceof Error ? error.message : 'Unknown error',
      })
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    safeMode,
    result,
    showResult,
    wouldGoNegative,
    applyFunds,
  }
}

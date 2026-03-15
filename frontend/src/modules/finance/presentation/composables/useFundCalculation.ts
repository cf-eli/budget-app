import { ref } from 'vue'
import { useQuasar } from 'quasar'
import {
  apiV1BudgetsFundsFundIdCalculateCalculateFund,
  apiV1BudgetsFundsFundIdUnlinkUnlinkFund,
  apiV1BudgetsFundsMastersMasterIdDetailsGetMasterFundDetailsEndpoint,
  type FundCalculationResponse,
  type MasterFundDetailsResponse,
  type FundUnlinkRequest,
} from 'src/api'

export function useFundCalculation(fundId: () => number, onRefresh?: () => void) {
  const $q = useQuasar()

  const loading = ref(false)
  const calculationData = ref<FundCalculationResponse | null>(null)
  const masterFundDetails = ref<MasterFundDetailsResponse | null>(null)
  const showUnlinkDialog = ref(false)
  const showMergeDialog = ref(false)

  const formatCurrency = (value: number | null | undefined) =>
    value !== null && value !== undefined
      ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      : 'N/A'

  async function loadCalculation() {
    loading.value = true
    try {
      const response = await apiV1BudgetsFundsFundIdCalculateCalculateFund({
        path: { fund_id: fundId() },
      })
      calculationData.value = response.data as FundCalculationResponse
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to load fund calculation',
        caption: error instanceof Error ? error.message : 'Unknown error',
      })
    } finally {
      loading.value = false
    }
  }

  async function loadMasterFundDetails() {
    if (!calculationData.value?.master_id) return

    loading.value = true
    try {
      const response = await apiV1BudgetsFundsMastersMasterIdDetailsGetMasterFundDetailsEndpoint({
        path: { master_id: calculationData.value.master_id },
      })
      masterFundDetails.value = response.data as MasterFundDetailsResponse
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to load master fund details',
        caption: error instanceof Error ? error.message : 'Unknown error',
      })
    } finally {
      loading.value = false
    }
  }

  async function unlinkFund(keepAmount: number) {
    loading.value = true
    try {
      const requestBody: FundUnlinkRequest = {
        keep_amount: keepAmount,
      }

      await apiV1BudgetsFundsFundIdUnlinkUnlinkFund({
        path: { fund_id: fundId() },
        body: requestBody,
      })

      $q.notify({
        type: 'positive',
        message: 'Fund unlinked and balance split successfully',
        icon: 'link_off',
      })

      await loadCalculation()
      return true
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to unlink fund',
        caption: error instanceof Error ? error.message : 'Unknown error',
      })
      return false
    } finally {
      loading.value = false
    }
  }

  async function confirmUnlink(keepAmount: number) {
    const success = await unlinkFund(keepAmount)
    if (success) {
      showUnlinkDialog.value = false
      onRefresh?.()
    }
  }

  async function handleMergeRefresh() {
    await loadCalculation()
    await loadMasterFundDetails()
    onRefresh?.()
  }

  return {
    loading,
    calculationData,
    masterFundDetails,
    formatCurrency,
    loadCalculation,
    loadMasterFundDetails,
    showUnlinkDialog,
    showMergeDialog,
    unlinkFund,
    confirmUnlink,
    handleMergeRefresh,
  }
}

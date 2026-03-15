import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import {
  apiV1BudgetsFundsMastersMasterIdAddMonthAddMonthToMasterEndpoint,
  type AddMonthToMasterRequest,
  type OrphanedMasterInfo,
} from 'src/api'

export function useAddMonthToMaster(
  master: () => OrphanedMasterInfo,
  month: () => number,
  year: () => number,
  onSuccess: () => void,
) {
  const $q = useQuasar()
  const loading = ref(false)

  const formData = ref({
    priority: 0,
    increment: 0,
    max: null as number | null,
  })

  const haveMax = ref(false)

  const formatCurrency = (value: number) =>
    `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

  const masterName = computed(() => master().name || `Master #${master().master_id}`)

  async function submitForm() {
    loading.value = true
    try {
      const requestBody: AddMonthToMasterRequest = {
        month: month(),
        year: year(),
        priority: formData.value.priority || 0,
        increment: formData.value.increment,
        max: haveMax.value ? formData.value.max : undefined,
      }

      await apiV1BudgetsFundsMastersMasterIdAddMonthAddMonthToMasterEndpoint({
        path: { master_id: master().master_id },
        body: requestBody,
      })

      $q.notify({
        type: 'positive',
        message: `Fund created successfully for ${masterName.value}`,
        icon: 'check_circle',
        timeout: 3000,
      })

      onSuccess()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to create fund',
        caption: error instanceof Error ? error.message : 'Unknown error',
      })
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    formData,
    haveMax,
    formatCurrency,
    masterName,
    submitForm,
  }
}

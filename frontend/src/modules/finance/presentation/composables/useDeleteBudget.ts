import { ref } from 'vue'
import { useQuasar } from 'quasar'
import { useBudgetStore } from '../stores/budgetStore'

export function useDeleteBudget() {
  const $q = useQuasar()
  const budgetStore = useBudgetStore()

  const deleteClickCount = ref(0)
  const deleteTimeout = ref<ReturnType<typeof setTimeout> | null>(null)

  function handleDelete(budgetId: number, budgetName: string, onSuccess: () => void) {
    return (event: Event) => {
      event.stopPropagation()
      deleteClickCount.value++

      if (deleteTimeout.value) {
        clearTimeout(deleteTimeout.value)
      }

      if (deleteClickCount.value === 1) {
        $q.notify({
          type: 'warning',
          message: 'Click delete again to confirm',
          timeout: 2000,
        })

        deleteTimeout.value = setTimeout(() => {
          deleteClickCount.value = 0
        }, 2000)
      } else if (deleteClickCount.value === 2) {
        deleteClickCount.value = 0
        if (deleteTimeout.value) {
          clearTimeout(deleteTimeout.value)
        }
        confirmDelete(budgetId, budgetName, onSuccess)
      }
    }
  }

  async function confirmDelete(budgetId: number, budgetName: string, onSuccess: () => void) {
    try {
      await budgetStore.deleteBudget(budgetId)

      $q.notify({
        type: 'positive',
        message: `Deleted budget "${budgetName}"`,
        timeout: 2000,
      })

      onSuccess()
    } catch (error) {
      console.error('Error deleting budget:', error)
      $q.notify({
        type: 'negative',
        message: 'Failed to delete budget. Please try again.',
        timeout: 3000,
      })
    }
  }

  return {
    handleDelete,
  }
}

import { ref } from 'vue'
import type { TransactionResponse } from 'src/api'

export function useTransactionDialogs(emit: () => void) {
  const breakdownDialogVisible = ref(false)
  const typeDialogVisible = ref(false)
  const ruleDialogVisible = ref(false)
  const selectedTransaction = ref<TransactionResponse | null>(null)

  function openBreakdown(transaction: TransactionResponse) {
    selectedTransaction.value = transaction
    breakdownDialogVisible.value = true
  }

  function openTypeDialog(transaction: TransactionResponse) {
    selectedTransaction.value = transaction
    typeDialogVisible.value = true
  }

  function openRuleDialog(transaction: TransactionResponse) {
    selectedTransaction.value = transaction
    ruleDialogVisible.value = true
  }

  function onDialogSaved() {
    emit('refresh')
  }

  return {
    breakdownDialogVisible,
    typeDialogVisible,
    ruleDialogVisible,
    selectedTransaction,
    openBreakdown,
    openTypeDialog,
    openRuleDialog,
    onDialogSaved,
  }
}

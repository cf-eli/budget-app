import { ref } from 'vue'
import { useQuasar } from 'quasar'
import type { TransactionResponse, TransactionTypeEnum } from 'src/api'
import { apiV1TransactionsTransactionIdTypeMarkTransactionTypeEndpoint } from 'src/api'
import { useRulesStore } from '../stores/rulesStore'

interface UseTransactionTypeMarkingOptions {
  getTransaction: () => TransactionResponse | null
  onSaved: () => void
  onClose: () => void
}

export function useTransactionTypeMarking(options: UseTransactionTypeMarkingOptions) {
  const $q = useQuasar()
  const rulesStore = useRulesStore()
  const loading = ref(false)
  const excludeFromBudget = ref(true)
  const selectedType = ref<TransactionTypeEnum | null>(null)
  const createRule = ref(false)

  const transactionTypeOptions: {
    label: string
    value: TransactionTypeEnum
    description: string
  }[] = [
    { label: 'Transfer', value: 'transfer', description: 'Money moved between accounts' },
    { label: 'Credit Payment', value: 'credit_payment', description: 'Credit card payment' },
    { label: 'Loan Payment', value: 'loan_payment', description: 'Loan or mortgage payment' },
  ]

  async function saveType() {
    const transaction = options.getTransaction()
    if (!transaction || !selectedType.value) return

    loading.value = true
    try {
      await apiV1TransactionsTransactionIdTypeMarkTransactionTypeEndpoint({
        path: { transaction_id: transaction.id },
        body: {
          transaction_type: selectedType.value,
          exclude_from_budget: excludeFromBudget.value,
        },
      })

      if (createRule.value) {
        await createRuleForTransaction(transaction)
      }

      options.onSaved()
      options.onClose()
    } catch (error) {
      console.error('Error marking transaction type:', error)
      $q.notify({ type: 'negative', message: 'Failed to mark transaction type.' })
    } finally {
      loading.value = false
    }
  }

  async function createRuleForTransaction(txn: TransactionResponse) {
    if (!selectedType.value) return
    const matchField = txn.payee || txn.description || ''
    const typeLabel = selectedType.value.replace('_', ' ')
    await rulesStore.createRule({
      name: `Auto: mark "${matchField}" as ${typeLabel}`,
      conditions: [
        {
          field: txn.payee ? 'payee' : 'description',
          operator: 'exact',
          value: matchField,
          value2: null,
        },
      ],
      target_transaction_type: selectedType.value,
      target_exclude_from_budget: excludeFromBudget.value,
      target_budget_id: null,
      priority: 0,
      is_active: true,
    })
    $q.notify({ type: 'positive', message: 'Rule created for future transactions' })
  }

  function cancel() {
    options.onClose()
    selectedType.value = null
    excludeFromBudget.value = true
    createRule.value = false
  }

  return {
    loading,
    excludeFromBudget,
    selectedType,
    createRule,
    transactionTypeOptions,
    saveType,
    cancel,
  }
}

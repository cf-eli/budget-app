import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import type { TransactionResponse, RuleCondition, RuleFieldEnum, RuleOperatorEnum } from 'src/api'
import { useBudgetStore } from '../stores/budgetStore'
import { useRulesStore } from '../stores/rulesStore'

interface UseRuleCreationOptions {
  getTransaction: () => TransactionResponse | null
  getVisible: () => boolean
  month: () => number
  year: () => number
  onSaved: () => void
  onClose: () => void
}

export function useRuleCreation(options: UseRuleCreationOptions) {
  const $q = useQuasar()
  const budgetStore = useBudgetStore()
  const rulesStore = useRulesStore()

  const ruleName = ref('')
  const targetBudgetId = ref<number | null>(null)
  const targetTransactionType = ref<string | null>(null)
  const targetExcludeFromBudget = ref(false)
  const conditions = ref<RuleCondition[]>([])
  const loading = ref(false)

  const transactionTypeOptions = [
    { label: 'None', value: null },
    { label: 'Transfer', value: 'transfer' },
    { label: 'Credit Card Payment', value: 'credit_payment' },
    { label: 'Loan Payment', value: 'loan_payment' },
  ]

  const canSave = computed(() => {
    const hasName = !!ruleName.value.trim()
    const hasConditions = conditions.value.length > 0
    const hasAction = !!targetBudgetId.value || !!targetTransactionType.value
    return hasName && hasConditions && hasAction
  })

  watch(targetTransactionType, (newType) => {
    if (newType) {
      targetExcludeFromBudget.value = true
    } else {
      targetExcludeFromBudget.value = false
    }
  })

  watch(options.getVisible, async (visible) => {
    if (visible && options.getTransaction()) {
      await budgetStore.fetchBudgets(true, options.month(), options.year())
      initializeFromTransaction()
    }
  })

  function initializeFromTransaction() {
    const transaction = options.getTransaction()
    if (!transaction) return
    ruleName.value = `Rule for ${transaction.payee || transaction.description}`
    targetBudgetId.value = transaction.budget?.id || null
    conditions.value = []
    if (transaction.payee) {
      conditions.value.push({
        field: 'payee' as RuleFieldEnum,
        operator: 'exact' as RuleOperatorEnum,
        value: transaction.payee,
        value2: null,
      })
    }
  }

  function addCondition() {
    conditions.value.push({
      field: 'payee' as RuleFieldEnum,
      operator: 'exact' as RuleOperatorEnum,
      value: '',
      value2: null,
    })
  }

  function updateCondition(index: number, condition: RuleCondition) {
    conditions.value[index] = condition
  }

  function removeCondition(index: number) {
    conditions.value.splice(index, 1)
  }

  function resetForm() {
    ruleName.value = ''
    targetBudgetId.value = null
    targetTransactionType.value = null
    targetExcludeFromBudget.value = false
    conditions.value = []
  }

  async function saveRule() {
    if (!canSave.value) return
    loading.value = true
    try {
      await rulesStore.createRule({
        name: ruleName.value.trim(),
        target_budget_id: targetBudgetId.value,
        conditions: conditions.value,
        priority: 0,
        is_active: true,
        target_transaction_type: targetTransactionType.value,
        target_exclude_from_budget: targetExcludeFromBudget.value,
      })
      $q.notify({ type: 'positive', message: 'Rule created successfully' })
      options.onSaved()
      cancel()
    } catch {
      $q.notify({ type: 'negative', message: 'Failed to create rule' })
    } finally {
      loading.value = false
    }
  }

  function cancel() {
    options.onClose()
    resetForm()
  }

  return {
    ruleName,
    targetBudgetId,
    targetTransactionType,
    targetExcludeFromBudget,
    transactionTypeOptions,
    conditions,
    loading,
    canSave,
    budgetStore,
    addCondition,
    updateCondition,
    removeCondition,
    saveRule,
    cancel,
  }
}

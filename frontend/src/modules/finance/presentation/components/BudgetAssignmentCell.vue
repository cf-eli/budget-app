<script setup lang="ts">
import { ref } from 'vue'
import type { TransactionResponse } from 'src/api'
import { apiV1BudgetsBudgetIdTransactionsTransactionIdAddTransactionToBudget } from 'src/api'
import { useBudgetStore } from '../stores/budgetStore'

interface Props {
  transaction: TransactionResponse
}

interface Emits {
  (_event: 'updated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const budgetStore = useBudgetStore()
const editedBudgetId = ref<number | null>(null)
const originalBudgetId = ref<number | null>(null)

async function assignBudget(transactionId: number, budgetId: number | null) {
  if (budgetId === null) {
    console.log('Unassigning budget from transaction:', transactionId)
    return { success: true }
  }

  try {
    const response = await apiV1BudgetsBudgetIdTransactionsTransactionIdAddTransactionToBudget({
      path: {
        budget_id: budgetId,
        transaction_id: transactionId,
      },
    })

    return { success: !!response.data, data: response.data }
  } catch (error) {
    console.error('Error assigning budget:', error)
    return { success: false, error }
  }
}

function getBudgetLabel(budgetName: string | undefined | null): string {
  if (!budgetName) return 'Unassigned'
  return budgetName
}

function getCurrentBudgetId(): number | null {
  return props.transaction.budget?.id ?? null
}

async function onBeforeShow() {
  originalBudgetId.value = getCurrentBudgetId()
  editedBudgetId.value = getCurrentBudgetId()

  // Get month/year from transaction date
  const transactionDate = new Date(props.transaction.transacted_at)
  const month = transactionDate.getMonth() + 1
  const year = transactionDate.getFullYear()

  // Fetch budgets for the transaction's month/year
  await budgetStore.fetchBudgets(false, month, year)

  console.log('Current budget ID:', editedBudgetId.value)
}

async function onHide() {
  // Only save if the value actually changed
  if (editedBudgetId.value !== originalBudgetId.value) {
    console.log(
      'Assigning transaction',
      props.transaction.id,
      'to budget ID:',
      editedBudgetId.value,
    )
    const result = await assignBudget(props.transaction.id, editedBudgetId.value)

    if (result.success) {
      emit('updated')
    }
  }
}
</script>

<template>
  <q-chip clickable :color="transaction.budget?.name ? 'primary' : 'grey'" text-color="white">
    {{ getBudgetLabel(transaction.budget?.name) }}

    <q-popup-edit
      v-model="editedBudgetId"
      title="Assign Budget"
      buttons
      @before-show="onBeforeShow"
      @hide="onHide"
    >
      <q-select
        v-model="editedBudgetId"
        :options="budgetStore.budgetOptions"
        option-value="value"
        option-label="label"
        emit-value
        map-options
        dense
        clearable
        :loading="budgetStore.loading"
      />
    </q-popup-edit>
  </q-chip>
</template>

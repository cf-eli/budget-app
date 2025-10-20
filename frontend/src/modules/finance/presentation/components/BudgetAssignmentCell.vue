<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { GetTransactionResponse } from 'src/api';
import { apiFinanceV1BudgetsNamesGetBudgetsNames, apiFinanceV1BudgetsBudgetIdTransactionsTransactionIdAddTransactionToBudget } from 'src/api';

interface Props {
  transaction: GetTransactionResponse;
}

interface Emits {
  (e: 'updated'): void;
}

interface BudgetOption {
  label: string;
  value: number | null;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const budgetOptions = ref<BudgetOption[]>([]);
const editedBudgetId = ref<number | null>(null);
const loading = ref(false);
const originalBudgetId = ref<number | null>(null);

async function fetchBudgets() {
  loading.value = true;
  try {
    const response = await apiFinanceV1BudgetsNamesGetBudgetsNames();

    if (response.data) {
      budgetOptions.value = [
        { label: 'None', value: null },
        ...response.data.map((budget) => ({
          label: budget.name,
          value: budget.id,
        }))
      ];
    }
  } catch (error) {
    console.error('Error fetching budgets:', error);
  } finally {
    loading.value = false;
  }
}

async function assignBudget(transactionId: number, budgetId: number | null) {
  if (budgetId === null) {
    console.log('Unassigning budget from transaction:', transactionId);
    return { success: true };
  }

  try {
    const response = await apiFinanceV1BudgetsBudgetIdTransactionsTransactionIdAddTransactionToBudget({
      path: {
        budget_id: budgetId,
        transaction_id: transactionId
      }
    });

    return { success: !!response.data, data: response.data };
  } catch (error) {
    console.error('Error assigning budget:', error);
    return { success: false, error };
  }
}

function getBudgetLabel(budgetName: string | undefined | null): string {
  if (!budgetName) return 'Unassigned';
  return budgetName;
}

function getCurrentBudgetId(): number | null {
  return props.transaction.budget?.id ?? null;
}

function onBeforeShow() {
  originalBudgetId.value = getCurrentBudgetId();
  editedBudgetId.value = getCurrentBudgetId();
  console.log('Current budget ID:', editedBudgetId.value);
}

async function onHide() {
  // Only save if the value actually changed
  if (editedBudgetId.value !== originalBudgetId.value) {
    console.log('Assigning transaction', props.transaction.id, 'to budget ID:', editedBudgetId.value);
    const result = await assignBudget(props.transaction.id, editedBudgetId.value);
   
    if (result.success) {
      emit('updated');
    }
  }
}

onMounted(() => {
  fetchBudgets();
});
</script>

<template>
  <q-chip
    clickable
    :color="transaction.budget?.name ? 'primary' : 'grey'"
    text-color="white"
  >
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
        :options="budgetOptions"
        option-value="value"
        option-label="label"
        emit-value
        map-options
        dense
        clearable
        :loading="loading"
      />
    </q-popup-edit>
  </q-chip>
</template>
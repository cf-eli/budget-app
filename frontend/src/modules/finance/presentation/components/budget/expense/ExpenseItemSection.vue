<script setup lang="ts">
import type { ExpenseBudgetResponse } from 'src/api';

interface Props {
  expense: ExpenseBudgetResponse;
}

defineProps<Props>();

const formatCurrency = (value: number | null | undefined) => 
  value !== null && value !== undefined ? `$${value.toLocaleString()}` : 'N/A';
</script>

<template>
  <q-item-section>
    <q-separator />
    <div class="q-mb-xs text-h6 text-dark">{{ expense.name }}</div>
    <div class="q-mb-xs">
      <strong>Type:</strong> {{ expense.fixed ? 'Fixed' : 'Estimated' }}
    </div>
    <div class="q-mb-xs">
      <strong>Expected:</strong> {{ formatCurrency(expense.expected_amount) }}
    </div>
    <div v-if="!expense.fixed && expense.min !== null" class="q-mb-xs">
      <strong>Min:</strong> {{ formatCurrency(expense.min) }}
    </div>
    <div v-if="!expense.fixed && expense.max !== null" class="q-mb-xs">
      <strong>Max:</strong> {{ formatCurrency(expense.max) }}
    </div>
    
    <q-separator class="q-my-sm" />
    
    <div class="q-mb-xs">
      <strong>Transaction Total:</strong> 
      <span :class="Math.abs(expense.transaction_sum) > 0 ? 'text-negative' : 'text-grey'">
        {{ formatCurrency(Math.abs(expense.transaction_sum)) }}
      </span>
    </div>
    <div class="q-mb-xs">
      <strong>Remaining:</strong> 
      <span :class="expense.amount_after_transactions > 0 ? 'text-positive' : expense.amount_after_transactions < 0 ? 'text-negative' : 'text-grey'">
        {{ formatCurrency(expense.amount_after_transactions) }}
      </span>
    </div>
    
    <div v-if="!expense.enable" class="q-mt-sm">
      <q-badge color="grey">Disabled</q-badge>
    </div>
  </q-item-section>
</template>
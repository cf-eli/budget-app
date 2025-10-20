<script setup lang="ts">
import type { IncomeBudgetResponse } from 'src/api';

interface Props {
  income: IncomeBudgetResponse;
}

defineProps<Props>();

const formatCurrency = (value: number | null | undefined) => 
  value !== null && value !== undefined ? `$${value.toLocaleString()}` : 'N/A';
</script>

<template>
  <q-item-section>
    <div class="q-mb-xs text-h6 text-dark">{{ income.name }}</div>
    <div class="q-mb-xs">
      <strong>Type:</strong> {{ income.fixed ? 'Fixed' : 'Estimated' }}
    </div>
    <div class="q-mb-xs">
      <strong>Expected:</strong> {{ formatCurrency(income.expected_amount) }}
    </div>
    <div v-if="!income.fixed && income.min !== null" class="q-mb-xs">
      <strong>Min:</strong> {{ formatCurrency(income.min) }}
    </div>
    <div v-if="!income.fixed && income.max !== null" class="q-mb-xs">
      <strong>Max:</strong> {{ formatCurrency(income.max) }}
    </div>
    
    <q-separator class="q-my-sm" />
    
    <div class="q-mb-xs">
      <strong>Transaction Total:</strong> 
      <span :class="income.transaction_sum >= 0 ? 'text-positive' : 'text-negative'">
        {{ formatCurrency(income.transaction_sum) }}
      </span>
    </div>
    <div class="q-mb-xs">
      <strong>Remaining:</strong> 
      <span :class="income.amount_after_transactions >= 0 ? 'text-positive' : 'text-negative'">
        {{ formatCurrency(income.amount_after_transactions) }}
      </span>
    </div>
    
    <div v-if="!income.enable" class="q-mt-sm">
      <q-badge color="grey">Disabled</q-badge>
    </div>
  </q-item-section>
</template>
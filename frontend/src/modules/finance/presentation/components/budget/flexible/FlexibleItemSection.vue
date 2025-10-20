<script setup lang="ts">
import type { FlexibleBudgetResponse } from 'src/api';

interface Props {
  flexible: FlexibleBudgetResponse;
}

defineProps<Props>();

const formatCurrency = (value: number | null | undefined) => 
  value !== null && value !== undefined ? `$${value.toLocaleString()}` : 'N/A';
</script>

<template>
  <q-item-section>
    <div class="q-mb-xs text-h6 text-dark">{{ flexible.name }}</div>
    <div class="q-mb-xs">
      <strong>Type:</strong> {{ flexible.fixed ? 'Fixed' : 'Estimated' }}
    </div>
    <div class="q-mb-xs">
      <strong>Expected:</strong> {{ formatCurrency(flexible.expected_amount) }}
    </div>
    <div v-if="!flexible.fixed && flexible.min !== null" class="q-mb-xs">
      <strong>Min:</strong> {{ formatCurrency(flexible.min) }}
    </div>
    <div v-if="!flexible.fixed && flexible.max !== null" class="q-mb-xs">
      <strong>Max:</strong> {{ formatCurrency(flexible.max) }}
    </div>
    
    <q-separator class="q-my-sm" />
    
    <div class="q-mb-xs">
      <strong>Transaction Total:</strong> 
      <span :class="Math.abs(flexible.transaction_sum) > 0 ? 'text-negative' : 'text-grey'">
        {{ formatCurrency(Math.abs(flexible.transaction_sum)) }}
      </span>
    </div>
    <div class="q-mb-xs">
      <strong>Remaining:</strong> 
      <span :class="flexible.amount_after_transactions > 0 ? 'text-positive' : flexible.amount_after_transactions < 0 ? 'text-negative' : 'text-grey'">
        {{ formatCurrency(flexible.amount_after_transactions) }}
      </span>
    </div>
    
    <div v-if="!flexible.enable" class="q-mt-sm">
      <q-badge color="grey">Disabled</q-badge>
    </div>
  </q-item-section>
</template>
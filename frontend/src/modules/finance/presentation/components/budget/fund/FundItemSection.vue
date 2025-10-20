<script setup lang="ts">
import type { FundBudgetResponse } from 'src/api';

interface Props {
  fund: FundBudgetResponse;
}

defineProps<Props>();

const formatCurrency = (value: number | null | undefined) => 
  value !== null && value !== undefined ? `$${value.toLocaleString()}` : 'N/A';
</script>

<template>
  <q-item-section>
    <div class="q-mb-xs text-h6 text-dark">{{ fund.name }}</div>
    <div class="q-mb-xs">
      <strong>Current Amount:</strong> {{ formatCurrency(fund.current_amount) }}
    </div>
    <div class="q-mb-xs">
      <strong>Increment:</strong> {{ formatCurrency(fund.increment) }}
    </div>
    <div v-if="fund.priority !== null" class="q-mb-xs">
      <strong>Priority:</strong> {{ fund.priority }}
    </div>
    <div v-if="fund.max !== null" class="q-mb-xs">
      <strong>Max:</strong> {{ formatCurrency(fund.max) }}
    </div>
    
    <q-separator class="q-my-sm" />
    
    <div class="q-mb-xs">
      <strong>Transaction Total:</strong> 
      <span :class="fund.transaction_sum >= 0 ? 'text-positive' : 'text-negative'">
        {{ formatCurrency(fund.transaction_sum) }}
      </span>
    </div>
    <div class="q-mb-xs">
      <strong>Amount After Transactions:</strong> 
      <span :class="fund.amount_after_transactions >= 0 ? 'text-positive' : 'text-negative'">
        {{ formatCurrency(fund.amount_after_transactions) }}
      </span>
    </div>
    
    <div v-if="!fund.enable" class="q-mt-sm">
      <q-badge color="grey">Disabled</q-badge>
    </div>
  </q-item-section>
</template>
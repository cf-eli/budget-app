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
  <q-card flat bordered class="budget-item-card">
    <q-card-section class="q-pa-md">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6 text-white">{{ expense.name }}</div>
        <q-badge 
          :color="expense.fixed ? 'blue-grey-8' : 'orange-8'" 
          text-color="white"
        >
          {{ expense.fixed ? 'Fixed' : 'Flexible' }}
        </q-badge>
      </div>

      <div class="row items-start justify-between">
        <div class="col">
          <q-list dense class="text-white">
            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Type:</q-item-label>
                <q-item-label>{{ expense.fixed ? 'Fixed' : 'Estimated' }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Expected Amount</q-item-label>
                <q-item-label>{{ formatCurrency(expense.expected_amount) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Remaining</q-item-label>
                <q-item-label>{{ formatCurrency(expense.amount_after_transactions) }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <div class="col-auto text-right">
          <div 
            class="text-h4 text-weight-bold q-mb-xs"
            :class="expense.transaction_sum < 0 ? 'text-negative' : 'text-positive'"
          >
            {{ formatCurrency(Math.abs(expense.transaction_sum)) }}
          </div>
          <div class="text-subtitle2 text-positive">
            {{ formatCurrency(expense.amount_after_transactions) }}
          </div>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<style scoped>
.budget-item-card {
  background: #2a2d35;
  border-color: #3a3d45;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.budget-item-card:hover {
  border-color: #ef4444;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
}
</style>
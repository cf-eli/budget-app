<script setup lang="ts">
import type { FundBudgetResponse } from 'src/api'

interface Props {
  fund: FundBudgetResponse
}

defineProps<Props>()

const formatCurrency = (value: number | null | undefined) =>
  value !== null && value !== undefined ? `$${value.toLocaleString()}` : 'N/A'
</script>

<template>
  <q-card flat bordered class="budget-item-card">
    <q-card-section class="q-pa-md">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6 text-white">{{ fund.name }}</div>
        <q-badge v-if="fund.priority !== null" color="teal-8" text-color="white">
          Priority: {{ fund.priority }}
        </q-badge>
      </div>

      <div class="row items-start justify-between">
        <div class="col">
          <q-list dense class="text-white">
            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Current Amount</q-item-label>
                <q-item-label>{{ formatCurrency(fund.current_amount) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Increment</q-item-label>
                <q-item-label>{{ formatCurrency(fund.increment) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item v-if="fund.max !== null" class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Max</q-item-label>
                <q-item-label>{{ formatCurrency(fund.max) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Transaction Total</q-item-label>
                <q-item-label
                  :class="fund.transaction_sum >= 0 ? 'text-positive' : 'text-negative'"
                >
                  {{ formatCurrency(fund.transaction_sum) }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <div class="col-auto text-right">
          <div
            class="text-h4 text-weight-bold q-mb-xs"
            :class="fund.amount_after_transactions >= 0 ? 'text-teal' : 'text-negative'"
          >
            {{ formatCurrency(Math.abs(fund.amount_after_transactions)) }}
          </div>
          <div class="text-caption text-grey-5">Amount After Transactions</div>
        </div>
      </div>

      <q-badge v-if="!fund.enable" color="grey" class="q-mt-sm"> Disabled </q-badge>
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
  border-color: #14b8a6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(20, 184, 166, 0.1);
}
</style>

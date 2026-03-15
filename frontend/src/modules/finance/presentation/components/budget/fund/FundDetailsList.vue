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
  <q-list dense class="text-white">
    <q-item class="q-px-none q-py-xs">
      <q-item-section>
        <q-item-label caption class="text-grey-5">Master Balance</q-item-label>
        <q-item-label class="text-weight-medium">{{
          formatCurrency(fund.master_balance)
        }}</q-item-label>
      </q-item-section>
    </q-item>

    <q-item class="q-px-none q-py-xs">
      <q-item-section>
        <q-item-label caption class="text-grey-5">This Month</q-item-label>
        <q-item-label>{{ formatCurrency(fund.month_amount) }}</q-item-label>
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
        <q-item-label :class="fund.transaction_sum >= 0 ? 'text-positive' : 'text-negative'">
          {{ formatCurrency(fund.transaction_sum) }}
        </q-item-label>
      </q-item-section>
    </q-item>
  </q-list>
</template>

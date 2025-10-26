<script setup lang="ts">
import type { FlexibleBudgetResponse } from 'src/api'

interface Props {
  flexible: FlexibleBudgetResponse
}

defineProps<Props>()

const formatCurrency = (value: number | null | undefined) =>
  value !== null && value !== undefined ? `$${value.toLocaleString()}` : 'N/A'
</script>

<template>
  <q-card flat bordered class="budget-item-card">
    <q-card-section class="q-pa-md">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6 text-white">{{ flexible.name }}</div>
        <q-badge :color="flexible.fixed ? 'blue-grey-8' : 'orange-8'" text-color="white">
          {{ flexible.fixed ? 'Fixed' : 'Flexible' }}
        </q-badge>
      </div>

      <div class="row items-start justify-between">
        <div class="col">
          <q-list dense class="text-white">
            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Type:</q-item-label>
                <q-item-label>{{ flexible.fixed ? 'Fixed' : 'Estimated' }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Expected Amount</q-item-label>
                <q-item-label>{{ formatCurrency(flexible.expected_amount) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item v-if="!flexible.fixed && flexible.min !== null" class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Min</q-item-label>
                <q-item-label>{{ formatCurrency(flexible.min) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item v-if="!flexible.fixed && flexible.max !== null" class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Max</q-item-label>
                <q-item-label>{{ formatCurrency(flexible.max) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Remaining</q-item-label>
                <q-item-label
                  :class="
                    flexible.amount_after_transactions > 0
                      ? 'text-positive'
                      : flexible.amount_after_transactions < 0
                        ? 'text-negative'
                        : 'text-grey'
                  "
                >
                  {{ formatCurrency(flexible.amount_after_transactions) }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <div class="col-auto text-right">
          <div
            class="text-h4 text-weight-bold q-mb-xs"
            :class="Math.abs(flexible.transaction_sum) > 0 ? 'text-negative' : 'text-grey'"
          >
            -{{ formatCurrency(Math.abs(flexible.transaction_sum)) }}
          </div>
          <div
            class="text-subtitle2"
            :class="flexible.amount_after_transactions > 0 ? 'text-positive' : 'text-grey-6'"
          >
            {{ formatCurrency(flexible.amount_after_transactions) }}
          </div>
        </div>
      </div>

      <q-badge v-if="!flexible.enable" color="grey" class="q-mt-sm"> Disabled </q-badge>
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
  border-color: #f59e0b;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
}
</style>

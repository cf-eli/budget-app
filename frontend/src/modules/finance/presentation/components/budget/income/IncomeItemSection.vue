<script setup lang="ts">
import type { IncomeBudgetResponse } from 'src/api'
import { useDeleteBudget } from 'src/modules/finance/presentation/composables/useDeleteBudget'

interface Props {
  income: IncomeBudgetResponse
}

interface Emits {
  (_event: 'deleted'): void
}

const _props = defineProps<Props>()
const emit = defineEmits<Emits>()
const { handleDelete } = useDeleteBudget()

const formatCurrency = (value: number | null | undefined) =>
  value !== null && value !== undefined ? `$${value.toLocaleString()}` : 'N/A'

</script>

<template>
  <q-card flat bordered class="budget-item-card">
    <q-card-section class="q-pa-md">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6 text-white">{{ income.name }}</div>
        <div class="row items-center q-gutter-xs">
          <q-badge :color="income.fixed ? 'blue-grey-8' : 'orange-8'" text-color="white">
            {{ income.fixed ? 'Fixed' : 'Flexible' }}
          </q-badge>
          <q-btn
            flat
            dense
            round
            size="sm"
            icon="delete"
            color="negative"
            @click="handleDelete(income.id, income.name, () => emit('deleted'))"
          >
            <q-tooltip>Delete budget (click twice to confirm)</q-tooltip>
          </q-btn>
        </div>
      </div>

      <div class="row items-start justify-between">
        <div class="col">
          <q-list dense class="text-white">
            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Type:</q-item-label>
                <q-item-label>{{ income.fixed ? 'Fixed' : 'Estimated' }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Expected Amount</q-item-label>
                <q-item-label>{{ formatCurrency(income.expected_amount) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Remaining</q-item-label>
                <q-item-label
                  :class="income.amount_after_transactions >= 0 ? 'text-positive' : 'text-negative'"
                >
                  {{ formatCurrency(income.amount_after_transactions) }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <div class="col-auto text-right">
          <div class="text-h4 text-weight-bold text-positive">
            {{ formatCurrency(income.transaction_sum) }}
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
  border-color: #10b981;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}
</style>

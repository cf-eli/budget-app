<script setup lang="ts">
import { ref } from 'vue'
import type { FundBudgetResponse } from 'src/api'
import { useDeleteBudget } from 'src/modules/finance/presentation/composables/useDeleteBudget'
import FundCalculationDialog from './FundCalculationDialog.vue'

interface Props {
  fund: FundBudgetResponse
  currentMonth?: number
  currentYear?: number
}

interface Emits {
  (_event: 'refresh'): void
  (_event: 'deleted'): void
}

const _props = defineProps<Props>()
const emit = defineEmits<Emits>()
const { handleDelete } = useDeleteBudget()

const showCalculationDialog = ref(false)

const formatCurrency = (value: number | null | undefined) =>
  value !== null && value !== undefined ? `$${value.toLocaleString()}` : 'N/A'

function viewCalculation(event: Event) {
  event.stopPropagation()
  showCalculationDialog.value = true
}

function handleRefresh() {
  emit('refresh')
}
</script>

<template>
  <q-card flat bordered class="budget-item-card">
    <q-card-section class="q-pa-md">
      <div class="row items-center justify-between q-mb-md">
        <div class="col">
          <div class="row items-center q-gutter-sm">
            <div class="text-h6 text-white">{{ fund.name }}</div>
            <q-icon
              v-if="fund.is_linked"
              name="link"
              color="positive"
              size="20px"
            >
              <q-tooltip>Linked to previous month</q-tooltip>
            </q-icon>
          </div>
          <div v-if="fund.master_fund_name" class="text-caption text-grey-5 q-mt-xs">
            <q-icon name="account_balance_wallet" size="14px" class="q-mr-xs" />
            Master: {{ fund.master_fund_name }}
          </div>
        </div>
        <div class="row items-center q-gutter-sm">
          <q-badge v-if="fund.priority !== null" color="teal-8" text-color="white">
            Priority: {{ fund.priority }}
          </q-badge>
          <q-btn
            flat
            round
            dense
            icon="calculate"
            color="primary"
            size="sm"
            @click="viewCalculation"
          >
            <q-tooltip>View Calculation Details</q-tooltip>
          </q-btn>
          <q-btn
            flat
            round
            dense
            icon="delete"
            color="negative"
            size="sm"
            @click="handleDelete(fund.id, fund.name, () => emit('deleted'))"
          >
            <q-tooltip>Delete fund (click twice to confirm)</q-tooltip>
          </q-btn>
        </div>
      </div>

      <div class="row items-start justify-between">
        <div class="col">
          <q-list dense class="text-white">
            <q-item class="q-px-none q-py-xs">
              <q-item-section>
                <q-item-label caption class="text-grey-5">Master Balance</q-item-label>
                <q-item-label class="text-weight-medium">{{ formatCurrency(fund.master_balance) }}</q-item-label>
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

    <!-- Calculation Dialog -->
    <fund-calculation-dialog
      v-if="showCalculationDialog"
      :fund-id="fund.id"
      :fund-name="fund.name"
      :current-month="currentMonth || new Date().getMonth() + 1"
      :current-year="currentYear || new Date().getFullYear()"
      @close="showCalculationDialog = false"
      @refresh="handleRefresh"
    />
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

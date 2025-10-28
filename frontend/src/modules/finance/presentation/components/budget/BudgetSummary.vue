<script setup lang="ts">
import { computed } from 'vue'
import type { IncomeBudgetResponse, ExpenseBudgetResponse, FlexibleBudgetResponse } from 'src/api'

interface Props {
  incomes: IncomeBudgetResponse[]
  expenses: ExpenseBudgetResponse[]
  flexibles: FlexibleBudgetResponse[]
}

const props = defineProps<Props>()

const formatCurrency = (value: number) => `$${value.toLocaleString()}`

// Carryover calculations (sum from all budget types)
const totalCarryover = computed(() => {
  const incomeCarryover = props.incomes.reduce((sum, i) => sum + (i.carryover || 0), 0)
  const expenseCarryover = props.expenses.reduce((sum, e) => sum + (e.carryover || 0), 0)
  const flexibleCarryover = props.flexibles.reduce((sum, f) => sum + (f.carryover || 0), 0)
  return incomeCarryover + expenseCarryover + flexibleCarryover
})

// Expected calculations
const totalExpectedIncome = computed(() =>
  props.incomes.reduce((sum, i) => sum + (i.expected_amount || 0), 0),
)

const totalExpectedExpenses = computed(() =>
  props.expenses.reduce((sum, e) => sum + (e.expected_amount || 0), 0),
)

const totalExpectedFlexibles = computed(() =>
  props.flexibles.reduce((sum, f) => sum + (f.expected_amount || 0), 0),
)

const expectedBalance = computed(
  () => totalExpectedIncome.value - totalExpectedExpenses.value - totalExpectedFlexibles.value + totalCarryover.value,
)

// Current (actual transactions) calculations
const totalCurrentIncome = computed(() =>
  props.incomes.reduce((sum, i) => sum + Math.abs(i.transaction_sum), 0),
)

const totalCurrentExpenses = computed(() =>
  props.expenses.reduce((sum, e) => sum + Math.abs(e.transaction_sum), 0),
)

const totalCurrentFlexibles = computed(() =>
  props.flexibles.reduce((sum, f) => sum + Math.abs(f.transaction_sum), 0),
)

const currentBalance = computed(
  () => totalCurrentIncome.value - totalCurrentExpenses.value - totalCurrentFlexibles.value + totalCarryover.value,
)
</script>

<template>
  <q-card flat bordered class="summary-card q-mb-lg">
    <q-card-section class="q-pa-md">
      <div class="row q-col-gutter-lg">
        <!-- Expected Summary -->
        <div class="col-12 col-md-6">
          <div class="summary-section">
            <div class="row items-center justify-between q-mb-md">
              <div class="text-h6 text-white">Expected Budget</div>
              <q-icon name="assignment" size="24px" color="blue-5" />
            </div>

            <q-list dense class="text-white">
              <q-item class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Income</q-item-label>
                  <q-item-label class="text-positive">{{
                    formatCurrency(totalExpectedIncome)
                  }}</q-item-label>
                </q-item-section>
              </q-item>

              <q-item class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Expenses</q-item-label>
                  <q-item-label class="text-negative"
                    >-{{ formatCurrency(totalExpectedExpenses) }}</q-item-label
                  >
                </q-item-section>
              </q-item>

              <q-item class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Flexible Expenses</q-item-label>
                  <q-item-label class="text-amber"
                    >-{{ formatCurrency(totalExpectedFlexibles) }}</q-item-label
                  >
                </q-item-section>
              </q-item>

              <q-item v-if="totalCarryover !== 0" class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Carryover from Previous Months</q-item-label>
                  <q-item-label
                    :class="totalCarryover >= 0 ? 'text-positive' : 'text-negative'"
                  >
                    {{ totalCarryover >= 0 ? '+' : '' }}{{ formatCurrency(totalCarryover) }}
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-separator color="grey-7" class="q-my-sm" />

              <q-item class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Balance</q-item-label>
                  <q-item-label
                    class="text-h6 text-weight-bold"
                    :class="expectedBalance >= 0 ? 'text-positive' : 'text-negative'"
                  >
                    {{ formatCurrency(Math.abs(expectedBalance)) }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </div>

        <!-- Current Summary -->
        <div class="col-12 col-md-6">
          <div class="summary-section">
            <div class="row items-center justify-between q-mb-md">
              <div class="text-h6 text-white">Current Activity</div>
              <q-icon name="account_balance_wallet" size="24px" color="teal-5" />
            </div>

            <q-list dense class="text-white">
              <q-item class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Income</q-item-label>
                  <q-item-label class="text-positive">{{
                    formatCurrency(totalCurrentIncome)
                  }}</q-item-label>
                </q-item-section>
              </q-item>

              <q-item class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Expenses</q-item-label>
                  <q-item-label class="text-negative"
                    >-{{ formatCurrency(totalCurrentExpenses) }}</q-item-label
                  >
                </q-item-section>
              </q-item>

              <q-item class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Flexible Expenses</q-item-label>
                  <q-item-label class="text-amber"
                    >-{{ formatCurrency(totalCurrentFlexibles) }}</q-item-label
                  >
                </q-item-section>
              </q-item>

              <q-item v-if="totalCarryover !== 0" class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Carryover from Previous Months</q-item-label>
                  <q-item-label
                    :class="totalCarryover >= 0 ? 'text-positive' : 'text-negative'"
                  >
                    {{ totalCarryover >= 0 ? '+' : '' }}{{ formatCurrency(totalCarryover) }}
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-separator color="grey-7" class="q-my-sm" />

              <q-item class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Balance</q-item-label>
                  <q-item-label
                    class="text-h6 text-weight-bold"
                    :class="currentBalance >= 0 ? 'text-positive' : 'text-negative'"
                  >
                    {{ formatCurrency(currentBalance) }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<style scoped>
.summary-card {
  background: #2a2d35;
  border-color: #3a3d45;
}

.summary-section {
  background: #1e2027;
  border-radius: 8px;
  padding: 16px;
}
</style>

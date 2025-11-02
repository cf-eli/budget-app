<script setup lang="ts">
import { ref, computed } from 'vue'
import type { IncomeBudgetResponse, ExpenseBudgetResponse, FlexibleBudgetResponse, FundBudgetResponse } from 'src/api'
import ApplyFundsDialog from './fund/ApplyFundsDialog.vue'

interface Props {
  incomes: IncomeBudgetResponse[]
  expenses: ExpenseBudgetResponse[]
  flexibles: FlexibleBudgetResponse[]
  funds: FundBudgetResponse[]
  currentMonth: number
  currentYear: number
}

interface Emits {
  (_event: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const showApplyFundsDialog = ref(false)

const formatCurrency = (value: number) => `$${value.toLocaleString()}`

/**
 * Balance calculation formula (single source of truth):
 * 
 * balance = income + expenses + flexibles + carryover - current_month_funds
 * 
 * Where:
 * - carryover = backend-calculated cumulative balance from all previous months
 *   - For income/expense/flexible: sum of all previous transaction_sum
 *   - For funds: sum of (-month_amount) for all previous months
 *     * Fund transactions are IGNORED - they only affect master fund balance
 *     * Only allocations reduce available balance
 * - current_month_funds = this month's fund allocations (month_amount)
 * 
 * This ensures:
 * - Previous month's ending balance = next month's carryover
 * - Fund allocations reduce available balance
 * - Fund transactions (withdrawals/deposits) ONLY affect master balance
 * 
 * See backend: src/finance_api/crud/budget.py::get_carryover_for_budgets()
 */

// Carryover calculations (sum from all budget types)
// Includes fund allocations because money allocated to funds reduces available balance
const totalCarryover = computed(() => {
  const incomeCarryover = props.incomes.reduce((sum, i) => sum + (i.carryover || 0), 0)
  const expenseCarryover = props.expenses.reduce((sum, e) => sum + (e.carryover || 0), 0)
  const flexibleCarryover = props.flexibles.reduce((sum, f) => sum + (f.carryover || 0), 0)
  const fundCarryover = props.funds.reduce((sum, f) => sum + (f.carryover || 0), 0)
  return incomeCarryover + expenseCarryover + flexibleCarryover + fundCarryover
})

// Fund calculations (using month_amount for monthly contribution, not cumulative master_balance)
const totalFunds = computed(() =>
  props.funds.reduce((sum, f) => sum + (f.month_amount || 0), 0)
)

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
  () => totalExpectedIncome.value - totalExpectedExpenses.value - totalExpectedFlexibles.value + totalCarryover.value - totalFunds.value,
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
  () => totalCurrentIncome.value - totalCurrentExpenses.value - totalCurrentFlexibles.value + totalCarryover.value - totalFunds.value,
)

function openApplyFundsDialog() {
  showApplyFundsDialog.value = true
}

function handleFundsApplied() {
  emit('refresh')
}
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

              <q-item v-if="totalFunds > 0" class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Funds (Savings)</q-item-label>
                  <q-item-label class="text-amber">
                    -{{ formatCurrency(totalFunds) }}
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

              <q-item v-if="totalFunds > 0" class="q-px-none q-py-xs">
                <q-item-section>
                  <q-item-label caption class="text-grey-5">Funds (Savings)</q-item-label>
                  <q-item-label class="text-amber">
                    -{{ formatCurrency(totalFunds) }}
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

            <!-- Apply Funds Button -->
            <div class="q-mt-md">
              <q-btn
                flat
                color="primary"
                label="Apply Fund Increments"
                icon="savings"
                class="full-width"
                @click="openApplyFundsDialog"
              />
            </div>
          </div>
        </div>
      </div>
    </q-card-section>

    <!-- Apply Funds Dialog -->
    <apply-funds-dialog
      v-if="showApplyFundsDialog"
      :month="currentMonth"
      :year="currentYear"
      :current-balance="currentBalance"
      @close="showApplyFundsDialog = false"
      @applied="handleFundsApplied"
    />
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

<script setup lang="ts">
import { ref } from 'vue'
import type {
  IncomeBudgetResponse,
  ExpenseBudgetResponse,
  FlexibleBudgetResponse,
  FundBudgetResponse,
} from 'src/api'
import ApplyFundsDialog from './fund/ApplyFundsDialog.vue'
import BudgetSummarySection from './BudgetSummarySection.vue'
import { useBudgetSummary } from '../../composables/useBudgetSummary'

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

const {
  totalCarryover,
  totalFunds,
  totalExpectedIncome,
  totalExpectedExpenses,
  totalExpectedFlexibles,
  expectedBalance,
  totalCurrentIncome,
  totalCurrentExpenses,
  totalCurrentFlexibles,
  currentBalance,
} = useBudgetSummary({
  incomes: () => props.incomes,
  expenses: () => props.expenses,
  flexibles: () => props.flexibles,
  funds: () => props.funds,
})

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
          <BudgetSummarySection
            title="Expected Budget"
            icon="assignment"
            icon-color="blue-5"
            :income="totalExpectedIncome"
            :expenses="totalExpectedExpenses"
            :flexibles="totalExpectedFlexibles"
            :carryover="totalCarryover"
            :funds="totalFunds"
            :balance="expectedBalance"
          />
        </div>

        <!-- Current Summary -->
        <div class="col-12 col-md-6">
          <BudgetSummarySection
            title="Current Activity"
            icon="account_balance_wallet"
            icon-color="teal-5"
            :income="totalCurrentIncome"
            :expenses="totalCurrentExpenses"
            :flexibles="totalCurrentFlexibles"
            :carryover="totalCarryover"
            :funds="totalFunds"
            :balance="currentBalance"
          >
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
          </BudgetSummarySection>
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
</style>

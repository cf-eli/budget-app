<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import IncomeCard from 'src/modules/finance/presentation/components/budget/income/IncomeCard.vue'
import ExpenseCard from 'src/modules/finance/presentation/components/budget/expense/ExpenseCard.vue'
import FlexibleCard from 'src/modules/finance/presentation/components/budget/flexible/FlexibleCard.vue'
import FundCard from 'src/modules/finance/presentation/components/budget/fund/FundCard.vue'
import BudgetSummary from 'src/modules/finance/presentation/components/budget/BudgetSummary.vue'
import MonthYearSelector from 'src/modules/finance/presentation/components/MonthYearSelector.vue'
import {
  apiV1BudgetsAllGetAllBudgets,
  apiV1BudgetsCreateCreateBudget,
  type IncomeBudgetResponse,
  type ExpenseBudgetResponse,
  type FlexibleBudgetResponse,
  type FundBudgetResponse,
  type BudgetRequest,
} from 'src/api'
import { useBudgetStore } from 'src/modules/finance/presentation/stores/budgetStore'
import { useDateSelectionStore } from 'src/modules/finance/presentation/stores/dateSelectionStore'

const budgetStore = useBudgetStore()
const dateStore = useDateSelectionStore()

const incomes = ref<IncomeBudgetResponse[]>([])
const expenses = ref<ExpenseBudgetResponse[]>([])
const flexibles = ref<FlexibleBudgetResponse[]>([])
const funds = ref<FundBudgetResponse[]>([])
const loading = ref(false)

const selectedMonthYear = computed({
  get: () => ({
    month: dateStore.selectedMonth,
    year: dateStore.selectedYear,
  }),
  set: (value) => {
    dateStore.setMonthYear(value.month, value.year)
  },
})

async function fetchBudgets() {
  loading.value = true
  try {
    const response = await apiV1BudgetsAllGetAllBudgets({
      query: {
        month: dateStore.selectedMonth,
        year: dateStore.selectedYear,
      },
    })

    if (response.data) {
      incomes.value = response.data.incomes || []
      expenses.value = response.data.expenses || []
      flexibles.value = response.data.flexibles || []
      funds.value = response.data.funds || []
    }
  } catch (error) {
    console.error('Error fetching budgets:', error)
  } finally {
    loading.value = false
  }
}

async function createBudget(budget: BudgetRequest) {
  try {
    const response = await apiV1BudgetsCreateCreateBudget({
      body: budget,
    })

    if (response.data) {
      await fetchBudgets()
      budgetStore.clearCache()
      await budgetStore.fetchBudgets(true)
      return { success: true, data: response.data }
    }
  } catch (error) {
    console.error('Error creating budget:', error)
    return { success: false, error }
  }
}

function handleMonthYearChange() {
  fetchBudgets()
  // Update budget store to use the selected month/year
  budgetStore.clearCache()
}

// Watch for external changes to the date store
watch(
  () => [dateStore.selectedMonth, dateStore.selectedYear],
  () => {
    fetchBudgets()
    budgetStore.clearCache()
  }
)

onMounted(() => {
  fetchBudgets()
})
</script>

<template>
  <q-page class="budget-page q-pa-lg">
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>

    <div class="row items-center justify-between q-mb-md">
      <div class="text-h5 text-white">Budgets</div>
      <month-year-selector v-model="selectedMonthYear" @update:model-value="handleMonthYearChange" />
    </div>

    <budget-summary :incomes="incomes" :expenses="expenses" :flexibles="flexibles" />

    <income-card :incomes="incomes" @refresh="fetchBudgets" @create="createBudget" />
    <expense-card :expenses="expenses" @refresh="fetchBudgets" @create="createBudget" />
    <flexible-card :flexibles="flexibles" @refresh="fetchBudgets" @create="createBudget" />
    <fund-card :funds="funds" @refresh="fetchBudgets" @create="createBudget" />
  </q-page>
</template>

<style scoped>
.budget-page {
  background: #16171d;
  min-height: 100vh;
}
</style>

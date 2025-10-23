<script setup lang="ts">
import { onMounted, ref } from 'vue';
import IncomeCard from 'src/modules/finance/presentation/components/budget/income/IncomeCard.vue';
import ExpenseCard from 'src/modules/finance/presentation/components/budget/expense/ExpenseCard.vue';
import FlexibleCard from 'src/modules/finance/presentation/components/budget/flexible/FlexibleCard.vue';
import FundCard from 'src/modules/finance/presentation/components/budget/fund/FundCard.vue';
import BudgetSummary from 'src/modules/finance/presentation/components/budget/BudgetSummary.vue';
import {
  apiFinanceV1BudgetsAllGetAllBudgets,
  apiFinanceV1BudgetsCreateCreateBudget,
  type IncomeBudgetResponse,
  type ExpenseBudgetResponse,
  type FlexibleBudgetResponse,
  type FundBudgetResponse,
  type BudgetRequest
} from 'src/api';
import { useBudgetStore } from 'src/modules/finance/presentation/stores/budgetStore';

const budgetStore = useBudgetStore();

const incomes = ref<IncomeBudgetResponse[]>([]);
const expenses = ref<ExpenseBudgetResponse[]>([]);
const flexibles = ref<FlexibleBudgetResponse[]>([]);
const funds = ref<FundBudgetResponse[]>([]);
const loading = ref(false);

async function fetchBudgets() {
  loading.value = true;
  try {
    const response = await apiFinanceV1BudgetsAllGetAllBudgets();

    if (response.data) {
      incomes.value = response.data.incomes || [];
      expenses.value = response.data.expenses || [];
      flexibles.value = response.data.flexibles || [];
      funds.value = response.data.funds || [];
    }
  } catch (error) {
    console.error('Error fetching budgets:', error);
  } finally {
    loading.value = false;
  }
}

async function createBudget(budget: BudgetRequest) {
  try {
    const response = await apiFinanceV1BudgetsCreateCreateBudget({
      body: budget
    });

    if (response.data) {
      await fetchBudgets();
      budgetStore.clearCache();
      await budgetStore.fetchBudgets(true);
      return { success: true, data: response.data };
    }
  } catch (error) {
    console.error('Error creating budget:', error);
    return { success: false, error };
  }
}

onMounted(() => {
  fetchBudgets();
});
</script>

<template>
  <q-page class="budget-page q-pa-lg">
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>

    <budget-summary 
      :incomes="incomes"
      :expenses="expenses"
      :flexibles="flexibles"
    />

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
<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import IncomeCard from 'src/modules/finance/presentation/components/budget/income/IncomeCard.vue'
import ExpenseCard from 'src/modules/finance/presentation/components/budget/expense/ExpenseCard.vue'
import FlexibleCard from 'src/modules/finance/presentation/components/budget/flexible/FlexibleCard.vue'
import FundCard from 'src/modules/finance/presentation/components/budget/fund/FundCard.vue'
import BudgetSummary from 'src/modules/finance/presentation/components/budget/BudgetSummary.vue'
import MonthYearSelector from 'src/modules/finance/presentation/components/MonthYearSelector.vue'
import CopyBudgetsDialog from 'src/modules/finance/presentation/components/budget/CopyBudgetsDialog.vue'
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

const $q = useQuasar()
const budgetStore = useBudgetStore()
const dateStore = useDateSelectionStore()

const incomes = ref<IncomeBudgetResponse[]>([])
const expenses = ref<ExpenseBudgetResponse[]>([])
const flexibles = ref<FlexibleBudgetResponse[]>([])
const funds = ref<FundBudgetResponse[]>([])
const loading = ref(false)
const showCopyDialog = ref(false)
const dismissedBanners = ref<Set<string>>(new Set())
const sourceMonthYear = ref<{ month: number; year: number } | null>(null)
const checkingForSource = ref(false)

const selectedMonthYear = computed({
  get: () => ({
    month: dateStore.selectedMonth,
    year: dateStore.selectedYear,
  }),
  set: (value) => {
    dateStore.setMonthYear(value.month, value.year)
  },
})

const hasNoBudgets = computed(() => {
  return (
    !loading.value &&
    incomes.value.length === 0 &&
    expenses.value.length === 0 &&
    flexibles.value.length === 0 &&
    funds.value.length === 0
  )
})

const bannerKey = computed(() => `${dateStore.selectedMonth}-${dateStore.selectedYear}`)

const showBanner = computed(() => {
  return (
    hasNoBudgets.value &&
    !dismissedBanners.value.has(bannerKey.value) &&
    sourceMonthYear.value !== null &&
    !checkingForSource.value
  )
})

const monthNames = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
]

const currentMonthName = computed(() => monthNames[dateStore.selectedMonth - 1])

const sourceMonthName = computed(() => {
  if (!sourceMonthYear.value) return ''
  return monthNames[sourceMonthYear.value.month - 1]
})

async function fetchBudgets() {
  loading.value = true
  // Reset source month immediately to prevent flash with stale data
  sourceMonthYear.value = null
  checkingForSource.value = true

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

    // Check for source month if no budgets
    if (hasNoBudgets.value && !dismissedBanners.value.has(bannerKey.value)) {
      await findSourceMonth()
    } else {
      // If we have budgets or banner dismissed, clear checking flag
      checkingForSource.value = false
    }
  } catch (error) {
    console.error('Error fetching budgets:', error)
    checkingForSource.value = false
  } finally {
    loading.value = false
  }
}

async function findSourceMonth() {
  // Already checking, don't start another check
  if (checkingForSource.value) return

  checkingForSource.value = true

  try {
    const now = new Date()
    const currentMonth = now.getMonth() + 1
    const currentYear = now.getFullYear()
    const selectedMonth = dateStore.selectedMonth
    const selectedYear = dateStore.selectedYear

    // Determine if we're looking at a past month relative to current date
    const isInPast =
      selectedYear < currentYear ||
      (selectedYear === currentYear && selectedMonth < currentMonth)

    // Try previous month first
    const prevMonth = selectedMonth === 1 ? 12 : selectedMonth - 1
    const prevYear = selectedMonth === 1 ? selectedYear - 1 : selectedYear

    const prevResponse = await apiV1BudgetsAllGetAllBudgets({
      query: { month: prevMonth, year: prevYear },
    })

    const hasPrevBudgets =
      prevResponse.data &&
      (prevResponse.data.incomes.length > 0 ||
        prevResponse.data.expenses.length > 0 ||
        prevResponse.data.flexibles.length > 0 ||
        prevResponse.data.funds.length > 0)

    if (hasPrevBudgets) {
      sourceMonthYear.value = { month: prevMonth, year: prevYear }
      return
    }

    // If in past and no previous month, try next month
    if (isInPast) {
      const nextMonth = selectedMonth === 12 ? 1 : selectedMonth + 1
      const nextYear = selectedMonth === 12 ? selectedYear + 1 : selectedYear

      const nextResponse = await apiV1BudgetsAllGetAllBudgets({
        query: { month: nextMonth, year: nextYear },
      })

      const hasNextBudgets =
        nextResponse.data &&
        (nextResponse.data.incomes.length > 0 ||
          nextResponse.data.expenses.length > 0 ||
          nextResponse.data.flexibles.length > 0 ||
          nextResponse.data.funds.length > 0)

      if (hasNextBudgets) {
        sourceMonthYear.value = { month: nextMonth, year: nextYear }
        return
      }
    }

    // No source found
    sourceMonthYear.value = null
  } catch (error) {
    console.error('Error finding source month:', error)
    sourceMonthYear.value = null
  } finally {
    checkingForSource.value = false
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

function handleCopyFromPrevious() {
  showCopyDialog.value = true
}

async function confirmCopyBudgets() {
  if (!sourceMonthYear.value) return

  try {
    const result = await budgetStore.copyFromPreviousMonth(
      dateStore.selectedMonth,
      dateStore.selectedYear,
      sourceMonthYear.value.month,
      sourceMonthYear.value.year
    )

    if (result) {
      $q.notify({
        type: 'positive',
        message: `Successfully copied ${result.copied_budgets.income + result.copied_budgets.expense + result.copied_budgets.flexible + result.copied_budgets.fund} budgets from ${sourceMonthName.value} ${result.source_year}`,
        timeout: 3000,
      })
      showCopyDialog.value = false
      await fetchBudgets()
      budgetStore.clearCache()
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  } catch (error) {
    console.error('Error copying budgets:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to copy budgets. Please try again.',
      timeout: 3000,
    })
  }
}

function dismissBanner() {
  dismissedBanners.value.add(bannerKey.value)
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

    <!-- No Budgets Banner -->
    <q-banner v-if="showBanner && sourceMonthYear" class="bg-grey-9 text-white q-mb-md" rounded>
      <template #avatar>
        <q-icon name="info" color="blue-5" size="md" />
      </template>
      <div class="text-subtitle1 q-mb-sm">
        No budgets found for {{ currentMonthName }} {{ selectedMonthYear.year }}
      </div>
      <div class="text-body2 q-mb-md">
        Would you like to copy budgets from
        {{ sourceMonthName }} {{ sourceMonthYear.year }}?
      </div>
      <div class="row q-gutter-sm">
        <q-btn
          unelevated
          :label="`Copy from ${sourceMonthName}`"
          color="primary"
          @click="handleCopyFromPrevious"
        />
        <q-btn flat label="Start Fresh" color="white" @click="dismissBanner" />
      </div>
    </q-banner>

    <budget-summary :incomes="incomes" :expenses="expenses" :flexibles="flexibles" />

    <income-card :incomes="incomes" @refresh="fetchBudgets" @create="createBudget" />
    <expense-card :expenses="expenses" @refresh="fetchBudgets" @create="createBudget" />
    <flexible-card :flexibles="flexibles" @refresh="fetchBudgets" @create="createBudget" />
    <fund-card :funds="funds" @refresh="fetchBudgets" @create="createBudget" />

    <!-- Copy Budgets Dialog -->
    <q-dialog
      v-model="showCopyDialog"
      :maximized="$q.screen.lt.sm"
      transition-show="slide-up"
      transition-hide="slide-down"
    >
      <copy-budgets-dialog
        v-if="sourceMonthYear"
        :target-month="dateStore.selectedMonth"
        :target-year="dateStore.selectedYear"
        :previous-month="sourceMonthYear.month"
        :previous-year="sourceMonthYear.year"
        @confirm="confirmCopyBudgets"
        @cancel="showCopyDialog = false"
      />
    </q-dialog>
  </q-page>
</template>

<style scoped>
.budget-page {
  background: #16171d;
  min-height: 100vh;
}
</style>

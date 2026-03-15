import { computed } from 'vue'
import type {
  IncomeBudgetResponse,
  ExpenseBudgetResponse,
  FlexibleBudgetResponse,
  FundBudgetResponse,
} from 'src/api'

interface BudgetSummaryInput {
  incomes: () => IncomeBudgetResponse[]
  expenses: () => ExpenseBudgetResponse[]
  flexibles: () => FlexibleBudgetResponse[]
  funds: () => FundBudgetResponse[]
}

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
export function useBudgetSummary(input: BudgetSummaryInput) {
  const totalCarryover = computed(() => {
    const incomeCarryover = input.incomes().reduce((sum, i) => sum + (i.carryover || 0), 0)
    const expenseCarryover = input.expenses().reduce((sum, e) => sum + (e.carryover || 0), 0)
    const flexibleCarryover = input.flexibles().reduce((sum, f) => sum + (f.carryover || 0), 0)
    const fundCarryover = input.funds().reduce((sum, f) => sum + (f.carryover || 0), 0)
    return incomeCarryover + expenseCarryover + flexibleCarryover + fundCarryover
  })

  const totalFunds = computed(() =>
    input.funds().reduce((sum, f) => sum + (f.month_amount || 0), 0),
  )

  // Expected calculations
  const totalExpectedIncome = computed(() =>
    input.incomes().reduce((sum, i) => sum + (i.expected_amount || 0), 0),
  )

  const totalExpectedExpenses = computed(() =>
    input.expenses().reduce((sum, e) => sum + (e.expected_amount || 0), 0),
  )

  const totalExpectedFlexibles = computed(() =>
    input.flexibles().reduce((sum, f) => sum + (f.expected_amount || 0), 0),
  )

  const expectedBalance = computed(
    () =>
      totalExpectedIncome.value -
      totalExpectedExpenses.value -
      totalExpectedFlexibles.value +
      totalCarryover.value -
      totalFunds.value,
  )

  // Current (actual transactions) calculations
  const totalCurrentIncome = computed(() =>
    input.incomes().reduce((sum, i) => sum + Math.abs(i.transaction_sum), 0),
  )

  const totalCurrentExpenses = computed(() =>
    input.expenses().reduce((sum, e) => sum + Math.abs(e.transaction_sum), 0),
  )

  const totalCurrentFlexibles = computed(() =>
    input.flexibles().reduce((sum, f) => sum + Math.abs(f.transaction_sum), 0),
  )

  const currentBalance = computed(
    () =>
      totalCurrentIncome.value -
      totalCurrentExpenses.value -
      totalCurrentFlexibles.value +
      totalCarryover.value -
      totalFunds.value,
  )

  return {
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
  }
}

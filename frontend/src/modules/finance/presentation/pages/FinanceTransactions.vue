<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { apiV1TransactionsGetTransactions, type TransactionResponse } from 'src/api'
import TransactionTable from 'src/modules/finance/presentation/components/TransactionTable.vue'
import MonthYearSelector from 'src/modules/finance/presentation/components/MonthYearSelector.vue'
import { useDateSelectionStore } from 'src/modules/finance/presentation/stores/dateSelectionStore'

const dateStore = useDateSelectionStore()

const transactions = ref<TransactionResponse[]>([])
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

const pagination = ref({
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
  sortBy: 'transacted_at',
  descending: true,
})

async function fetchTransactions() {
  loading.value = true
  try {
    const response = await apiV1TransactionsGetTransactions({
      query: {
        page: pagination.value.page,
        descending: pagination.value.descending,
        sort_by: pagination.value.sortBy,
        rows_per_page: pagination.value.rowsPerPage,
        month: dateStore.selectedMonth,
        year: dateStore.selectedYear,
      },
    })

    if (response.data) {
      // Handle paginated response
      if (!Array.isArray(response.data) && response.data.transactions) {
        transactions.value = response.data.transactions
        pagination.value.rowsNumber = response.data.total
      } else {
        // Fallback for legacy array response
        transactions.value = Array.isArray(response.data) ? response.data : []
        pagination.value.rowsNumber = transactions.value.length
      }
    }
  } catch (error) {
    console.error('Failed to fetch transactions:', error)
  } finally {
    loading.value = false
  }
}

function handlePaginationUpdate(newPagination: typeof pagination.value) {
  // Update pagination but preserve rowsNumber (will be updated after fetch)
  pagination.value.page = newPagination.page
  pagination.value.rowsPerPage = newPagination.rowsPerPage
  pagination.value.sortBy = newPagination.sortBy
  pagination.value.descending = newPagination.descending
  fetchTransactions()
}

function handleRefresh() {
  fetchTransactions()
}

function handleMonthYearChange() {
  // Reset to first page when changing month/year
  pagination.value.page = 1
  fetchTransactions()
}

// Watch for external changes to the date store
watch(
  () => [dateStore.selectedMonth, dateStore.selectedYear],
  () => {
    pagination.value.page = 1
    fetchTransactions()
  }
)

onMounted(() => {
  fetchTransactions()
})
</script>

<template>
  <q-page class="transactions-page q-pa-lg">
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h5 text-white">Transactions</div>
      <month-year-selector v-model="selectedMonthYear" @update:model-value="handleMonthYearChange" />
    </div>

    <transaction-table
      :transactions="transactions"
      :pagination="pagination"
      :loading="loading"
      @update:pagination="handlePaginationUpdate"
      @refresh="handleRefresh"
    />
  </q-page>
</template>

<style scoped>
.transactions-page {
  background: #16171d;
  min-height: 100vh;
}
</style>

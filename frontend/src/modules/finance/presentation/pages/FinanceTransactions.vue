<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { apiFinanceV1TransactionsGetTransactions, type TransactionResponse } from 'src/api';
import TransactionTable from 'src/modules/finance/presentation/components/TransactionTable.vue';

const transactions = ref<TransactionResponse[]>([]);
const loading = ref(false);

const pagination = ref({
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
  sortBy: 'transacted_at',
  descending: true
});

async function fetchTransactions() {
  loading.value = true;
  try {
    const response = await apiFinanceV1TransactionsGetTransactions({
      query: {
        page: pagination.value.page,
        descending: pagination.value.descending,
        sort_by: pagination.value.sortBy,
        rows_per_page: pagination.value.rowsPerPage
      }
    });
   
    if (response.data) {
      transactions.value = Array.isArray(response.data)
        ? response.data
        : response.data.transactions || [];
      
      pagination.value.rowsNumber = response.data.total || transactions.value.length;
    }
  } catch (error) {
    console.error('Failed to fetch transactions:', error);
  } finally {
    loading.value = false;
  }
}

function handlePaginationUpdate(newPagination: typeof pagination.value) {
  pagination.value = newPagination;
  fetchTransactions();
}

function handleRefresh() {
  fetchTransactions();
}

onMounted(() => {
  fetchTransactions();
});
</script>

<template>
  <q-page class="transactions-page q-pa-lg">
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
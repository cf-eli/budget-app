<script setup lang="ts">
import { ref } from 'vue';
import type { GetTransactionResponse } from 'src/api';
import BudgetAssignmentCell from './BudgetAssignmentCell.vue';
import TransactionBreakdownDialog from './breakdown/TransactionBreakdownDialog.vue';

interface Props {
  transactions: GetTransactionResponse[];
  pagination: {
    page: number;
    rowsPerPage: number;
    rowsNumber: number;
    sortBy: string;
    descending: boolean;
  };
  loading?: boolean;
}

interface Emits {
  (e: 'update:pagination', value: Props['pagination']): void;
  (e: 'refresh'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const breakdownDialogVisible = ref(false);
const selectedTransaction = ref<GetTransactionResponse | null>(null);

const columns = [
  { name: 'id', required: true, label: 'ID', align: 'center' as const, field: 'id', sortable: true },
  { name: 'account_name', label: 'Account Name', align: 'center' as const, field: (row: GetTransactionResponse) => row.account?.name || 'N/A', sortable: true },
  { name: 'amount', label: 'Amount', align: 'right' as const, field: 'amount', sortable: true, format: (val: number) => `$${val.toFixed(2)}` },
  { name: 'description', label: 'Description', align: 'left' as const, field: 'description', sortable: true },
  { name: 'transacted_at', label: 'Date', align: 'center' as const, field: 'transacted_at', sortable: true },
  { name: 'payee', label: 'Payee', align: 'left' as const, field: 'payee', sortable: true },
  { name: 'pending', label: 'Pending', align: 'center' as const, field: 'pending', sortable: true },
  { name: 'budget_name', label: 'Budget', align: 'center' as const, field: 'budget_name', sortable: true },
  { name: 'actions', label: 'Actions', align: 'center' as const, field: 'actions', sortable: false }
];

function onPaginationChange(newPagination: Props['pagination']) {
  emit('update:pagination', newPagination);
}

function onRefresh() {
  emit('refresh');
}

function onBudgetUpdated() {
  emit('refresh');
}

function openBreakdown(transaction: GetTransactionResponse) {
  selectedTransaction.value = transaction;
  breakdownDialogVisible.value = true;
}

function onBreakdownSaved() {
  emit('refresh');
}
</script>

<template>
  <q-page>
    <q-table
      title="Recent Transactions"
      :rows="transactions"
      :columns="columns"
      :loading="loading"
      :pagination="pagination"
      row-key="transaction_id"
      @update:pagination="onPaginationChange"
    >
      <template v-slot:top-right>
        <q-btn
          color="primary"
          icon="refresh"
          unelevated
          :loading="loading"
          @click="onRefresh"
        />
      </template>
     
      <template v-slot:body-cell-pending="props">
        <q-td :props="props">
          <q-badge :color="props.row.pending ? 'orange' : 'green'">
            {{ props.row.pending ? 'Pending' : 'Posted' }}
          </q-badge>
        </q-td>
      </template>

      <template v-slot:body-cell-budget_name="{ row }">
        <q-td class="text-center">
          <!-- Show disabled chip if transaction is split -->
          <q-chip
            v-if="row.is_split"
            color="grey"
            text-color="white"
            icon="info"
          >
            Split Transaction
            <q-tooltip>
              This transaction has been split into line items. 
              Edit budgets for individual items in the breakdown.
            </q-tooltip>
          </q-chip>
          
          <!-- Show budget assignment if not split -->
          <budget-assignment-cell
            v-else
            :transaction="row"
            @updated="onBudgetUpdated"
          />
        </q-td>
      </template>

      <template v-slot:body-cell-actions="{ row }">
        <q-td class="text-center">
          <q-btn
            flat
            round
            dense
            :icon="row.is_split ? 'edit' : 'receipt_long'"
            :color="row.is_split ? 'secondary' : 'primary'"
            size="sm"
            @click="openBreakdown(row)"
          >
            <q-tooltip>
              {{ row.is_split ? 'Edit breakdown' : 'Break down transaction' }}
            </q-tooltip>
          </q-btn>
        </q-td>
      </template>
    </q-table>

    <!-- Breakdown Dialog -->
    <transaction-breakdown-dialog
      v-if="selectedTransaction"
      v-model:visible="breakdownDialogVisible"
      :transaction="selectedTransaction"
      @saved="onBreakdownSaved"
    />
  </q-page>
</template>
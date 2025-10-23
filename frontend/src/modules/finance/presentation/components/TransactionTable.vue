<script setup lang="ts">
import { ref } from 'vue';
import type { TransactionResponse } from 'src/api';
import BudgetAssignmentCell from './BudgetAssignmentCell.vue';
import TransactionBreakdownDialog from './breakdown/TransactionBreakdownDialog.vue';
import TransactionTypeDialog from './actions/TransactionTypeDialog.vue';

interface Props {
  transactions: TransactionResponse[];
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
const typeDialogVisible = ref(false);
const selectedTransaction = ref<TransactionResponse | null>(null);

const columns = [
  { name: 'id', required: true, label: 'ID', align: 'center' as const, field: 'id', sortable: true },
  { name: 'org_domain', label: 'Organization', align: 'center' as const, field: (row: TransactionResponse) => row.account?.org.name || 'N/A', sortable: true },
  { name: 'account_name', label: 'Account Name', align: 'center' as const, field: (row: TransactionResponse) => row.account?.name || 'N/A', sortable: true },
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

function openBreakdown(transaction: TransactionResponse) {
  selectedTransaction.value = transaction;
  breakdownDialogVisible.value = true;
}

function openTypeDialog(transaction: TransactionResponse) {
  selectedTransaction.value = transaction;
  typeDialogVisible.value = true;
}

function onBreakdownSaved() {
  emit('refresh');
}

function onTypeSaved() {
  emit('refresh');
}
</script>

<template>
  <q-card flat bordered class="transaction-table-card">
    <q-card-section class="q-pa-none">
      <q-table
        flat
        :rows="transactions"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        row-key="transaction_id"
        class="transaction-table"
        @update:pagination="onPaginationChange"
      >
        <template v-slot:top>
          <div class="row items-center justify-between full-width q-pa-md">
            <div class="row items-center q-gutter-sm">
              <q-icon name="account_balance" size="28px" color="primary" />
              <span class="text-h5 text-white">Recent Transactions</span>
            </div>
            <q-btn
              flat
              round
              icon="refresh"
              color="primary"
              :loading="loading"
              @click="onRefresh"
            >
              <q-tooltip>Refresh</q-tooltip>
            </q-btn>
          </div>
        </template>
       
        <template v-slot:body-cell-amount="props">
          <q-td :props="props" class="text-right">
            <span 
              class="text-weight-medium"
              :class="props.row.amount < 0 ? 'text-negative' : 'text-positive'"
            >
              {{ props.value }}
            </span>
          </q-td>
        </template>

        <template v-slot:body-cell-pending="props">
          <q-td :props="props">
            <q-badge 
              :color="props.row.pending ? 'orange' : 'positive'"
              text-color="white"
            >
              {{ props.row.pending ? 'Pending' : 'Posted' }}
            </q-badge>
          </q-td>
        </template>

        <template v-slot:body-cell-budget_name="{ row }">
          <q-td class="text-center">
            <q-chip
              v-if="row.is_split"
              color="grey-7"
              text-color="white"
              icon="call_split"
              size="sm"
            >
              Split
              <q-tooltip>
                This transaction has been split into line items. 
                Edit budgets for individual items in the breakdown.
              </q-tooltip>
            </q-chip>
            
            <budget-assignment-cell
              v-else
              :transaction="row"
              @updated="onBudgetUpdated"
            />
          </q-td>
        </template>

        <template v-slot:body-cell-actions="{ row }">
          <q-td class="text-center">
            <q-btn-group flat>
              <q-btn
                flat
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

              <q-btn
                flat
                dense
                icon="label"
                color="accent"
                size="sm"
                @click="openTypeDialog(row)"
              >
                <q-tooltip>Mark transaction type</q-tooltip>
              </q-btn>
            </q-btn-group>
          </q-td>
        </template>
      </q-table>
    </q-card-section>

    <transaction-breakdown-dialog
      v-if="selectedTransaction"
      v-model:visible="breakdownDialogVisible"
      :transaction="selectedTransaction"
      @saved="onBreakdownSaved"
    />

    <transaction-type-dialog
      v-model:visible="typeDialogVisible"
      :transaction="selectedTransaction"
      @saved="onTypeSaved"
    />
  </q-card>
</template>

<style scoped>
.transaction-table-card {
  background: #2a2d35;
  border-color: #3a3d45;
}

.transaction-table :deep(.q-table__top) {
  background: #2a2d35;
  border-bottom: 1px solid #3a3d45;
}

.transaction-table :deep(thead tr) {
  background: #1e2027;
}

.transaction-table :deep(th) {
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.5px;
}

.transaction-table :deep(tbody tr) {
  background: #2a2d35;
  transition: all 0.2s;
}

.transaction-table :deep(tbody tr:hover) {
  background: #323540;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.transaction-table :deep(td) {
  color: #ffffff;
  border-color: #3a3d45;
}

.transaction-table :deep(.q-table__bottom) {
  background: #2a2d35;
  border-top: 1px solid #3a3d45;
  color: #ffffff;
}
</style>
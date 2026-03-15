<script setup lang="ts">
import { ref, watch } from 'vue'
import type { TransactionResponse } from 'src/api'
import BudgetAssignmentCell from './BudgetAssignmentCell.vue'
import EllipsisCell from './EllipsisCell.vue'
import TransactionActionButtons from './TransactionActionButtons.vue'
import TransactionDialogs from './TransactionDialogs.vue'
import TransactionTableHeader from './TransactionTableHeader.vue'
import { transactionTableColumns } from './transactionTableColumns'
import { useTransactionDialogs } from '../composables/useTransactionDialogs'

interface Props {
  transactions: TransactionResponse[]
  pagination: {
    page: number
    rowsPerPage: number
    rowsNumber: number
    sortBy: string
    descending: boolean
  }
  loading?: boolean
  month: number
  year: number
}

interface Emits {
  (_event: 'update:pagination', _value: Props['pagination']): void
  (_event: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const localPagination = ref({ ...props.pagination })
watch(
  () => props.pagination,
  (newVal) => {
    localPagination.value = { ...newVal }
  },
  { deep: true },
)

const {
  breakdownDialogVisible,
  typeDialogVisible,
  ruleDialogVisible,
  selectedTransaction,
  openBreakdown,
  openTypeDialog,
  openRuleDialog,
  onDialogSaved,
} = useTransactionDialogs(() => emit('refresh'))

function onPaginationChange(requestProps: { pagination: Props['pagination'] }) {
  emit('update:pagination', requestProps.pagination)
}
</script>

<template>
  <q-card flat bordered class="transaction-table-card">
    <q-card-section class="q-pa-none">
      <q-table
        flat
        dense
        :rows="transactions"
        :columns="transactionTableColumns"
        :loading="loading"
        v-model:pagination="localPagination"
        :rows-per-page-options="[10, 20, 50, 100]"
        row-key="transaction_id"
        class="transaction-table"
        @request="onPaginationChange"
      >
        <template v-slot:top>
          <transaction-table-header :loading="loading" @refresh="emit('refresh')" />
        </template>

        <template v-slot:body-cell-description="cellProps">
          <ellipsis-cell :cell-props="cellProps" :tooltip-threshold="25" />
        </template>
        <template v-slot:body-cell-payee="cellProps">
          <ellipsis-cell :cell-props="cellProps" :tooltip-threshold="18" />
        </template>
        <template v-slot:body-cell-account_name="cellProps">
          <ellipsis-cell :cell-props="cellProps" :tooltip-threshold="16" />
        </template>
        <template v-slot:body-cell-org_name="cellProps">
          <ellipsis-cell :cell-props="cellProps" :tooltip-threshold="14" />
        </template>

        <template v-slot:body-cell-pending="cellProps">
          <q-td :props="cellProps" class="text-center">
            <q-badge :color="cellProps.row.pending ? 'warning' : 'positive'" dense>
              {{ cellProps.row.pending ? 'Pending' : 'Posted' }}
            </q-badge>
          </q-td>
        </template>

        <template v-slot:body-cell-amount="cellProps">
          <q-td :props="cellProps" class="text-right">
            <span
              class="text-weight-medium"
              :class="cellProps.row.amount < 0 ? 'text-negative' : 'text-positive'"
            >
              {{ cellProps.value }}
            </span>
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
              dense
            >
              Split
              <q-tooltip>Transaction split into line items</q-tooltip>
            </q-chip>
            <budget-assignment-cell v-else :transaction="row" @updated="onDialogSaved" />
          </q-td>
        </template>

        <template v-slot:body-cell-actions="{ row }">
          <transaction-action-buttons
            :row="row"
            @breakdown="openBreakdown"
            @type="openTypeDialog"
            @rule="openRuleDialog"
          />
        </template>
      </q-table>
    </q-card-section>

    <transaction-dialogs
      :selected-transaction="selectedTransaction"
      v-model:breakdown-dialog-visible="breakdownDialogVisible"
      v-model:type-dialog-visible="typeDialogVisible"
      v-model:rule-dialog-visible="ruleDialogVisible"
      :month="month"
      :year="year"
      @saved="onDialogSaved"
    />
  </q-card>
</template>
<style scoped src="./TransactionTable.css"></style>
<style src="./TransactionTableGlobal.css"></style>

<script setup lang="ts">
import { useQuasar } from 'quasar'
import type { TransactionResponse } from 'src/api'
import { useTransactionBreakdown } from '../../composables/useTransactionBreakdown'
import LineItemForm from './LineItemForm.vue'
import LineItemList from './LineItemList.vue'

interface Props {
  transaction: TransactionResponse
  visible: boolean
}

interface Emits {
  (_event: 'update:visible', _value: boolean): void
  (_event: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const $q = useQuasar()

const {
  lineItems,
  showAddForm,
  editingItemIndex,
  isExistingBreakdown,
  transactionAbsAmount,
  isExpense,
  totalAllocated,
  remaining,
  isBalanced,
  editingItem,
  maxAmountForForm,
  editLineItem,
  quickAddRemaining,
  addLineItem,
  deleteLineItem,
  saveBreakdown,
  cancel,
} = useTransactionBreakdown(
  () => props.transaction,
  () => props.visible,
  () => emit('saved'),
  () => emit('update:visible', false),
)
</script>

<template>
  <q-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    :maximized="$q.screen.lt.sm"
  >
    <q-card
      class="dialog-card transaction-breakdown-dialog"
      :style="$q.screen.lt.sm ? '' : 'min-width: 600px; max-width: 800px; width: 90vw;'"
    >
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">{{ isExistingBreakdown ? 'Edit' : 'Break Down' }} Transaction</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="cancel" />
      </q-card-section>

      <q-card-section>
        <!-- Transaction Info -->
        <div class="q-mb-md q-pa-md dialog-info-section">
          <div class="text-subtitle1">{{ transaction.description }}</div>
          <div class="text-subtitle2 text-grey-7">
            {{ transaction.payee }} • {{ transaction.transacted_at }}
          </div>
          <div class="text-h6 q-mt-sm" :class="isExpense ? 'text-negative' : 'text-positive'">
            Total: ${{ transactionAbsAmount.toFixed(2) }}
            <q-badge :color="isExpense ? 'negative' : 'positive'" class="q-ml-sm">
              {{ isExpense ? 'Expense' : 'Income' }}
            </q-badge>
          </div>
        </div>

        <!-- Balance Summary -->
        <div
          class="row q-mb-md q-pa-md rounded"
          :class="isBalanced ? 'bg-positive text-white' : 'bg-warning'"
        >
          <div class="col">
            <div class="text-caption">Allocated</div>
            <div class="text-h6">${{ totalAllocated.toFixed(2) }}</div>
          </div>
          <div class="col">
            <div class="text-caption">Remaining</div>
            <div class="text-h6">${{ remaining.toFixed(2) }}</div>
          </div>
          <div class="col">
            <div class="text-caption">Status</div>
            <div class="text-h6">
              <q-icon :name="isBalanced ? 'check_circle' : 'warning'" />
              {{ isBalanced ? 'Balanced' : 'Unbalanced' }}
            </div>
          </div>
        </div>

        <!-- Line Items List -->
        <line-item-list :items="lineItems" @edit="editLineItem" @delete="deleteLineItem" />

        <!-- Quick Actions -->
        <div class="row q-gutter-sm q-mt-md">
          <q-btn
            v-if="!showAddForm"
            color="primary"
            icon="add"
            label="Add Item"
            @click="showAddForm = true"
          />
          <q-btn
            v-if="remaining > 0.01 && !showAddForm"
            color="secondary"
            outline
            label="Add Remaining"
            @click="quickAddRemaining"
          />
        </div>

        <!-- Add/Edit Form -->
        <line-item-form
          v-if="showAddForm"
          :item="editingItem"
          :max-amount="maxAmountForForm"
          @submit="addLineItem"
          @cancel="showAddForm = false; editingItemIndex = null"
        />
      </q-card-section>

      <q-card-actions align="right" class="dialog-actions">
        <q-btn flat label="Cancel" class="btn-cancel" @click="cancel" />
        <q-btn
          flat
          :label="isExistingBreakdown ? 'Update Breakdown' : 'Save Breakdown'"
          class="btn-submit"
          :disable="!isBalanced || lineItems.length === 0"
          @click="saveBreakdown"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

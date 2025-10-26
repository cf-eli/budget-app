<script setup lang="ts">
import { ref } from 'vue'
import type { TransactionResponse, TransactionTypeEnum } from 'src/api'
import { apiV1TransactionsTransactionIdTypeMarkTransactionTypeEndpoint } from 'src/api'

interface Props {
  transaction: TransactionResponse | null
  visible: boolean
}

interface Emits {
  (_event: 'update:visible', _value: boolean): void
  (_event: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const loading = ref(false)

const transactionTypeOptions: { label: string; value: TransactionTypeEnum; description: string }[] =
  [
    { label: 'Transfer', value: 'transfer', description: 'Money moved between accounts' },
    { label: 'Credit Payment', value: 'credit_payment', description: 'Credit card payment' },
    { label: 'Loan Payment', value: 'loan_payment', description: 'Loan or mortgage payment' },
  ]
const excludeFromBudget = ref(true)
const selectedType = ref<TransactionTypeEnum | null>(null)

async function saveType() {
  if (!props.transaction || !selectedType.value) {
    return
  }

  loading.value = true
  try {
    await apiV1TransactionsTransactionIdTypeMarkTransactionTypeEndpoint({
      path: {
        transaction_id: props.transaction.id,
      },
      body: {
        transaction_type: selectedType.value,
        exclude_from_budget: excludeFromBudget.value,
      },
    })

    emit('saved')
    emit('update:visible', false)
  } catch (error) {
    console.error('Error marking transaction type:', error)
    alert('Failed to mark transaction type. Please try again.')
  } finally {
    loading.value = false
  }
}

function cancel() {
  emit('update:visible', false)
  selectedType.value = null
  excludeFromBudget.value = true
}
</script>

<template>
  <q-dialog :model-value="visible" @update:model-value="emit('update:visible', $event)">
    <q-card class="dialog-card" style="min-width: 400px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Mark Transaction Type</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="cancel" />
      </q-card-section>

      <q-card-section v-if="transaction">
        <!-- Transaction Info -->
        <div class="q-mb-md q-pa-md dialog-info-section">
          <div class="text-subtitle1">{{ transaction.description }}</div>
          <div class="text-subtitle2 text-grey-7">
            {{ transaction.payee }} • ${{ Math.abs(transaction.amount).toFixed(2) }}
          </div>
        </div>

        <!-- Transaction Type Selection -->
        <div class="text-subtitle2 q-mb-sm">Select Transaction Type:</div>
        <q-list bordered separator class="dialog-list">
          <q-item
            v-for="option in transactionTypeOptions"
            :key="option.value"
            clickable
            v-ripple
            :active="selectedType === option.value"
            @click="selectedType = option.value"
          >
            <q-item-section>
              <q-item-label>{{ option.label }}</q-item-label>
              <q-item-label caption>{{ option.description }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-radio
                :model-value="selectedType"
                :val="option.value"
                @update:model-value="selectedType = $event"
              />
            </q-item-section>
          </q-item>
        </q-list>

        <!-- Exclude from Budget Option -->
        <div class="q-mt-md">
          <q-checkbox v-model="excludeFromBudget" label="Exclude from budget calculations" class="dialog-checkbox" />
          <div class="text-caption text-grey-7 q-pl-lg">
            This transaction will be hidden from the transaction list and not counted in budgets.
          </div>
        </div>
      </q-card-section>

      <q-card-actions align="right" class="dialog-actions">
        <q-btn flat label="Cancel" class="btn-cancel" @click="cancel" />
        <q-btn
          flat
          label="Mark Transaction"
          class="btn-submit"
          :disable="!selectedType"
          :loading="loading"
          @click="saveType"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

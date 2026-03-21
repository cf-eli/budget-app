<script setup lang="ts">
import type { TransactionResponse } from 'src/api'
import { useTransactionTypeMarking } from '../../composables/useTransactionTypeMarking'

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

const { loading, excludeFromBudget, selectedType, createRule, transactionTypeOptions, saveType, cancel } =
  useTransactionTypeMarking({
    getTransaction: () => props.transaction,
    onSaved: () => emit('saved'),
    onClose: () => emit('update:visible', false),
  })
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
            {{ transaction.payee }} &bull; ${{ Math.abs(transaction.amount).toFixed(2) }}
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

        <!-- Create Rule Option -->
        <div class="q-mt-md">
          <q-checkbox
            v-model="createRule"
            label="Apply to future matching transactions"
            class="dialog-checkbox"
            :disable="!selectedType"
          />
          <div class="text-caption text-grey-7 q-pl-lg">
            Automatically mark future transactions from
            "{{ transaction.payee || transaction.description }}" the same way.
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

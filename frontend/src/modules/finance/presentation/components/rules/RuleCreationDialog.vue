<script setup lang="ts">
import type { TransactionResponse } from 'src/api'
import { useRuleCreation } from '../../composables/useRuleCreation'
import RuleConditionForm from './RuleConditionForm.vue'

interface Props {
  transaction: TransactionResponse | null
  visible: boolean
  month: number
  year: number
}

interface Emits {
  (_event: 'update:visible', _value: boolean): void
  (_event: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const {
  ruleName,
  targetBudgetId,
  targetTransactionType,
  targetExcludeFromBudget,
  transactionTypeOptions,
  conditions,
  loading,
  canSave,
  budgetStore,
  addCondition,
  updateCondition,
  removeCondition,
  saveRule,
  cancel,
} = useRuleCreation({
  getTransaction: () => props.transaction,
  getVisible: () => props.visible,
  month: () => props.month,
  year: () => props.year,
  onSaved: () => emit('saved'),
  onClose: () => emit('update:visible', false),
})
</script>

<template>
  <q-dialog :model-value="visible" @update:model-value="emit('update:visible', $event)">
    <q-card class="dialog-card" style="min-width: 600px; max-width: 800px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Create Rule from Transaction</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="cancel" />
      </q-card-section>

      <q-card-section v-if="transaction">
        <div class="q-mb-md q-pa-md dialog-info-section">
          <div class="text-subtitle1">{{ transaction.description }}</div>
          <div class="text-subtitle2 text-grey-7">
            {{ transaction.payee }} | ${{ Math.abs(transaction.amount).toFixed(2) }} |
            {{ transaction.account?.name }}
          </div>
        </div>

        <q-input v-model="ruleName" label="Rule Name" dense outlined class="q-mb-md dialog-input" />

        <q-select
          v-model="targetBudgetId"
          :options="budgetStore.budgetOptions"
          emit-value
          map-options
          dense
          outlined
          clearable
          label="Assign to Budget (optional)"
          class="q-mb-md dialog-select"
        />

        <q-select
          v-model="targetTransactionType"
          :options="transactionTypeOptions"
          emit-value
          map-options
          dense
          outlined
          label="Mark as Transaction Type (optional)"
          class="q-mb-sm dialog-select"
        />
        <q-checkbox
          v-if="targetTransactionType"
          v-model="targetExcludeFromBudget"
          label="Exclude from budget"
          class="q-mb-md"
        />

        <div class="text-subtitle2 q-mb-sm">Conditions (all must match):</div>
        <div class="q-gutter-sm q-mb-md">
          <RuleConditionForm
            v-for="(cond, idx) in conditions"
            :key="idx"
            :condition="cond"
            :index="idx"
            @update="updateCondition"
            @remove="removeCondition"
          />
        </div>
        <q-btn flat dense icon="add" label="Add Condition" color="primary" @click="addCondition" />
      </q-card-section>

      <q-card-actions align="right" class="dialog-actions">
        <q-btn flat label="Cancel" class="btn-cancel" @click="cancel" />
        <q-btn
          flat
          label="Create Rule"
          class="btn-submit"
          :disable="!canSave"
          :loading="loading"
          @click="saveRule"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

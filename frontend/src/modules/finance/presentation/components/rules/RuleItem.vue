<script setup lang="ts">
import { computed } from 'vue'
import type { RuleResponse } from 'src/api'

interface Props {
  rule: RuleResponse
}

interface Emits {
  (_event: 'edit', _rule: RuleResponse): void
  (_event: 'delete', _ruleId: number): void
  (_event: 'toggle', _ruleId: number, _isActive: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const operatorLabels: Record<string, string> = {
  exact: '=',
  contains: 'contains',
  greater_than: '>',
  less_than: '<',
  range: 'between',
}

const fieldLabels: Record<string, string> = {
  payee: 'Payee',
  description: 'Description',
  amount: 'Amount',
  account_id: 'Account ID',
  account_name: 'Account',
  org_domain: 'Org Domain',
  org_name: 'Organization',
}

const typeLabels: Record<string, string> = {
  transfer: 'Transfer',
  credit_payment: 'Credit Payment',
  loan_payment: 'Loan Payment',
}

const actionSummary = computed(() => {
  const parts: string[] = []
  if (props.rule.target_budget_name) {
    parts.push(`Budget: ${props.rule.target_budget_name}`)
  }
  if (props.rule.target_transaction_type) {
    parts.push(`Mark as: ${typeLabels[props.rule.target_transaction_type] || props.rule.target_transaction_type}`)
  }
  return parts.join(' | ') || 'No action configured'
})

const conditionsSummary = computed(() => {
  return props.rule.conditions
    .map((c) => {
      const field = fieldLabels[c.field] || c.field
      const op = operatorLabels[c.operator] || c.operator
      if (c.operator === 'range') {
        return `${field} ${op} ${c.value}-${c.value2}`
      }
      return `${field} ${op} "${c.value}"`
    })
    .join(' AND ')
})
</script>

<template>
  <q-item class="q-pa-md" :class="{ 'bg-grey-9': !rule.is_active }">
    <q-item-section>
      <q-item-label class="text-weight-medium">
        {{ rule.name }}
        <q-badge v-if="!rule.is_active" color="grey" class="q-ml-sm">Inactive</q-badge>
      </q-item-label>
      <q-item-label caption class="text-grey-6 rule-conditions">
        {{ conditionsSummary }}
        <q-tooltip v-if="conditionsSummary.length > 60">{{ conditionsSummary }}</q-tooltip>
      </q-item-label>
      <q-item-label caption class="text-primary">
        {{ actionSummary }}
      </q-item-label>
    </q-item-section>

    <q-item-section side>
      <div class="row q-gutter-sm">
        <q-toggle
          :model-value="rule.is_active"
          size="sm"
          color="positive"
          @update:model-value="emit('toggle', rule.id, $event)"
        >
          <q-tooltip>{{ rule.is_active ? 'Active' : 'Inactive' }}</q-tooltip>
        </q-toggle>
        <q-btn flat round dense icon="edit" size="sm" @click="emit('edit', rule)">
          <q-tooltip>Edit rule</q-tooltip>
        </q-btn>
        <q-btn
          flat
          round
          dense
          icon="delete"
          size="sm"
          color="negative"
          @click="emit('delete', rule.id)"
        >
          <q-tooltip>Delete rule</q-tooltip>
        </q-btn>
      </div>
    </q-item-section>
  </q-item>
</template>

<style scoped>
.rule-conditions {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}
</style>

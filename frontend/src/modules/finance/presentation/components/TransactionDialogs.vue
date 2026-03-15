<script setup lang="ts">
import type { TransactionResponse } from 'src/api'
import TransactionBreakdownDialog from './breakdown/TransactionBreakdownDialog.vue'
import TransactionTypeDialog from './actions/TransactionTypeDialog.vue'
import RuleCreationDialog from './rules/RuleCreationDialog.vue'

interface Props {
  selectedTransaction: TransactionResponse | null
  breakdownDialogVisible: boolean
  typeDialogVisible: boolean
  ruleDialogVisible: boolean
  month: number
  year: number
}

interface Emits {
  (_event: 'update:breakdownDialogVisible', _value: boolean): void
  (_event: 'update:typeDialogVisible', _value: boolean): void
  (_event: 'update:ruleDialogVisible', _value: boolean): void
  (_event: 'saved'): void
}

defineProps<Props>()
defineEmits<Emits>()
</script>

<template>
  <transaction-breakdown-dialog
    v-if="selectedTransaction"
    :visible="breakdownDialogVisible"
    @update:visible="$emit('update:breakdownDialogVisible', $event)"
    :transaction="selectedTransaction"
    @saved="$emit('saved')"
  />
  <transaction-type-dialog
    :visible="typeDialogVisible"
    @update:visible="$emit('update:typeDialogVisible', $event)"
    :transaction="selectedTransaction"
    @saved="$emit('saved')"
  />
  <rule-creation-dialog
    :visible="ruleDialogVisible"
    @update:visible="$emit('update:ruleDialogVisible', $event)"
    :transaction="selectedTransaction"
    :month="month"
    :year="year"
    @saved="$emit('saved')"
  />
</template>

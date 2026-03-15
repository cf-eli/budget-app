<script setup lang="ts">
import { computed } from 'vue'
import type { RuleCondition, RuleFieldEnum, RuleOperatorEnum } from 'src/api'

interface Props {
  condition: RuleCondition
  index: number
}

interface Emits {
  (_event: 'update', _index: number, _condition: RuleCondition): void
  (_event: 'remove', _index: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const fieldOptions = [
  { label: 'Payee', value: 'payee' },
  { label: 'Description', value: 'description' },
  { label: 'Amount', value: 'amount' },
  { label: 'Account ID', value: 'account_id' },
  { label: 'Account Name', value: 'account_name' },
  { label: 'Organization Domain', value: 'org_domain' },
  { label: 'Organization Name', value: 'org_name' },
]

const textOperators = [
  { label: 'Exact match', value: 'exact' },
  { label: 'Contains', value: 'contains' },
]

const numericOperators = [
  { label: 'Equal to', value: 'exact' },
  { label: 'Greater than', value: 'greater_than' },
  { label: 'Less than', value: 'less_than' },
  { label: 'Between', value: 'range' },
]

const isNumericField = computed(() => props.condition.field === 'amount')
const isRangeOperator = computed(() => props.condition.operator === 'range')
const operatorOptions = computed(() => (isNumericField.value ? numericOperators : textOperators))

function updateField(value: RuleFieldEnum) {
  const newCondition = { ...props.condition, field: value }
  // Reset operator if switching between text/numeric fields
  if (value === 'amount' && !['exact', 'greater_than', 'less_than', 'range'].includes(newCondition.operator)) {
    newCondition.operator = 'exact' as RuleOperatorEnum
  } else if (value !== 'amount' && !['exact', 'contains'].includes(newCondition.operator)) {
    newCondition.operator = 'exact' as RuleOperatorEnum
  }
  emit('update', props.index, newCondition)
}

function updateOperator(value: RuleOperatorEnum) {
  emit('update', props.index, { ...props.condition, operator: value })
}

function updateValue(value: string | number) {
  emit('update', props.index, { ...props.condition, value })
}

function updateValue2(value: number | null) {
  emit('update', props.index, { ...props.condition, value2: value })
}
</script>

<template>
  <div class="row q-gutter-sm items-center">
    <q-select
      :model-value="condition.field"
      :options="fieldOptions"
      emit-value
      map-options
      dense
      outlined
      class="col-3 dialog-select"
      label="Field"
      @update:model-value="updateField"
    />
    <q-select
      :model-value="condition.operator"
      :options="operatorOptions"
      emit-value
      map-options
      dense
      outlined
      class="col-2 dialog-select"
      label="Operator"
      @update:model-value="updateOperator"
    />
    <q-input
      v-if="isNumericField"
      :model-value="condition.value"
      type="number"
      dense
      outlined
      class="col dialog-input"
      :label="isRangeOperator ? 'Min' : 'Value'"
      @update:model-value="updateValue"
    />
    <q-input
      v-else
      :model-value="condition.value"
      dense
      outlined
      class="col dialog-input"
      label="Value"
      @update:model-value="updateValue"
    />
    <q-input
      v-if="isRangeOperator"
      :model-value="condition.value2"
      type="number"
      dense
      outlined
      class="col-2 dialog-input"
      label="Max"
      @update:model-value="updateValue2"
    />
    <q-btn flat round dense icon="delete" color="negative" @click="emit('remove', index)">
      <q-tooltip>Remove condition</q-tooltip>
    </q-btn>
  </div>
</template>

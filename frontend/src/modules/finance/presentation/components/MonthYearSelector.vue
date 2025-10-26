<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: {
    month: number
    year: number
  }
}

interface Emits {
  (_e: 'update:modelValue', _value: { month: number; year: number }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const months = [
  { label: 'January', value: 1 },
  { label: 'February', value: 2 },
  { label: 'March', value: 3 },
  { label: 'April', value: 4 },
  { label: 'May', value: 5 },
  { label: 'June', value: 6 },
  { label: 'July', value: 7 },
  { label: 'August', value: 8 },
  { label: 'September', value: 9 },
  { label: 'October', value: 10 },
  { label: 'November', value: 11 },
  { label: 'December', value: 12 },
]

const currentYear = new Date().getFullYear()
const years = Array.from({ length: 10 }, (_, i) => currentYear - i + 2)

const selectedMonth = computed({
  get: () => props.modelValue.month,
  set: (value) => emit('update:modelValue', { month: value, year: props.modelValue.year }),
})

const selectedYear = computed({
  get: () => props.modelValue.year,
  set: (value) => emit('update:modelValue', { month: props.modelValue.month, year: value }),
})

function goToPreviousMonth() {
  const newMonth = props.modelValue.month === 1 ? 12 : props.modelValue.month - 1
  const newYear = props.modelValue.month === 1 ? props.modelValue.year - 1 : props.modelValue.year
  emit('update:modelValue', { month: newMonth, year: newYear })
}

function goToNextMonth() {
  const newMonth = props.modelValue.month === 12 ? 1 : props.modelValue.month + 1
  const newYear = props.modelValue.month === 12 ? props.modelValue.year + 1 : props.modelValue.year
  emit('update:modelValue', { month: newMonth, year: newYear })
}

function goToCurrentMonth() {
  const now = new Date()
  emit('update:modelValue', { month: now.getMonth() + 1, year: now.getFullYear() })
}

const displayText = computed(() => {
  const monthName = months.find((m) => m.value === props.modelValue.month)?.label || ''
  return `${monthName} ${props.modelValue.year}`
})
</script>

<template>
  <div class="month-year-selector row items-center q-gutter-sm">
    <q-btn
      flat
      round
      dense
      icon="chevron_left"
      color="primary"
      size="sm"
      @click="goToPreviousMonth"
    >
      <q-tooltip>Previous Month</q-tooltip>
    </q-btn>

    <div class="row items-center q-gutter-xs">
      <q-select
        v-model="selectedMonth"
        :options="months"
        option-value="value"
        option-label="label"
        emit-value
        map-options
        dense
        filled
        options-dense
        class="dialog-select"
        style="min-width: 120px"
      />
      <q-select
        v-model="selectedYear"
        :options="years"
        dense
        filled
        options-dense
        class="dialog-select"
        style="min-width: 90px"
      />
    </div>

    <q-btn flat round dense icon="today" color="primary" size="sm" @click="goToCurrentMonth">
      <q-tooltip>Current Month</q-tooltip>
    </q-btn>

    <q-btn
      flat
      round
      dense
      icon="chevron_right"
      color="primary"
      size="sm"
      @click="goToNextMonth"
    >
      <q-tooltip>Next Month</q-tooltip>
    </q-btn>

    <div class="text-subtitle2 text-grey-7 q-ml-sm">
      {{ displayText }}
    </div>
  </div>
</template>

<style scoped>
.month-year-selector {
  padding: 8px;
}
</style>

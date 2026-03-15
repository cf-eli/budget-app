<script setup lang="ts">
import type { TransactionResponse } from 'src/api'

interface Props {
  row: TransactionResponse
}

interface Emits {
  (_event: 'breakdown', _row: TransactionResponse): void
  (_event: 'type', _row: TransactionResponse): void
  (_event: 'rule', _row: TransactionResponse): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()
</script>

<template>
  <q-td class="text-center">
    <q-btn-group flat>
      <q-btn
        flat
        dense
        round
        :icon="row.is_split ? 'edit' : 'receipt_long'"
        :color="row.is_split ? 'secondary' : 'primary'"
        size="xs"
        @click="emit('breakdown', row)"
      >
        <q-tooltip>{{ row.is_split ? 'Edit breakdown' : 'Break down transaction' }}</q-tooltip>
      </q-btn>
      <q-btn flat dense round icon="label" color="accent" size="xs" @click="emit('type', row)">
        <q-tooltip>Mark transaction type</q-tooltip>
      </q-btn>
      <q-btn flat dense round icon="rule" color="info" size="xs" @click="emit('rule', row)">
        <q-tooltip>Create rule from transaction</q-tooltip>
      </q-btn>
    </q-btn-group>
  </q-td>
</template>

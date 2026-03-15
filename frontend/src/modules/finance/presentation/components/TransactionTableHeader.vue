<script setup lang="ts">
interface Emits {
  (_event: 'refresh'): void
}

interface Props {
  loading?: boolean
}

defineProps<Props>()
const emit = defineEmits<Emits>()
</script>

<template>
  <div class="row items-center justify-between full-width q-pa-sm">
    <div class="row items-center q-gutter-sm">
      <q-icon name="account_balance" size="24px" color="primary" />
      <span class="text-h6 text-white">Recent Transactions</span>
    </div>
    <q-btn
      flat
      round
      icon="refresh"
      color="primary"
      size="sm"
      :loading="loading"
      @click="emit('refresh')"
    >
      <q-tooltip>Refresh</q-tooltip>
    </q-btn>
  </div>
</template>

<script setup lang="ts">
interface Props {
  cellProps: {
    value: string
    [key: string]: unknown
  }
  tooltipThreshold: number
}

defineProps<Props>()
</script>

<template>
  <q-td :props="cellProps" class="cell-ellipsis">
    <span>{{ cellProps.value }}</span>
    <q-tooltip v-if="cellProps.value && cellProps.value.length > tooltipThreshold">
      {{ cellProps.value }}
    </q-tooltip>
  </q-td>
</template>

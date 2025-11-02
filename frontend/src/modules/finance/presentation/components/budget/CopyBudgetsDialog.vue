<script setup lang="ts">
import { computed } from 'vue'
import { useQuasar } from 'quasar'

interface Props {
  targetMonth: number
  targetYear: number
  previousMonth: number
  previousYear: number
}

interface Emits {
  (_e: 'confirm'): void
  (_e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const $q = useQuasar()

// Format month name
const monthNames = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
]

const targetMonthName = computed(() => monthNames[props.targetMonth - 1])
const previousMonthName = computed(() => monthNames[props.previousMonth - 1])

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <q-card
    :style="
      $q.screen.lt.sm
        ? 'width: 100vw; max-width: 100vw;'
        : 'width: 500px; max-width: 90vw;'
    "
  >
    <q-card-section class="row items-center">
      <div class="text-h6">Copy Budgets</div>
      <q-space />
      <q-btn icon="close" flat round dense @click="handleCancel" />
    </q-card-section>

    <q-card-section>
      <p class="text-body1">
        Copy all budget items from <strong>{{ previousMonthName }} {{ previousYear }}</strong> to
        <strong>{{ targetMonthName }} {{ targetYear }}</strong>?
      </p>
      <p class="text-body2 text-grey-7 q-mt-md">
        This will copy all income, expense, flexible expense, and fund budget categories. Existing
        transaction assignments will not be copied.
      </p>
      <q-banner class="bg-info text-white q-mt-md" rounded dense>
        <template #avatar>
          <q-icon name="info" />
        </template>
        <div class="text-body2">
          <strong>Funds:</strong> Copied funds will automatically link to their existing master fund families. No manual linking required.
        </div>
      </q-banner>
    </q-card-section>

    <q-card-actions align="right" class="q-px-md q-pb-md">
      <q-btn flat label="Cancel" color="grey-7" @click="handleCancel" />
      <q-btn unelevated label="Copy Budgets" color="primary" @click="handleConfirm" />
    </q-card-actions>
  </q-card>
</template>

<style scoped>
.text-body1 {
  line-height: 1.6;
}
</style>

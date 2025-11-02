<script setup lang="ts">
import { ref } from 'vue'
import { useQuasar } from 'quasar'
import type { BudgetRequest } from 'src/api'
import { useDateSelectionStore } from 'src/modules/finance/presentation/stores/dateSelectionStore'

interface Emits {
  (_event: 'close'): void
  (_event: 'submit', _budget: BudgetRequest): void
}

const emit = defineEmits<Emits>()

const $q = useQuasar()
const dateStore = useDateSelectionStore()

const formData = ref({
  name: '',
  month_amount: 0,
  increment: 0,
  priority: 0,
  max: null as number | null,
})

const haveMax = ref(false)

function submitForm() {
  const budget: BudgetRequest = {
    name: formData.value.name,
    budget_type: 'fund',
    month_amount: formData.value.month_amount,
    increment: formData.value.increment,
    priority: formData.value.priority || 0,
    max: haveMax.value ? formData.value.max : null,
    month: dateStore.selectedMonth,
    year: dateStore.selectedYear,
  }

  emit('submit', budget)
}

function closeForm() {
  emit('close')
}
</script>

<template>
  <q-card class="dialog-card" :style="$q.screen.lt.sm ? 'width: 100vw; max-width: 100vw;' : 'width: 400px; max-width: 90vw;'">
    <q-card-section>
      <div class="text-h6">Add New Fund</div>
    </q-card-section>

    <q-card-section>
      <q-form @submit.prevent="submitForm">
        <q-input
          v-model="formData.name"
          label="Name"
          filled
          class="q-mb-md dialog-input"
          :rules="[(val) => !!val || 'Name is required']"
        />

        <q-input
          v-model.number="formData.month_amount"
          type="number"
          label="Starting Balance"
          filled
          class="q-mb-md dialog-input"
          prefix="$"
          hint="Initial balance for new fund (leave at 0 if starting fresh)"
        />

        <q-input
          v-model.number="formData.increment"
          type="number"
          label="Increment"
          filled
          class="q-mb-md dialog-input"
          prefix="$"
          :rules="[
            (val) => (val !== null && val !== '') || 'Increment is required',
            (val) => val > 0 || 'Must be positive',
          ]"
        />

        <q-input
          v-model.number="formData.priority"
          type="number"
          label="Priority"
          hint="Leave at 0 to add to end of list"
          filled
          class="q-mb-md dialog-input"
        />

        <q-checkbox v-model="haveMax" label="Have Max" class="q-mb-md dialog-checkbox" />

        <q-input
          v-if="haveMax"
          v-model.number="formData.max"
          type="number"
          label="Maximum"
          filled
          class="q-mb-md dialog-input"
          prefix="$"
        />

        <div class="row justify-end q-mt-md dialog-actions">
          <q-btn flat label="Cancel" class="btn-cancel" @click="closeForm" />
          <q-btn flat label="Add" class="btn-submit" type="submit" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

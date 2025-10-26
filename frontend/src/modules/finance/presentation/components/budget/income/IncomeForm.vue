<script setup lang="ts">
import { ref } from 'vue'
import { useQuasar } from 'quasar'
import type { BudgetRequest } from 'src/api'

interface Emits {
  (_event: 'close'): void
  (_event: 'submit', _budget: BudgetRequest): void
}

const emit = defineEmits<Emits>()

const $q = useQuasar()

const formData = ref({
  name: '',
  fixed: true,
  expected_amount: 0,
  min: null as number | null,
  max: null as number | null,
})

const now = new Date()
const currentMonth = now.getMonth() + 1
const currentYear = now.getFullYear()

function submitForm() {
  const budget: BudgetRequest = {
    name: formData.value.name,
    fixed: formData.value.fixed,
    budget_type: 'income',
    expected_amount: formData.value.expected_amount,
    min: formData.value.fixed ? null : formData.value.min,
    max: formData.value.fixed ? null : formData.value.max,
    month: currentMonth,
    year: currentYear,
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
      <div class="text-h6">Add Income Budget</div>
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

        <div class="q-mb-md flex justify-center">
          <q-btn-toggle
            v-model="formData.fixed"
            :options="[
              { label: 'Fixed', value: true },
              { label: 'Estimated', value: false },
            ]"
          />
        </div>

        <q-input
          v-model.number="formData.expected_amount"
          type="number"
          label="Expected Amount"
          filled
          class="q-mb-md dialog-input"
          prefix="$"
          :rules="[
            (val) => (val !== null && val !== '') || 'Amount is required',
            (val) => val > 0 || 'Must be positive',
          ]"
        />

        <div v-if="!formData.fixed">
          <q-input
            v-model.number="formData.min"
            type="number"
            label="Minimum"
            filled
            class="q-mb-md dialog-input"
            prefix="$"
          />
          <q-input
            v-model.number="formData.max"
            type="number"
            label="Maximum"
            filled
            class="q-mb-md dialog-input"
            prefix="$"
          />
        </div>

        <div class="row justify-end q-mt-md dialog-actions">
          <q-btn flat label="Cancel" class="btn-cancel" @click="closeForm" />
          <q-btn flat label="Add" class="btn-submit" type="submit" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

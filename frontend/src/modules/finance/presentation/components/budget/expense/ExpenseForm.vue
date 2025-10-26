<script setup lang="ts">
import { ref } from 'vue'
import type { BudgetRequest } from 'src/api'

interface Emits {
  (_event: 'close'): void
  (_event: 'submit', _budget: BudgetRequest): void
}

const emit = defineEmits<Emits>()

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
    budget_type: 'expense',
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
  <q-card style="width: 400px">
    <q-card-section>
      <div class="text-h6">Add New Expense</div>
    </q-card-section>

    <q-card-section>
      <q-form @submit.prevent="submitForm">
        <q-input
          v-model="formData.name"
          label="Name"
          filled
          class="q-mb-md"
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
          class="q-mb-md"
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
            class="q-mb-md"
            prefix="$"
          />
          <q-input
            v-model.number="formData.max"
            type="number"
            label="Maximum"
            filled
            class="q-mb-md"
            prefix="$"
          />
        </div>

        <div class="row justify-end q-mt-md">
          <q-btn flat label="Cancel" color="negative" @click="closeForm" />
          <q-btn flat label="Add" color="positive" type="submit" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

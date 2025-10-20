<script setup lang="ts">
import { ref } from 'vue';
import type { BudgetRequest } from 'src/api';

interface Emits {
  (e: 'close'): void;
  (e: 'submit', budget: BudgetRequest): void;
}

const emit = defineEmits<Emits>();

const formData = ref({
  name: '',
  current_amount: 0,
  increment: 0,
  priority: 0,
  max: null as number | null,
});

const haveMax = ref(false);

const now = new Date();
const currentMonth = now.getMonth() + 1;
const currentYear = now.getFullYear();

function submitForm() {
  const budget: BudgetRequest = {
    name: formData.value.name,
    budget_type: 'fund',
    current_amount: formData.value.current_amount,
    increment: formData.value.increment,
    priority: formData.value.priority || null,
    max: haveMax.value ? formData.value.max : null,
    month: currentMonth,
    year: currentYear,
  };

  emit('submit', budget);
}

function closeForm() {
  emit('close');
}
</script>

<template>
  <q-card style="width: 400px;">
    <q-card-section>
      <div class="text-h6">Add New Fund</div>
    </q-card-section>

    <q-card-section>
      <q-form @submit.prevent="submitForm">
        <q-input 
          v-model="formData.name" 
          label="Name" 
          filled 
          class="q-mb-md"
          :rules="[val => !!val || 'Name is required']"
        />

        <q-input 
          v-model.number="formData.current_amount" 
          type="number" 
          label="Current Amount" 
          filled 
          class="q-mb-md"
          prefix="$"
        />

        <q-input 
          v-model.number="formData.increment" 
          type="number" 
          label="Increment" 
          filled 
          class="q-mb-md"
          prefix="$"
          :rules="[
            val => val !== null && val !== '' || 'Increment is required',
            val => val > 0 || 'Must be positive'
          ]"
        />

        <q-input 
          v-model.number="formData.priority" 
          type="number" 
          label="Priority" 
          hint="Leave at 0 to add to end of list"
          filled 
          class="q-mb-md"
        />

        <q-checkbox v-model="haveMax" label="Have Max" class="q-mb-md" />

        <q-input 
          v-if="haveMax"
          v-model.number="formData.max" 
          type="number" 
          label="Maximum" 
          filled 
          class="q-mb-md"
          prefix="$"
        />

        <div class="row justify-end q-mt-md">
          <q-btn flat label="Cancel" color="negative" @click="closeForm" />
          <q-btn flat label="Add" color="positive" type="submit" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>
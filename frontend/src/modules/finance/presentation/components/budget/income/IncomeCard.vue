<script setup lang="ts">
import { ref } from 'vue';
import type { IncomeBudgetResponse, BudgetRequest } from 'src/api';
import IncomeItemSection from './IncomeItemSection.vue';
import IncomeForm from './IncomeForm.vue';

interface Props {
  incomes: IncomeBudgetResponse[];
}

interface Emits {
  (e: 'refresh'): void;
  (e: 'create', budget: BudgetRequest): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();

const formVisible = ref(false);

function openForm() {
  formVisible.value = true;
}

function showDetails(id: number) {
  console.log('Show details for income:', id);
}

async function handleFormSubmit(formData: BudgetRequest) {
  await emit('create', formData);
  formVisible.value = false;
}
</script>

<template>
  <q-card class="q-mb-lg shadow-2">
    <q-card-section class="row items-center">
      <q-icon name="attach_money" color="positive" size="md" class="q-mr-sm" />
      <div class="text-h5 text-primary">Income</div>
      <q-icon name="add_circle" color="positive" size="md" class="q-pl-xl cursor-pointer" @click="openForm" />
    </q-card-section>
    
    <q-separator />
    
    <q-card-section>
      <q-list dense>
        <q-item 
          v-for="income in incomes" 
          :key="income.id" 
          clickable 
          @click="showDetails(income.id)"
          class="hover-highlight"
        >
          <income-item-section :income="income" />
        </q-item>
        
        <q-item v-if="incomes.length === 0">
          <q-item-section class="text-center text-grey">
            No income budgets created yet
          </q-item-section>
        </q-item>
      </q-list>
    </q-card-section>

    <q-dialog v-model="formVisible">
      <income-form @submit="handleFormSubmit" @close="formVisible = false" />
    </q-dialog>
  </q-card>
</template>
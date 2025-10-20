<script setup lang="ts">
import { ref } from 'vue';
import type { ExpenseBudgetResponse, BudgetRequest } from 'src/api';
import ExpenseItemSection from './ExpenseItemSection.vue';
import ExpenseForm from './ExpenseForm.vue';

interface Props {
  expenses: ExpenseBudgetResponse[];
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
  console.log('Show details for expense:', id);
}

async function handleFormSubmit(formData: BudgetRequest) {
  await emit('create', formData);
  formVisible.value = false;
}
</script>

<template>
  <q-card class="q-mb-lg shadow-2">
    <q-card-section class="row items-center">
      <q-icon name="shopping_cart" color="negative" size="md" class="q-mr-sm" />
      <div class="text-h5 text-primary">Expenses</div>
      <q-icon name="add_circle" color="positive" size="md" class="q-pl-xl cursor-pointer" @click="openForm" />
    </q-card-section>
    
    <q-separator />
    
    <q-card-section>
      <q-list dense>
        <q-item 
          v-for="expense in expenses" 
          :key="expense.id" 
          clickable 
          @click="showDetails(expense.id)"
          class="hover-highlight"
        >
          <expense-item-section :expense="expense" />
        </q-item>
        
        <q-item v-if="expenses.length === 0">
          <q-item-section class="text-center text-grey">
            No expense budgets created yet
          </q-item-section>
        </q-item>
      </q-list>
    </q-card-section>

    <q-dialog v-model="formVisible">
      <expense-form @submit="handleFormSubmit" @close="formVisible = false" />
    </q-dialog>
  </q-card>
</template>
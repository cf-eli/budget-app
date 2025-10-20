<script setup lang="ts">
import { ref } from 'vue';
import type { FlexibleBudgetResponse, BudgetRequest } from 'src/api';
import FlexibleItemSection from './FlexibleItemSection.vue';
import FlexibleForm from './FlexibleForm.vue';

interface Props {
  flexibles: FlexibleBudgetResponse[];
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
  console.log('Show details for flexible:', id);
}

async function handleFormSubmit(formData: BudgetRequest) {
  await emit('create', formData);
  formVisible.value = false;
}
</script>

<template>
  <q-card class="q-mb-lg shadow-2">
    <q-card-section class="row items-center">
      <q-icon name="event" color="amber" size="md" class="q-mr-sm" />
      <div class="text-h5 text-primary">Flexibles</div>
      <q-icon name="add_circle" color="positive" size="md" class="q-pl-xl cursor-pointer" @click="openForm" />
    </q-card-section>
    
    <q-separator />
    
    <q-card-section>
      <q-list dense>
        <q-item 
          v-for="flexible in flexibles" 
          :key="flexible.id" 
          clickable 
          @click="showDetails(flexible.id)"
          class="hover-highlight"
        >
          <flexible-item-section :flexible="flexible" />
        </q-item>
        
        <q-item v-if="flexibles.length === 0">
          <q-item-section class="text-center text-grey">
            No flexible budgets created yet
          </q-item-section>
        </q-item>
      </q-list>
    </q-card-section>

    <q-dialog v-model="formVisible">
      <flexible-form @submit="handleFormSubmit" @close="formVisible = false" />
    </q-dialog>
  </q-card>
</template>
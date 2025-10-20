<script setup lang="ts">
import { ref } from 'vue';
import type { FundBudgetResponse, BudgetRequest } from 'src/api';
import FundItemSection from './FundItemSection.vue';
import FundForm from './FundForm.vue';

interface Props {
  funds: FundBudgetResponse[];
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
  console.log('Show details for fund:', id);
}

async function handleFormSubmit(formData: BudgetRequest) {
  await emit('create', formData);
  formVisible.value = false;
}
</script>

<template>
  <q-card class="q-mb-lg shadow-2">
    <q-card-section class="row items-center">
      <q-icon name="savings" color="teal" size="md" class="q-mr-sm" />
      <div class="text-h5 text-primary">Funds</div>
      <q-icon name="add_circle" color="positive" size="md" class="q-pl-xl cursor-pointer" @click="openForm" />
    </q-card-section>
    
    <q-separator />
    
    <q-card-section>
      <q-list dense>
        <q-item 
          v-for="fund in funds" 
          :key="fund.id" 
          clickable 
          @click="showDetails(fund.id)"
          class="hover-highlight"
        >
          <fund-item-section :fund="fund" />
        </q-item>
        
        <q-item v-if="funds.length === 0">
          <q-item-section class="text-center text-grey">
            No fund budgets created yet
          </q-item-section>
        </q-item>
      </q-list>
    </q-card-section>

    <q-dialog v-model="formVisible">
      <fund-form @submit="handleFormSubmit" @close="formVisible = false" />
    </q-dialog>
  </q-card>
</template>
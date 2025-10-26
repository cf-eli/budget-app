<script setup lang="ts">
import { ref } from 'vue'
import type { FundBudgetResponse, BudgetRequest } from 'src/api'
import FundItemSection from './FundItemSection.vue'
import FundForm from './FundForm.vue'

interface Props {
  funds: FundBudgetResponse[]
}

interface Emits {
  (_event: 'refresh'): void
  (_event: 'create', _budget: BudgetRequest): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const formVisible = ref(false)

function openForm() {
  formVisible.value = true
}

function showDetails(id: number) {
  console.log('Show details for fund:', id)
}

async function handleFormSubmit(formData: BudgetRequest) {
  await emit('create', formData)
  formVisible.value = false
}
</script>

<template>
  <q-card flat bordered class="budget-category-card q-mb-lg">
    <q-card-section class="row items-center justify-between category-header">
      <div class="row items-center q-gutter-sm">
        <q-icon name="savings" size="28px" color="teal" />
        <span class="text-h5 text-white">Funds</span>
      </div>
      <q-btn flat round icon="add" color="positive" size="md" @click="openForm">
        <q-tooltip>Add Fund</q-tooltip>
      </q-btn>
    </q-card-section>

    <q-separator color="grey-8" />

    <q-card-section class="category-items-section">
      <q-list separator class="q-pa-none">
        <q-item
          v-for="fund in funds"
          :key="fund.id"
          clickable
          class="q-pa-none"
          @click="showDetails(fund.id)"
        >
          <q-item-section class="q-pa-none">
            <fund-item-section :fund="fund" />
          </q-item-section>
        </q-item>
      </q-list>

      <q-card v-if="funds.length === 0" flat class="empty-state-card text-center">
        <q-card-section>
          <q-icon name="inbox" size="64px" color="grey-6" />
          <div class="text-subtitle1 text-grey-6 q-mt-md">No funds yet</div>
          <q-btn outline color="primary" label="Add Fund" class="q-mt-md" @click="openForm" />
        </q-card-section>
      </q-card>
    </q-card-section>

    <q-dialog v-model="formVisible">
      <fund-form @submit="handleFormSubmit" @close="formVisible = false" />
    </q-dialog>
  </q-card>
</template>

<style scoped>
.budget-category-card {
  background: #2a2d35;
  border-color: #3a3d45;
}

.category-header {
  background: #2a2d35;
  padding: 16px 20px;
}

.category-items-section {
  background: #1e2027;
  padding: 16px;
}

.empty-state-card {
  background: transparent;
  padding: 32px 24px;
}
</style>

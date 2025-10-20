<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { apiFinanceV1BudgetsNamesGetBudgetsNames } from 'src/api';


const loading = ref(false);
const budgetOptions = ref<BudgetOption[]>([]);
interface BudgetOption {
  label: string;
  value: number | null;
}
async function fetchBudgets() {
  loading.value = true;
  try {
    const response = await apiFinanceV1BudgetsNamesGetBudgetsNames();
   
    if (response.data) {
      budgetOptions.value = [
        { label: 'None', value: null },
        ...response.data.map((budget) => ({
          label: budget.name,
          value: budget.id,
        }))
      ];
    }
  } catch (error) {
    console.error('Error fetching budgets:', error);
  } finally {
    loading.value = false;
  }
}

interface LineItem {
  description: string;
  amount: number;
  quantity?: number;
  unit_price?: number;
  category?: string;
  budget_id?: number;
  notes?: string;
}

interface Props {
  item?: LineItem | null;
  maxAmount: number;
}

interface Emits {
  (e: 'submit', item: LineItem): void;
  (e: 'cancel'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const formData = ref<LineItem>({
  description: '',
  amount: 0,
  quantity: 1,
  category: '',
  notes: '',
});

const autoCalculate = ref(true);

watch(() => props.item, (newItem) => {
  if (newItem) {
    formData.value = { ...newItem };
  }
}, { immediate: true });

// Auto-calculate amount from quantity × unit_price
watch([() => formData.value.quantity, () => formData.value.unit_price], () => {
  if (autoCalculate.value && formData.value.quantity && formData.value.unit_price) {
    formData.value.amount = formData.value.quantity * formData.value.unit_price;
  }
});

function submit() {
  emit('submit', { ...formData.value });
  resetForm();
}

function cancel() {
  emit('cancel');
  resetForm();
}

function resetForm() {
  formData.value = {
    description: '',
    amount: 0,
    quantity: 1,
    category: '',
    notes: '',
  };
}

onMounted(() => {
  fetchBudgets();
});
</script>
<template>
  <q-card flat bordered class="q-mt-md">
    <q-card-section>
      <q-form @submit.prevent="submit">
        <div class="row q-col-gutter-md">
          <div class="col-12">
            <q-input
              v-model="formData.description"
              label="Description *"
              filled
              :rules="[val => !!val || 'Description is required']"
            />
          </div>

          <div class="col-4">
            <q-input
              v-model.number="formData.quantity"
              type="number"
              label="Quantity"
              filled
              step="0.01"
            />
          </div>

          <div class="col-4">
            <q-input
              v-model.number="formData.unit_price"
              type="number"
              label="Unit Price"
              filled
              prefix="$"
              step="0.01"
            />
          </div>

          <div class="col-4">
            <q-input
              v-model.number="formData.amount"
              type="number"
              label="Total Amount *"
              filled
              prefix="$"
              step="0.01"
              :rules="[
                val => !!val || 'Amount is required',
                val => val > 0 || 'Must be positive',
                val => val <= maxAmount || `Cannot exceed $${maxAmount.toFixed(2)}`
              ]"
            />
          </div>

          <div class="col-6">
            <q-input
              v-model="formData.category"
              label="Category"
              filled
            />
          </div>

          <div class="col-6">
            <q-select
              v-model="formData.budget_id"
              label="Assign to Budget"
              filled
              clearable
              emit-value
              map-options
              :options="budgetOptions"
            />
          </div>

          <div class="col-12">
            <q-input
              v-model="formData.notes"
              label="Notes"
              filled
              type="textarea"
              rows="2"
            />
          </div>
        </div>

        <div class="row justify-end q-mt-md q-gutter-sm">
          <q-btn flat label="Cancel" @click="cancel" />
          <q-btn color="primary" label="Add Item" type="submit" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>
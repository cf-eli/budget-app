<script setup lang="ts">
interface LineItem {
  id?: number;
  description: string;
  amount: number;
  quantity?: number;
  unit_price?: number;
  category?: string;
  budget_id?: number;
  notes?: string;
}

interface Props {
  items: LineItem[];
}

interface Emits {
  (e: 'edit', index: number): void;
  (e: 'delete', index: number): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();

const formatCurrency = (value: number) => `$${value.toFixed(2)}`;
</script>

<template>
  <div v-if="items.length > 0">
    <div class="text-subtitle2 q-mb-sm">Line Items ({{ items.length }})</div>
    <q-list bordered separator>
      <q-item v-for="(item, index) in items" :key="index">
        <q-item-section>
          <q-item-label>{{ item.description }}</q-item-label>
          <q-item-label caption>
            <span v-if="item.quantity && item.unit_price">
              {{ item.quantity }} × {{ formatCurrency(item.unit_price) }}
            </span>
            <span v-if="item.category" class="q-ml-sm">
              • {{ item.category }}
            </span>
          </q-item-label>
          <q-item-label caption v-if="item.notes">
            {{ item.notes }}
          </q-item-label>
        </q-item-section>

        <q-item-section side top>
          <div class="text-h6">{{ formatCurrency(item.amount) }}</div>
          <div v-if="item.budget_id" class="text-caption text-primary">
            Budget assigned
          </div>
        </q-item-section>

        <q-item-section side top>
          <div class="row q-gutter-xs">
            <q-btn
              flat
              round
              dense
              icon="edit"
              size="sm"
              @click="emit('edit', index)"
            />
            <q-btn
              flat
              round
              dense
              icon="delete"
              color="negative"
              size="sm"
              @click="emit('delete', index)"
            />
          </div>
        </q-item-section>
      </q-item>
    </q-list>
  </div>
  <div v-else class="text-center q-pa-md text-grey-7">
    No items added yet. Add items to break down this transaction.
  </div>
</template>
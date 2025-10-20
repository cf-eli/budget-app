<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { GetTransactionResponse } from 'src/api';
import { 
  apiFinanceV1TransactionsTransactionIdBreakdownGetBreakdown,
  apiFinanceV1TransactionsLineItemsLineItemIdUpdateLineItemEndpoint,
  apiFinanceV1TransactionsTransactionIdBreakdownCreateBreakdown,
  apiFinanceV1TransactionsLineItemsLineItemIdDeleteLineItemEndpoint,
  type CreateLineItemRequest 
} from 'src/api';
import LineItemForm from './LineItemForm.vue';
import LineItemList from './LineItemList.vue';

interface LineItem {
  id?: number;
  description: string;
  amount: number;
  quantity?: number | null;
  unit_price?: number | null;
  category?: string | null;
  budget_id?: number | null;
  notes?: string | null;
}

interface Props {
  transaction: GetTransactionResponse;
  visible: boolean;
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'saved'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const lineItems = ref<LineItem[]>([]);
const showAddForm = ref(false);
const editingItemIndex = ref<number | null>(null);
const isExistingBreakdown = ref(false);

// Work with absolute values for breakdown
const transactionAbsAmount = computed(() => Math.abs(props.transaction.amount));
const isExpense = computed(() => props.transaction.amount < 0);

// Calculate totals using absolute values
const totalAllocated = computed(() => 
  lineItems.value.reduce((sum, item) => sum + Math.abs(item.amount), 0)
);

const remaining = computed(() => 
  transactionAbsAmount.value - totalAllocated.value
);

const isBalanced = computed(() => 
  Math.abs(remaining.value) < 0.01
);

const suggestedFirstItem = computed(() => {
  if (lineItems.value.length === 0) {
    return {
      description: props.transaction.description || 'Item 1',
      amount: transactionAbsAmount.value, // Use absolute value
      quantity: 1,
    };
  }
  return null;
});

const editingItem = computed(() => {
  if (editingItemIndex.value !== null) {
    const item = lineItems.value[editingItemIndex.value];
    if (item) {
      return item;
    }
  }
  return suggestedFirstItem.value;
});

const maxAmountForForm = computed(() => {
  const editingItem = editingItemIndex.value !== null 
    ? lineItems.value[editingItemIndex.value] 
    : null;
  
  return editingItem 
    ? remaining.value + Math.abs(editingItem.amount)
    : remaining.value;
});

function editLineItem(index: number) {
  editingItemIndex.value = index;
  showAddForm.value = true;
}


function quickAddRemaining() {
  if (remaining.value > 0) {
    lineItems.value.push({
      description: `Item ${lineItems.value.length + 1}`,
      amount: remaining.value,
      quantity: 1,
    });
  }
}

// Track which items are new vs existing
const newLineItems = ref<LineItem[]>([]);
const deletedLineItemIds = ref<number[]>([]);

function addLineItem(item: LineItem) {
  const normalizedItem = {
    ...item,
    amount: Math.abs(item.amount)
  };
  
  if (editingItemIndex.value !== null) {
    lineItems.value[editingItemIndex.value] = normalizedItem;
    editingItemIndex.value = null;
  } else {
    lineItems.value.push(normalizedItem);
    // Track as new if it doesn't have an id
    if (!normalizedItem.id) {
      newLineItems.value.push(normalizedItem);
    }
  }
  showAddForm.value = false;
}

function deleteLineItem(index: number) {
  const item = lineItems.value[index];
  
  // If the item doesn't exist (out of bounds), do nothing
  if (!item) {
    return;
  }

  // If it has an id, track it for deletion on save
  if (item.id) {
    deletedLineItemIds.value.push(item.id);
  } else {
    // Remove from new items list if it was newly added
    const newItemIndex = newLineItems.value.findIndex(i => i === item);
    if (newItemIndex !== -1) {
      newLineItems.value.splice(newItemIndex, 1);
    }
  }
  
  lineItems.value.splice(index, 1);
}

async function saveBreakdown() {
  if (!isBalanced.value) {
    alert('Total must equal transaction amount');
    return;
  }

  try {
    if (isExistingBreakdown.value) {
      // UPDATE MODE: Update existing items, create new ones, delete removed ones
      
      // 1. Delete removed items
      for (const itemId of deletedLineItemIds.value) {
        await apiFinanceV1TransactionsLineItemsLineItemIdDeleteLineItemEndpoint({
          path: { line_item_id: itemId }
        });
      }

      // 2. Update existing items
      for (const item of lineItems.value) {
        if (item.id) {
          await apiFinanceV1TransactionsLineItemsLineItemIdUpdateLineItemEndpoint({
            path: { line_item_id: item.id },
            body: {
              description: item.description,
              amount: isExpense.value ? -Math.abs(item.amount) : Math.abs(item.amount),
              quantity: item.quantity ?? null,
              unit_price: item.unit_price ?? null,
              category: item.category ?? null,
              budget_id: item.budget_id ?? null,
              notes: item.notes ?? null,
            }
          });
        }
      }

      // 3. Create new items (items without an id)
      const itemsToCreate = lineItems.value.filter(item => !item.id);
      if (itemsToCreate.length > 0) {
        await apiFinanceV1TransactionsTransactionIdBreakdownCreateBreakdown({
          path: { transaction_id: props.transaction.id },
          body: {
            transaction_id: props.transaction.id,
            line_items: itemsToCreate.map(item => ({
              description: item.description,
              amount: isExpense.value ? -Math.abs(item.amount) : Math.abs(item.amount),
              quantity: item.quantity ?? null,
              unit_price: item.unit_price ?? null,
              category: item.category ?? null,
              budget_id: item.budget_id ?? null,
              notes: item.notes ?? null,
            }))
          }
        });
      }
    } else {
      // CREATE MODE: Create new breakdown with all items
      await apiFinanceV1TransactionsTransactionIdBreakdownCreateBreakdown({
        path: { transaction_id: props.transaction.id },
        body: {
          transaction_id: props.transaction.id,
          line_items: lineItems.value.map(item => ({
            description: item.description,
            amount: isExpense.value ? -Math.abs(item.amount) : Math.abs(item.amount),
            quantity: item.quantity ?? null,
            unit_price: item.unit_price ?? null,
            category: item.category ?? null,
            budget_id: item.budget_id ?? null,
            notes: item.notes ?? null,
          }))
        }
      });
    }

    emit('saved');
    emit('update:visible', false);
  } catch (error) {
    console.error('Error saving breakdown:', error);
    alert('Failed to save breakdown. Please try again.');
  }
}

function cancel() {
  emit('update:visible', false);
  lineItems.value = [];
  newLineItems.value = [];
  deletedLineItemIds.value = [];
  isExistingBreakdown.value = false;
}

// Load existing breakdown if transaction is already split
watch(() => props.visible, async (visible) => {
  if (visible && props.transaction.is_split) {
    try {
      const response = await apiFinanceV1TransactionsTransactionIdBreakdownGetBreakdown({
        path: { transaction_id: props.transaction.id }
      });
      
      // Convert amounts to absolute values for editing
      lineItems.value = (response.data?.line_items || []).map(item => ({
        ...item,
        amount: Math.abs(item.amount)
      }));
      
      isExistingBreakdown.value = true;
      newLineItems.value = [];
      deletedLineItemIds.value = [];
    } catch (error) {
      console.error('Error loading breakdown:', error);
    }
  } else if (visible) {
    // Reset for new breakdown
    lineItems.value = [];
    newLineItems.value = [];
    deletedLineItemIds.value = [];
    isExistingBreakdown.value = false;
  }
});
</script>

<template>
  <q-dialog :model-value="visible" @update:model-value="emit('update:visible', $event)">
    <q-card style="min-width: 600px; max-width: 800px;">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">
          {{ isExistingBreakdown ? 'Edit' : 'Break Down' }} Transaction
        </div>
        <q-space />
        <q-btn icon="close" flat round dense @click="cancel" />
      </q-card-section>

      <q-card-section>
        <!-- Transaction Info -->
        <div class="q-mb-md q-pa-md bg-grey-2 rounded">
          <div class="text-subtitle1">{{ transaction.description }}</div>
          <div class="text-subtitle2 text-grey-7">
            {{ transaction.payee }} • {{ transaction.transacted_at }}
          </div>
          <div class="text-h6 q-mt-sm" :class="isExpense ? 'text-negative' : 'text-positive'">
            Total: ${{ transactionAbsAmount.toFixed(2) }}
            <q-badge :color="isExpense ? 'negative' : 'positive'" class="q-ml-sm">
              {{ isExpense ? 'Expense' : 'Income' }}
            </q-badge>
          </div>
        </div>

        <!-- Balance Summary -->
        <div class="row q-mb-md q-pa-md rounded" :class="isBalanced ? 'bg-positive text-white' : 'bg-warning'">
          <div class="col">
            <div class="text-caption">Allocated</div>
            <div class="text-h6">${{ totalAllocated.toFixed(2) }}</div>
          </div>
          <div class="col">
            <div class="text-caption">Remaining</div>
            <div class="text-h6">${{ remaining.toFixed(2) }}</div>
          </div>
          <div class="col">
            <div class="text-caption">Status</div>
            <div class="text-h6">
              <q-icon :name="isBalanced ? 'check_circle' : 'warning'" />
              {{ isBalanced ? 'Balanced' : 'Unbalanced' }}
            </div>
          </div>
        </div>

        <!-- Line Items List -->
        <line-item-list 
          :items="lineItems"
          @edit="editLineItem"
          @delete="deleteLineItem"
        />

        <!-- Quick Actions -->
        <div class="row q-gutter-sm q-mt-md">
          <q-btn 
            v-if="!showAddForm"
            color="primary" 
            icon="add" 
            label="Add Item"
            @click="showAddForm = true"
          />
          <q-btn 
            v-if="remaining > 0.01 && !showAddForm"
            color="secondary" 
            outline
            label="Add Remaining"
            @click="quickAddRemaining"
          />
        </div>

        <!-- Add/Edit Form -->
        <line-item-form
          v-if="showAddForm"
          :item="editingItem"
          :max-amount="maxAmountForForm"
          @submit="addLineItem"
          @cancel="showAddForm = false; editingItemIndex = null"
        />
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Cancel" @click="cancel" />
        <q-btn 
          color="primary" 
          :label="isExistingBreakdown ? 'Update Breakdown' : 'Save Breakdown'"
          :disable="!isBalanced || lineItems.length === 0"
          @click="saveBreakdown"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
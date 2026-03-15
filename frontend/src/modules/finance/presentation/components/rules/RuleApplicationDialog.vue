<script setup lang="ts">
import { useRuleApplication } from '../../composables/useRuleApplication'
import { ruleApplicationColumns } from './ruleApplicationColumns'

interface Props {
  visible: boolean
  month: number
  year: number
}

interface Emits {
  (_event: 'update:visible', _value: boolean): void
  (_event: 'applied'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const {
  rulesStore,
  previewItems,
  overrideExisting,
  selectedIds,
  selectedCount,
  hasPreview,
  loadPreview,
  toggleSelection,
  selectAll,
  selectNone,
  applyRules,
  cancel,
} = useRuleApplication({
  visible: () => props.visible,
  month: () => props.month,
  year: () => props.year,
  onApplied: () => emit('applied'),
  onClose: () => emit('update:visible', false),
})
</script>

<template>
  <q-dialog :model-value="visible" @update:model-value="emit('update:visible', $event)">
    <q-card class="dialog-card" style="min-width: 700px; max-width: 900px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Apply Transaction Rules</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="cancel" />
      </q-card-section>

      <q-card-section>
        <div class="row items-center q-mb-md">
          <q-checkbox v-model="overrideExisting" label="Override existing assignments" />
          <q-btn flat dense label="Refresh" icon="refresh" class="q-ml-md" @click="loadPreview" />
          <q-space />
          <q-btn flat dense label="Select All" @click="selectAll" />
          <q-btn flat dense label="Select None" class="q-ml-sm" @click="selectNone" />
        </div>

        <q-banner v-if="rulesStore.previewLoading" class="bg-grey-8">
          <q-spinner-dots /> Loading preview...
        </q-banner>

        <q-banner v-else-if="!hasPreview" class="bg-grey-8">
          No transactions match any rules for this month.
        </q-banner>

        <q-table
          v-else
          :rows="previewItems"
          :columns="ruleApplicationColumns"
          row-key="transaction_id"
          flat
          dense
          dark
          :pagination="{ rowsPerPage: 10 }"
        >
          <template #body-cell-select="cellProps">
            <q-td :props="cellProps">
              <q-checkbox
                :model-value="selectedIds.has(cellProps.row.transaction_id)"
                @update:model-value="toggleSelection(cellProps.row.transaction_id)"
              />
            </q-td>
          </template>
          <template #body-cell-description="cellProps">
            <q-td :props="cellProps" class="cell-ellipsis">
              <span>{{ cellProps.value }}</span>
              <q-tooltip v-if="cellProps.value && cellProps.value.length > 28">{{
                cellProps.value
              }}</q-tooltip>
            </q-td>
          </template>
          <template #body-cell-amount="cellProps">
            <q-td :props="cellProps">
              <span
                :class="cellProps.row.transaction_amount < 0 ? 'text-negative' : 'text-positive'"
              >
                ${{ Math.abs(cellProps.row.transaction_amount).toFixed(2) }}
              </span>
            </q-td>
          </template>
          <template #body-cell-rule="cellProps">
            <q-td :props="cellProps" class="cell-ellipsis">
              <span>{{ cellProps.value }}</span>
              <q-tooltip v-if="cellProps.value && cellProps.value.length > 18">{{
                cellProps.value
              }}</q-tooltip>
            </q-td>
          </template>
          <template #body-cell-budget="cellProps">
            <q-td :props="cellProps" class="cell-ellipsis">
              <span>{{ cellProps.value }}</span>
              <q-tooltip v-if="cellProps.value && cellProps.value.length > 18">{{
                cellProps.value
              }}</q-tooltip>
            </q-td>
          </template>
        </q-table>
      </q-card-section>

      <q-card-actions align="right" class="dialog-actions">
        <span class="text-grey-6 q-mr-md">{{ selectedCount }} selected</span>
        <q-btn flat label="Cancel" class="btn-cancel" @click="cancel" />
        <q-btn
          flat
          label="Apply Rules"
          class="btn-submit"
          :disable="selectedCount === 0"
          :loading="rulesStore.applyLoading"
          @click="applyRules"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<style scoped>
.cell-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

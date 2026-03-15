<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useQuasar } from 'quasar'
import type { RulePreviewItem } from 'src/api'
import { useRulesStore } from '../../stores/rulesStore'

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
const $q = useQuasar()
const rulesStore = useRulesStore()

const previewItems = ref<RulePreviewItem[]>([])
const overrideExisting = ref(false)
const selectedIds = ref<Set<number>>(new Set())

const selectedCount = computed(() => selectedIds.value.size)
const hasPreview = computed(() => previewItems.value.length > 0)

watch(
  () => props.visible,
  async (visible) => {
    if (visible) {
      await loadPreview()
    }
  },
)

async function loadPreview() {
  try {
    const response = await rulesStore.previewRuleApplication(
      props.month,
      props.year,
      overrideExisting.value,
    )
    if (response) {
      previewItems.value = response.assignments
      selectedIds.value = new Set(response.assignments.map((a) => a.transaction_id))
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to load rule preview' })
  }
}

function toggleSelection(transactionId: number) {
  if (selectedIds.value.has(transactionId)) {
    selectedIds.value.delete(transactionId)
  } else {
    selectedIds.value.add(transactionId)
  }
  selectedIds.value = new Set(selectedIds.value)
}

function selectAll() {
  selectedIds.value = new Set(previewItems.value.map((a) => a.transaction_id))
}

function selectNone() {
  selectedIds.value = new Set()
}

async function applyRules() {
  if (selectedIds.value.size === 0) return
  try {
    const response = await rulesStore.applyRules(
      Array.from(selectedIds.value),
      overrideExisting.value,
    )
    if (response) {
      $q.notify({
        type: 'positive',
        message: `Applied ${response.applied_count} assignments`,
      })
      emit('applied')
      cancel()
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to apply rules' })
  }
}

function cancel() {
  emit('update:visible', false)
  previewItems.value = []
  selectedIds.value = new Set()
}
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
          :columns="[
            { name: 'select', label: '', field: 'transaction_id', align: 'center' },
            { name: 'description', label: 'Description', field: 'transaction_description', align: 'left' },
            { name: 'amount', label: 'Amount', field: 'transaction_amount', align: 'right' },
            { name: 'rule', label: 'Rule', field: 'rule_name', align: 'left' },
            { name: 'budget', label: 'Target Budget', field: 'target_budget_name', align: 'left' },
          ]"
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
          <template #body-cell-amount="cellProps">
            <q-td :props="cellProps">
              <span :class="cellProps.row.transaction_amount < 0 ? 'text-negative' : 'text-positive'">
                ${{ Math.abs(cellProps.row.transaction_amount).toFixed(2) }}
              </span>
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

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useQuasar } from 'quasar'
import type { TransactionResponse, RuleCondition, RuleFieldEnum, RuleOperatorEnum } from 'src/api'
import { useBudgetStore } from '../../stores/budgetStore'
import { useRulesStore } from '../../stores/rulesStore'
import RuleConditionForm from './RuleConditionForm.vue'

interface Props {
  transaction: TransactionResponse | null
  visible: boolean
  month: number
  year: number
}

interface Emits {
  (_event: 'update:visible', _value: boolean): void
  (_event: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const $q = useQuasar()
const budgetStore = useBudgetStore()
const rulesStore = useRulesStore()

const ruleName = ref('')
const targetBudgetId = ref<number | null>(null)
const conditions = ref<RuleCondition[]>([])
const loading = ref(false)

const canSave = computed(() => {
  return ruleName.value.trim() && targetBudgetId.value && conditions.value.length > 0
})

watch(
  () => props.visible,
  async (visible) => {
    if (visible && props.transaction) {
      await budgetStore.fetchBudgets(true, props.month, props.year)
      initializeFromTransaction()
    }
  },
)

function initializeFromTransaction() {
  if (!props.transaction) return
  ruleName.value = `Rule for ${props.transaction.payee || props.transaction.description}`
  targetBudgetId.value = props.transaction.budget?.id || null
  conditions.value = []
  // Pre-populate with payee if available
  if (props.transaction.payee) {
    conditions.value.push({
      field: 'payee' as RuleFieldEnum,
      operator: 'exact' as RuleOperatorEnum,
      value: props.transaction.payee,
      value2: null,
    })
  }
}

function addCondition() {
  conditions.value.push({
    field: 'payee' as RuleFieldEnum,
    operator: 'exact' as RuleOperatorEnum,
    value: '',
    value2: null,
  })
}

function updateCondition(index: number, condition: RuleCondition) {
  conditions.value[index] = condition
}

function removeCondition(index: number) {
  conditions.value.splice(index, 1)
}

async function saveRule() {
  if (!canSave.value || !targetBudgetId.value) return
  loading.value = true
  try {
    await rulesStore.createRule({
      name: ruleName.value.trim(),
      target_budget_id: targetBudgetId.value,
      conditions: conditions.value,
      priority: 0,
      is_active: true,
    })
    $q.notify({ type: 'positive', message: 'Rule created successfully' })
    emit('saved')
    cancel()
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to create rule' })
  } finally {
    loading.value = false
  }
}

function cancel() {
  emit('update:visible', false)
  ruleName.value = ''
  targetBudgetId.value = null
  conditions.value = []
}
</script>

<template>
  <q-dialog :model-value="visible" @update:model-value="emit('update:visible', $event)">
    <q-card class="dialog-card" style="min-width: 600px; max-width: 800px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Create Rule from Transaction</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="cancel" />
      </q-card-section>

      <q-card-section v-if="transaction">
        <div class="q-mb-md q-pa-md dialog-info-section">
          <div class="text-subtitle1">{{ transaction.description }}</div>
          <div class="text-subtitle2 text-grey-7">
            {{ transaction.payee }} | ${{ Math.abs(transaction.amount).toFixed(2) }}
            | {{ transaction.account?.name }}
          </div>
        </div>

        <q-input v-model="ruleName" label="Rule Name" dense outlined class="q-mb-md dialog-input" />

        <q-select
          v-model="targetBudgetId"
          :options="budgetStore.budgetOptions"
          emit-value
          map-options
          dense
          outlined
          label="Assign to Budget"
          class="q-mb-md dialog-select"
        />

        <div class="text-subtitle2 q-mb-sm">Conditions (all must match):</div>
        <div class="q-gutter-sm q-mb-md">
          <RuleConditionForm
            v-for="(cond, idx) in conditions"
            :key="idx"
            :condition="cond"
            :index="idx"
            @update="updateCondition"
            @remove="removeCondition"
          />
        </div>
        <q-btn flat dense icon="add" label="Add Condition" color="primary" @click="addCondition" />
      </q-card-section>

      <q-card-actions align="right" class="dialog-actions">
        <q-btn flat label="Cancel" class="btn-cancel" @click="cancel" />
        <q-btn
          flat
          label="Create Rule"
          class="btn-submit"
          :disable="!canSave"
          :loading="loading"
          @click="saveRule"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

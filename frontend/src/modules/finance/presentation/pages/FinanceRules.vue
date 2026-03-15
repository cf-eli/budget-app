<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import type { RuleResponse } from 'src/api'
import { useRulesStore } from '../stores/rulesStore'
import RuleItem from '../components/rules/RuleItem.vue'

const $q = useQuasar()
const rulesStore = useRulesStore()
const includeInactive = ref(true)

onMounted(async () => {
  await rulesStore.fetchRules(includeInactive.value)
})

async function handleToggle(ruleId: number, isActive: boolean) {
  try {
    await rulesStore.updateRule(ruleId, { is_active: isActive })
    $q.notify({ type: 'positive', message: `Rule ${isActive ? 'activated' : 'deactivated'}` })
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to update rule' })
  }
}

async function handleDelete(ruleId: number) {
  $q.dialog({
    title: 'Delete Rule',
    message: 'Are you sure you want to delete this rule?',
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await rulesStore.deleteRule(ruleId)
      $q.notify({ type: 'positive', message: 'Rule deleted' })
    } catch {
      $q.notify({ type: 'negative', message: 'Failed to delete rule' })
    }
  })
}

function handleEdit(rule: RuleResponse) {
  // TODO: Implement edit dialog
  $q.notify({ type: 'info', message: `Edit rule: ${rule.name}` })
}

async function moveRule(index: number, direction: 'up' | 'down') {
  const rules = [...rulesStore.rules]
  const newIndex = direction === 'up' ? index - 1 : index + 1
  if (newIndex < 0 || newIndex >= rules.length) return
  ;[rules[index], rules[newIndex]] = [rules[newIndex], rules[index]]
  const ruleIds = rules.map((r) => r.id)
  try {
    await rulesStore.reorderRules(ruleIds)
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to reorder rules' })
  }
}
</script>

<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5">Transaction Rules</div>
      <q-space />
      <q-checkbox v-model="includeInactive" label="Show inactive" class="q-mr-md" />
    </div>

    <q-banner v-if="rulesStore.loading" class="bg-grey-8 q-mb-md">
      <q-spinner-dots /> Loading rules...
    </q-banner>

    <q-banner v-else-if="rulesStore.rules.length === 0" class="bg-grey-8">
      <template #avatar>
        <q-icon name="rule" color="grey" />
      </template>
      No rules created yet. Create a rule from a transaction to get started.
    </q-banner>

    <q-list v-else bordered separator class="bg-dark">
      <q-item class="bg-grey-9 text-grey-5 text-caption">
        <q-item-section avatar />
        <q-item-section> Rules are applied in order. Higher rules take priority. </q-item-section>
      </q-item>

      <template v-for="(rule, index) in rulesStore.rules" :key="rule.id">
        <div v-if="includeInactive || rule.is_active" class="row items-center">
          <div class="col-auto q-pa-sm">
            <div class="column">
              <q-btn
                flat
                round
                dense
                size="xs"
                icon="arrow_upward"
                :disable="index === 0"
                @click="moveRule(index, 'up')"
              />
              <q-btn
                flat
                round
                dense
                size="xs"
                icon="arrow_downward"
                :disable="index === rulesStore.rules.length - 1"
                @click="moveRule(index, 'down')"
              />
            </div>
          </div>
          <div class="col">
            <RuleItem
              :rule="rule"
              @edit="handleEdit"
              @delete="handleDelete"
              @toggle="handleToggle"
            />
          </div>
        </div>
      </template>
    </q-list>
  </q-page>
</template>

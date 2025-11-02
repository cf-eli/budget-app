<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import {
  apiV1BudgetsFundsOrphanedMastersGetOrphanedMastersEndpoint,
  type OrphanedMasterInfo,
} from 'src/api'

interface Props {
  month: number
  year: number
}

interface Emits {
  (_event: 'discontinue', _master: OrphanedMasterInfo): void
  (_event: 'addMonth', _master: OrphanedMasterInfo): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const orphanedMasters = ref<OrphanedMasterInfo[]>([])
const loading = ref(false)
const dismissed = ref(false)

const formatCurrency = (value: number) =>
  `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

async function loadOrphanedMasters() {
  loading.value = true
  try {
    const response = await apiV1BudgetsFundsOrphanedMastersGetOrphanedMastersEndpoint({
      query: {
        month: props.month,
        year: props.year,
      },
    })

    if (response.data) {
      orphanedMasters.value = response.data.orphaned_masters || []
    }
  } catch (error) {
    console.error('Failed to load orphaned masters:', error)
  } finally {
    loading.value = false
  }
}

function dismissBanner() {
  dismissed.value = true
}

function handleDiscontinue(master: OrphanedMasterInfo) {
  emit('discontinue', master)
}

function handleAddMonth(master: OrphanedMasterInfo) {
  emit('addMonth', master)
}

watch(
  () => [props.month, props.year],
  () => {
    dismissed.value = false
    loadOrphanedMasters()
  },
)

onMounted(() => {
  loadOrphanedMasters()
})
</script>

<template>
  <q-banner
    v-if="!loading && orphanedMasters.length > 0 && !dismissed"
    class="orphaned-funds-banner bg-warning text-dark q-mb-md"
    rounded
  >
    <template #avatar>
      <q-icon name="warning" color="orange-9" size="32px" />
    </template>

    <div class="row items-center justify-between">
      <div class="col">
        <div class="text-h6 q-mb-sm">Orphaned Fund Masters Detected</div>
        <div class="text-body2 q-mb-md">
          You have {{ orphanedMasters.length }} fund master{{ orphanedMasters.length > 1 ? 's' : '' }}
          with balance but no active fund for {{ month }}/{{ year }}. These funds are not included
          in your current budget calculations.
        </div>

        <q-list bordered separator class="rounded-borders bg-white">
          <q-item
            v-for="master in orphanedMasters"
            :key="master.master_id"
            class="orphaned-master-item"
          >
            <q-item-section avatar>
              <q-icon name="account_balance_wallet" color="orange-9" />
            </q-item-section>

            <q-item-section>
              <q-item-label class="text-weight-bold">
                {{ master.name || `Master #${master.master_id}` }}
              </q-item-label>
              <q-item-label caption>
                <span v-if="master.last_fund_name">
                  Last active: {{ master.last_fund_name }}
                  ({{ master.last_active_month }}/{{ master.last_active_year }})
                </span>
                <span v-else>No previous fund history</span>
              </q-item-label>
            </q-item-section>

            <q-item-section side>
              <q-item-label class="text-h6 text-orange-9">
                {{ formatCurrency(master.balance) }}
              </q-item-label>
            </q-item-section>

            <q-item-section side>
              <div class="row q-gutter-sm">
                <q-btn
                  flat
                  dense
                  color="primary"
                  label="Add to Month"
                  icon="add"
                  size="sm"
                  @click="handleAddMonth(master)"
                >
                  <q-tooltip>Create a fund for this month linked to this master</q-tooltip>
                </q-btn>
                <q-btn
                  flat
                  dense
                  color="negative"
                  label="Discontinue"
                  icon="close"
                  size="sm"
                  @click="handleDiscontinue(master)"
                >
                  <q-tooltip>Withdraw balance and close this fund master</q-tooltip>
                </q-btn>
              </div>
            </q-item-section>
          </q-item>
        </q-list>
      </div>

      <q-btn
        flat
        round
        icon="close"
        color="dark"
        class="q-ml-md"
        @click="dismissBanner"
      >
        <q-tooltip>Dismiss for this month</q-tooltip>
      </q-btn>
    </div>
  </q-banner>
</template>

<style scoped>
.orphaned-funds-banner {
  border: 2px solid #f9a825;
}

.orphaned-master-item {
  min-height: 72px;
}
</style>

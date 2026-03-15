<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import {
  apiV1BudgetsFundsOrphanedMastersGetOrphanedMastersEndpoint,
  type OrphanedMasterInfo,
} from 'src/api'
import OrphanedMasterItem from './OrphanedMasterItem.vue'

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
          You have {{ orphanedMasters.length }} fund master{{
            orphanedMasters.length > 1 ? 's' : ''
          }}
          with balance but no active fund for {{ month }}/{{ year }}. These funds are not included
          in your current budget calculations.
        </div>

        <q-list bordered separator class="rounded-borders bg-white">
          <OrphanedMasterItem
            v-for="master in orphanedMasters"
            :key="master.master_id"
            :master="master"
            @discontinue="emit('discontinue', $event)"
            @add-month="emit('addMonth', $event)"
          />
        </q-list>
      </div>

      <q-btn flat round icon="close" color="dark" class="q-ml-md" @click="dismissBanner">
        <q-tooltip>Dismiss for this month</q-tooltip>
      </q-btn>
    </div>
  </q-banner>
</template>

<style scoped>
.orphaned-funds-banner {
  border: 2px solid #f9a825;
}
</style>

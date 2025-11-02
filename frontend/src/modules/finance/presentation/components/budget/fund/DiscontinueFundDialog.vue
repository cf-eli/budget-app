<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import {
  apiV1BudgetsFundsMastersMasterIdDiscontinueDiscontinueMasterEndpoint,
  type DiscontinueMasterRequest,
  type OrphanedMasterInfo,
} from 'src/api'

interface Props {
  master: OrphanedMasterInfo
  month: number
  year: number
}

interface Emits {
  (_event: 'close'): void
  (_event: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const $q = useQuasar()

const visible = ref(true)
const loading = ref(false)

const formatCurrency = (value: number) =>
  `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

const masterName = computed(() => props.master.name || `Master #${props.master.master_id}`)

async function confirmDiscontinue() {
  loading.value = true
  try {
    const requestBody: DiscontinueMasterRequest = {
      month: props.month,
      year: props.year,
    }

    await apiV1BudgetsFundsMastersMasterIdDiscontinueDiscontinueMasterEndpoint({
      path: { master_id: props.master.master_id },
      body: requestBody,
    })

    $q.notify({
      type: 'positive',
      message: `Fund master discontinued successfully. Withdrew ${formatCurrency(props.master.balance)}`,
      icon: 'check_circle',
      timeout: 5000,
    })

    visible.value = false
    emit('success')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to discontinue fund master',
      caption: error instanceof Error ? error.message : 'Unknown error',
    })
  } finally {
    loading.value = false
  }
}

function close() {
  visible.value = false
  emit('close')
}
</script>

<template>
  <q-dialog v-model="visible" @hide="close">
    <q-card style="min-width: 500px">
      <q-card-section class="row items-center q-pb-none">
        <q-icon name="warning" color="negative" size="32px" class="q-mr-md" />
        <div class="text-h6">Discontinue Fund Master</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="close" />
      </q-card-section>

      <q-separator />

      <q-card-section>
        <div class="text-body1 q-mb-md">
          Are you sure you want to discontinue the fund master
          <strong>{{ masterName }}</strong>?
        </div>

        <q-card flat bordered class="bg-orange-1 q-mb-md">
          <q-card-section>
            <div class="text-caption text-grey-7">Current Balance to Withdraw</div>
            <div class="text-h4 text-orange-9">{{ formatCurrency(master.balance) }}</div>
          </q-card-section>
        </q-card>

        <div class="text-body2 q-mb-md">
          This will:
          <ul class="q-pl-md q-my-sm">
            <li>Withdraw the entire balance ({{ formatCurrency(master.balance) }})</li>
            <li>Close the fund master permanently</li>
            <li>Create a withdrawal transaction for {{ month }}/{{ year }}</li>
          </ul>
        </div>

        <q-banner class="bg-negative text-white" rounded dense>
          <template #avatar>
            <q-icon name="error" />
          </template>
          <div>
            <strong>This action cannot be undone!</strong>
            <div class="text-caption">
              Once discontinued, the fund master and its history will be permanently removed.
            </div>
          </div>
        </q-banner>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right">
        <q-btn flat label="Cancel" @click="close" />
        <q-btn
          flat
          color="negative"
          label="Yes, Discontinue"
          icon="delete_forever"
          @click="confirmDiscontinue"
          :loading="loading"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

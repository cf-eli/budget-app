<script setup lang="ts">
import { ref } from 'vue'
import { useQuasar } from 'quasar'
import type { OrphanedMasterInfo } from 'src/api'
import { useAddMonthToMaster } from 'src/modules/finance/presentation/composables/useAddMonthToMaster'

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

const { loading, formData, haveMax, formatCurrency, masterName, submitForm } = useAddMonthToMaster(
  () => props.master,
  () => props.month,
  () => props.year,
  () => {
    visible.value = false
    emit('success')
  },
)

function close() {
  visible.value = false
  emit('close')
}
</script>

<template>
  <q-dialog
    v-model="visible"
    @hide="close"
    :maximized="$q.screen.lt.sm"
    transition-show="slide-up"
    transition-hide="slide-down"
  >
    <q-card
      :style="
        $q.screen.lt.sm ? 'width: 100vw; max-width: 100vw;' : 'width: 500px; max-width: 90vw;'
      "
    >
      <q-card-section class="row items-center q-pb-none">
        <q-icon name="add_circle" color="primary" size="32px" class="q-mr-md" />
        <div class="text-h6">Add Fund to Orphaned Master</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="close" />
      </q-card-section>

      <q-separator />

      <q-card-section>
        <div class="text-body1 q-mb-md">
          Create a new fund for <strong>{{ month }}/{{ year }}</strong> linked to:
        </div>

        <q-card flat bordered class="bg-blue-1 q-mb-md">
          <q-card-section>
            <div class="row items-center justify-between">
              <div>
                <div class="text-subtitle2 text-grey-7">Fund Master</div>
                <div class="text-h6 text-blue-9">{{ masterName }}</div>
                <div class="text-caption text-grey-7" v-if="master.last_fund_name">
                  Last active: {{ master.last_fund_name }} ({{ master.last_active_month }}/{{
                    master.last_active_year
                  }})
                </div>
              </div>
              <div class="text-right">
                <div class="text-caption text-grey-7">Current Balance</div>
                <div class="text-h5 text-blue-9">{{ formatCurrency(master.balance) }}</div>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <q-form @submit.prevent="submitForm">
          <q-input
            v-model.number="formData.increment"
            type="number"
            label="Monthly Increment"
            filled
            class="q-mb-md"
            prefix="$"
            hint="Amount to add each month"
            :rules="[
              (val) => (val !== null && val !== '') || 'Increment is required',
              (val) => val > 0 || 'Must be positive',
            ]"
          />

          <q-input
            v-model.number="formData.priority"
            type="number"
            label="Priority"
            hint="Leave at 0 to add to end of list"
            filled
            class="q-mb-md"
          />

          <q-checkbox v-model="haveMax" label="Set Maximum" class="q-mb-md" />

          <q-input
            v-if="haveMax"
            v-model.number="formData.max"
            type="number"
            label="Maximum Balance"
            filled
            class="q-mb-md"
            prefix="$"
            hint="Optional maximum balance for this fund"
          />

          <q-banner class="bg-info text-white q-mb-md" rounded dense>
            <template #avatar>
              <q-icon name="info" />
            </template>
            <div class="text-body2">
              This fund will be linked to the existing master and will have access to the current
              balance of {{ formatCurrency(master.balance) }}.
            </div>
          </q-banner>

          <div class="row justify-end q-mt-md q-gutter-sm">
            <q-btn flat label="Cancel" @click="close" />
            <q-btn
              flat
              color="primary"
              label="Create Fund"
              icon="add"
              type="submit"
              :loading="loading"
            />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

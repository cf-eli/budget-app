<script setup lang="ts">
import { useMergeMaster } from 'src/modules/finance/presentation/composables/useMergeMaster'
import MergeFundSelector from './MergeFundSelector.vue'

interface Props {
  fundId: number
  fundName: string
  currentMasterId: number
  currentMasterBalance: number
  currentMonth: number
  currentYear: number
}

interface Emits {
  (_event: 'close'): void
  (_event: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const {
  visible,
  loading,
  searchMonth,
  searchYear,
  availableFunds,
  selectedFund,
  selectedFundDetails,
  formatCurrency,
  searchFunds,
  confirmCombine,
  close,
} = useMergeMaster({
  fundId: props.fundId,
  currentMasterId: props.currentMasterId,
  currentMonth: props.currentMonth,
  currentYear: props.currentYear,
  onClose: () => emit('close'),
  onRefresh: () => emit('refresh'),
})
</script>

<template>
  <q-dialog v-model="visible" @hide="close">
    <q-card style="min-width: 600px; max-width: 800px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Combine with Another Master Fund</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="close" />
      </q-card-section>

      <q-separator />

      <q-card-section>
        <!-- Current Fund Info -->
        <q-banner class="bg-blue-1 q-mb-md" rounded>
          <template #avatar>
            <q-icon name="savings" color="blue-9" />
          </template>
          <div>
            <div class="text-subtitle1 text-bold">{{ fundName }}</div>
            <div class="text-caption">
              Current Master Balance: {{ formatCurrency(currentMasterBalance) }}
            </div>
          </div>
        </q-banner>

        <!-- Warning Banner -->
        <q-banner class="bg-warning text-dark q-mb-md" rounded>
          <template #avatar><q-icon name="warning" /></template>
          <div class="text-body2">
            <strong>Important:</strong> Combining fund masters will merge the balances of both
            masters. All funds from the selected master will be linked to this fund's master. This
            action cannot be undone.
          </div>
        </q-banner>

        <MergeFundSelector
          v-model:search-month="searchMonth"
          v-model:search-year="searchYear"
          v-model:selected-fund="selectedFund"
          :available-funds="availableFunds"
          :selected-fund-details="selectedFundDetails"
          :loading="loading"
          @search="searchFunds"
        />

        <!-- Info Banner -->
        <q-banner class="bg-info text-white q-mt-md" rounded dense>
          <template #avatar><q-icon name="info" /></template>
          <div class="text-body2">
            After combining, all funds from the selected master will point to
            <strong>{{ fundName }}'s</strong> master. The combined balance will be the sum of both
            master balances.
          </div>
        </q-banner>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right">
        <q-btn flat label="Cancel" @click="close" />
        <q-btn
          flat
          color="primary"
          label="Combine Masters"
          icon="merge_type"
          :loading="loading"
          :disable="!selectedFund"
          @click="confirmCombine"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<style scoped>
.q-card {
  max-height: 80vh;
  overflow-y: auto;
}
</style>

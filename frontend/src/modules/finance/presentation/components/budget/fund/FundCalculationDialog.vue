<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFundCalculation } from 'src/modules/finance/presentation/composables/useFundCalculation'
import FundCalculationTab from './FundCalculationTab.vue'
import FundMasterHistoryTab from './FundMasterHistoryTab.vue'
import FundUnlinkDialog from './FundUnlinkDialog.vue'
import MergeMasterDialog from './MergeMasterDialog.vue'

interface Props {
  fundId: number
  fundName: string
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
  loading,
  calculationData,
  masterFundDetails,
  formatCurrency,
  loadCalculation,
  loadMasterFundDetails,
  showUnlinkDialog,
  showMergeDialog,
  confirmUnlink,
  handleMergeRefresh,
} = useFundCalculation(
  () => props.fundId,
  () => emit('refresh'),
)

const visible = ref(true)
const activeTab = ref('calculation')

function close() {
  visible.value = false
  emit('close')
}

onMounted(async () => {
  await loadCalculation()
  await loadMasterFundDetails()
})
</script>

<template>
  <q-dialog v-model="visible" @hide="close">
    <q-card style="min-width: 700px; max-width: 900px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">{{ fundName }} - Fund Details</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="close" />
      </q-card-section>
      <q-separator />
      <q-tabs
        v-model="activeTab"
        dense
        class="text-grey"
        active-color="primary"
        indicator-color="primary"
        align="left"
      >
        <q-tab name="calculation" label="Current Month" icon="calculate" />
        <q-tab name="master" label="Master Fund History" icon="history" />
      </q-tabs>
      <q-separator />
      <q-card-section v-if="loading" class="text-center">
        <q-spinner color="primary" size="50px" />
        <div class="q-mt-md text-grey-7">Loading...</div>
      </q-card-section>
      <q-tab-panels v-else v-model="activeTab" animated>
        <q-tab-panel name="calculation" class="bg-grey-10">
          <FundCalculationTab
            v-if="calculationData"
            :calculation-data="calculationData"
            :format-currency="formatCurrency"
          />
        </q-tab-panel>
        <q-tab-panel name="master" class="bg-grey-10">
          <FundMasterHistoryTab
            v-if="masterFundDetails"
            :master-fund-details="masterFundDetails"
            :current-month="props.currentMonth"
            :current-year="props.currentYear"
            :format-currency="formatCurrency"
          />
        </q-tab-panel>
      </q-tab-panels>
      <q-separator />
      <q-card-actions align="right">
        <q-btn
          flat
          color="secondary"
          label="Combine with Another Master"
          icon="merge_type"
          :loading="loading"
          @click="showMergeDialog = true"
        />
        <q-btn
          flat
          color="negative"
          label="Unlink & Split Balance"
          icon="link_off"
          :loading="loading"
          @click="showUnlinkDialog = true"
        />
        <q-btn flat label="Close" @click="close" />
      </q-card-actions>
    </q-card>
    <q-dialog v-model="showUnlinkDialog">
      <FundUnlinkDialog
        :master-balance="calculationData?.master_balance || 0"
        :loading="loading"
        :format-currency="formatCurrency"
        @confirm="confirmUnlink"
        @cancel="showUnlinkDialog = false"
      />
    </q-dialog>
    <MergeMasterDialog
      v-if="showMergeDialog && calculationData"
      :fund-id="props.fundId"
      :fund-name="props.fundName"
      :current-master-id="calculationData.master_id"
      :current-master-balance="calculationData.master_balance || 0"
      :current-month="props.currentMonth"
      :current-year="props.currentYear"
      @close="showMergeDialog = false"
      @refresh="handleMergeRefresh"
    />
  </q-dialog>
</template>

<style scoped>
.q-card {
  max-height: 80vh;
  overflow-y: auto;
}
</style>

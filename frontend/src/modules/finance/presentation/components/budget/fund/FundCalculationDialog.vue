<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import {
  apiV1BudgetsFundsFundIdCalculateCalculateFund,
  apiV1BudgetsFundsFundIdUnlinkUnlinkFund,
  apiV1BudgetsFundsMastersMasterIdDetailsGetMasterFundDetailsEndpoint,
  type FundCalculationResponse,
  type MasterFundDetailsResponse,
  type FundUnlinkRequest,
} from 'src/api'
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
const $q = useQuasar()

const visible = ref(true)
const loading = ref(false)
const activeTab = ref('calculation')
const calculationData = ref<FundCalculationResponse | null>(null)
const masterFundDetails = ref<MasterFundDetailsResponse | null>(null)
const showUnlinkDialog = ref(false)
const showMergeDialog = ref(false)
const unlinkKeepAmount = ref(0)

const formatCurrency = (value: number | null | undefined) =>
  value !== null && value !== undefined ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A'

async function loadCalculation() {
  loading.value = true
  try {
    const response = await apiV1BudgetsFundsFundIdCalculateCalculateFund({
      path: { fund_id: props.fundId }
    })
    calculationData.value = response.data as FundCalculationResponse
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load fund calculation',
      caption: error instanceof Error ? error.message : 'Unknown error'
    })
  } finally {
    loading.value = false
  }
}

async function loadMasterFundDetails() {
  if (!calculationData.value?.master_id) return
  
  loading.value = true
  try {
    const response = await apiV1BudgetsFundsMastersMasterIdDetailsGetMasterFundDetailsEndpoint({
      path: { master_id: calculationData.value.master_id }
    })
    masterFundDetails.value = response.data as MasterFundDetailsResponse
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load master fund details',
      caption: error instanceof Error ? error.message : 'Unknown error'
    })
  } finally {
    loading.value = false
  }
}

function openUnlinkDialog() {
  // Initialize with half the master balance
  unlinkKeepAmount.value = Math.floor((calculationData.value?.master_balance || 0) / 2)
  showUnlinkDialog.value = true
}

async function confirmUnlink() {
  loading.value = true
  try {
    const requestBody: FundUnlinkRequest = {
      keep_amount: unlinkKeepAmount.value
    }
    
    await apiV1BudgetsFundsFundIdUnlinkUnlinkFund({
      path: { fund_id: props.fundId },
      body: requestBody
    })
    
    $q.notify({
      type: 'positive',
      message: 'Fund unlinked and balance split successfully',
      icon: 'link_off'
    })
    
    showUnlinkDialog.value = false
    await loadCalculation()
    emit('refresh')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to unlink fund',
      caption: error instanceof Error ? error.message : 'Unknown error'
    })
  } finally {
    loading.value = false
  }
}

function openMergeDialog() {
  showMergeDialog.value = true
}

async function handleMergeRefresh() {
  // Reload calculation first to get updated master_fund_id after merge
  await loadCalculation()
  // Then load master fund details with the new master ID
  await loadMasterFundDetails()
  emit('refresh')
}

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

      <!-- Tabs -->
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
        <!-- Current Month Calculation Tab -->
        <q-tab-panel name="calculation" class="bg-grey-10">
          <q-card-section v-if="calculationData">
        <!-- Fund Summary -->
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-6">
            <q-card flat bordered class="bg-grey-9">
              <q-card-section>
                <div class="text-caption text-grey-5">Master Balance</div>
                <div class="text-h5 text-blue-4">{{ formatCurrency(calculationData.master_balance) }}</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-6">
            <q-card flat bordered class="bg-grey-9">
              <q-card-section>
                <div class="text-caption text-grey-5">This Month</div>
                <div class="text-h5 text-white">{{ formatCurrency(calculationData.month_amount) }}</div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- Fund Properties -->
        <div class="row q-col-gutter-sm q-mb-md">
          <div class="col-4">
            <div class="text-caption text-grey-5">Priority</div>
            <div class="text-body1 text-white">{{ calculationData.priority }}</div>
          </div>
          <div class="col-4">
            <div class="text-caption text-grey-5">Increment</div>
            <div class="text-body1 text-white">{{ formatCurrency(calculationData.increment) }}</div>
          </div>
          <div class="col-4">
            <div class="text-caption text-grey-5">Max</div>
            <div class="text-body1 text-white">{{ formatCurrency(calculationData.max) }}</div>
          </div>
        </div>
      </q-card-section>
        </q-tab-panel>

        <!-- Master Fund History Tab -->
        <q-tab-panel name="master" class="bg-grey-10">
          <q-card-section v-if="masterFundDetails">
            <!-- Master Fund Summary -->
            <q-banner class="bg-grey-9 text-white q-mb-md" rounded>
              <template #avatar>
                <q-icon name="account_balance" color="blue-4" size="36px" />
              </template>
              <div>
                <div class="text-subtitle1 text-bold text-white">
                  {{ masterFundDetails.master_name || 'Master Fund' }}
                </div>
                <div class="text-h4 text-blue-4 q-mt-xs">
                  {{ formatCurrency(masterFundDetails.total_balance) }}
                </div>
                <div class="text-caption text-grey-5">Total Balance Across All Months</div>
              </div>
            </q-banner>

            <!-- Monthly Contributions & Withdrawals -->
            <div class="text-subtitle1 text-white q-mb-md">Monthly History</div>
            <q-list bordered separator class="bg-grey-9">
              <q-item
                v-for="fund in masterFundDetails.funds"
                :key="fund.fund_id"
                :class="{ 'bg-grey-8': fund.month === currentMonth && fund.year === currentYear }"
                dark
              >
                <q-item-section>
                  <q-item-label class="text-bold text-white">
                    {{ fund.budget_name }}
                    <q-badge
                      v-if="fund.month === currentMonth && fund.year === currentYear"
                      color="blue-4"
                      label="Current"
                      class="q-ml-sm"
                    />
                  </q-item-label>
                  <q-item-label caption class="text-grey-5">
                    {{ fund.month }}/{{ fund.year }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div class="text-right">
                    <div class="text-positive">
                      + {{ formatCurrency(fund.month_amount) }}
                      <q-tooltip>Amount contributed this month</q-tooltip>
                    </div>
                    <div class="text-negative">
                      {{ formatCurrency(fund.transactions) }}
                      <q-tooltip>Amount withdrawn (transactions)</q-tooltip>
                    </div>
                    <q-separator class="q-my-xs" dark />
                    <div 
                      class="text-bold"
                      :class="fund.net_contribution >= 0 ? 'text-positive' : 'text-negative'"
                    >
                      Net: {{ formatCurrency(fund.net_contribution) }}
                    </div>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <!-- Summary -->
            <q-card flat bordered class="q-mt-md bg-grey-9">
              <q-card-section>
                <div class="text-caption text-grey-5">
                  This shows all funds across months that belong to the same master fund family.
                  The master balance represents your cumulative savings over time.
                </div>
              </q-card-section>
            </q-card>
          </q-card-section>
        </q-tab-panel>
      </q-tab-panels>

      <q-separator />

      <q-card-actions align="right">
        <q-btn
          flat
          color="secondary"
          label="Combine with Another Master"
          icon="merge_type"
          @click="openMergeDialog"
          :loading="loading"
        />
        <q-btn
          flat
          color="negative"
          label="Unlink & Split Balance"
          icon="link_off"
          @click="openUnlinkDialog"
          :loading="loading"
        />
        <q-btn flat label="Close" @click="close" />
      </q-card-actions>
    </q-card>

    <!-- Unlink & Split Balance Dialog -->
    <q-dialog v-model="showUnlinkDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Unlink & Split Balance</div>
        </q-card-section>

        <q-card-section>
          <div class="text-body2 q-mb-md">
            Unlinking will create a new master fund for this fund. You can choose how to split
            the current master balance between this fund and the remaining linked funds.
          </div>

          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-6">
              <q-card flat bordered class="bg-blue-1">
                <q-card-section>
                  <div class="text-caption text-grey-7">Current Master Balance</div>
                  <div class="text-h5 text-blue-9">
                    {{ formatCurrency(calculationData?.master_balance || 0) }}
                  </div>
                </q-card-section>
              </q-card>
            </div>
            <div class="col-6">
              <q-card flat bordered class="bg-orange-1">
                <q-card-section>
                  <div class="text-caption text-grey-7">Remaining Balance</div>
                  <div class="text-h5 text-orange-9">
                    {{ formatCurrency((calculationData?.master_balance || 0) - unlinkKeepAmount) }}
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>

          <q-input
            v-model.number="unlinkKeepAmount"
            type="number"
            label="Amount to Keep with This Fund"
            filled
            prefix="$"
            :hint="`Amount this fund's new master will have. Remaining ${formatCurrency((calculationData?.master_balance || 0) - unlinkKeepAmount)} stays with old master.`"
            :rules="[
              (val: number) => val !== null && val !== undefined || 'Amount is required',
              (val: number) => val >= 0 || 'Must be non-negative',
              (val: number) => val <= (calculationData?.master_balance || 0) || 'Cannot exceed master balance',
            ]"
          />

          <q-banner class="bg-warning text-dark q-mt-md" rounded dense>
            <template #avatar>
              <q-icon name="warning" />
            </template>
            <div class="text-body2">
              <strong>Warning:</strong> This action cannot be undone. The fund will be unlinked
              and the master balance will be split as specified.
            </div>
          </q-banner>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showUnlinkDialog = false" />
          <q-btn
            flat
            color="negative"
            label="Unlink & Split"
            icon="link_off"
            @click="confirmUnlink"
            :loading="loading"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Merge with Another Master Dialog -->
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

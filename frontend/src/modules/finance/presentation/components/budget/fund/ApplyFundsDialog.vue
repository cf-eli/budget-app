<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import {
  apiV1BudgetsFundsApplyIncrementsApplyFundIncrementsEndpoint,
  type ApplyFundIncrementsResponse,
} from 'src/api'

interface Props {
  month: number
  year: number
  currentBalance: number
}

interface Emits {
  (_event: 'close'): void
  (_event: 'applied'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const $q = useQuasar()

const visible = ref(true)
const loading = ref(false)
const safeMode = ref(false)
const result = ref<ApplyFundIncrementsResponse | null>(null)
const showResult = ref(false)

const formatCurrency = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '$0.00'
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const wouldGoNegative = computed(() => {
  if (!result.value) return false
  return result.value.would_go_negative
})

async function applyFunds() {
  loading.value = true
  try {
    const response = await apiV1BudgetsFundsApplyIncrementsApplyFundIncrementsEndpoint({
      body: {
        month: props.month,
        year: props.year,
        safe_mode: safeMode.value
      }
    })
    
    // Ensure we have a valid response
    if (!response.data) {
      throw new Error('No data received from server')
    }
    
    result.value = response.data as ApplyFundIncrementsResponse
    
    // Ensure result has all required fields
    if (
      result.value.applied_funds === undefined ||
      result.value.skipped_funds === undefined ||
      result.value.balance_before === undefined ||
      result.value.balance_after === undefined ||
      result.value.total_applied === undefined ||
      result.value.would_go_negative === undefined
    ) {
      throw new Error('Invalid response structure from server')
    }
    
    showResult.value = true
    
    $q.notify({
      type: 'positive',
      message: `Applied ${formatCurrency(result.value.total_applied)} to ${result.value.applied_funds.length} funds`,
      icon: 'savings'
    })
    
    emit('applied')
  } catch (error) {
    console.error('Error applying fund increments:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to apply fund increments',
      caption: error instanceof Error ? error.message : 'Unknown error'
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
    <q-card style="min-width: 500px; max-width: 700px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Apply Fund Increments</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="close" />
      </q-card-section>

      <q-separator />

      <q-card-section v-if="!showResult">
        <div class="text-body1 q-mb-md">
          This will add each fund's increment amount to its current balance, by priority (1 = highest first).
        </div>

        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-caption text-grey-7">Current Balance</div>
            <div class="text-h6" :class="currentBalance >= 0 ? 'text-positive' : 'text-negative'">
              {{ formatCurrency(currentBalance) }}
            </div>
          </q-card-section>
        </q-card>

        <q-toggle
          v-model="safeMode"
          label="Safe Mode (stop before balance goes negative)"
          color="primary"
          class="q-mb-md"
        />

        <q-banner v-if="safeMode" class="bg-info text-white q-mb-md" rounded dense>
          <template #avatar>
            <q-icon name="info" />
          </template>
          Safe mode will only apply increments up to the available balance, ensuring your balance doesn't go negative.
        </q-banner>

        <q-banner v-else class="bg-warning text-white q-mb-md" rounded dense>
          <template #avatar>
            <q-icon name="warning" />
          </template>
          Without safe mode, all increments will be applied even if it makes your balance negative. This will carry over to next month.
        </q-banner>
      </q-card-section>

      <!-- Results Section -->
      <q-card-section v-else-if="result">
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-6">
            <q-card flat bordered>
              <q-card-section>
                <div class="text-caption text-grey-7">Balance Before</div>
                <div class="text-h6">{{ formatCurrency(result.balance_before) }}</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-6">
            <q-card flat bordered :class="result.balance_after < 0 ? 'bg-red-1' : 'bg-teal-1'">
              <q-card-section>
                <div class="text-caption text-grey-7">Balance After</div>
                <div class="text-h6" :class="result.balance_after >= 0 ? 'text-teal' : 'text-negative'">
                  {{ formatCurrency(result.balance_after) }}
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <q-banner v-if="wouldGoNegative" class="bg-warning text-white q-mb-md" rounded>
          <template #avatar>
            <q-icon name="warning" />
          </template>
          <strong>Warning:</strong> Balance is now negative. This deficit will carry over to next month.
        </q-banner>

        <!-- Applied Funds -->
        <div v-if="result.applied_funds.length > 0" class="q-mb-md">
          <div class="text-subtitle1 q-mb-sm">Applied to Funds</div>
          <q-list bordered separator>
            <q-item v-for="fund in result.applied_funds" :key="fund.fund_id">
              <q-item-section avatar>
                <q-icon name="check_circle" color="positive" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ fund.fund_name }}</q-item-label>
                <q-item-label caption>
                  Added {{ formatCurrency(fund.amount_added!) }} → New total: {{ formatCurrency(fund.new_amount!) }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-item-label class="text-positive text-bold">+{{ formatCurrency(fund.amount_added!) }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <!-- Skipped Funds -->
        <div v-if="result.skipped_funds.length > 0">
          <div class="text-subtitle1 q-mb-sm">Skipped Funds</div>
          <q-list bordered separator>
            <q-item v-for="fund in result.skipped_funds" :key="fund.fund_id">
              <q-item-section avatar>
                <q-icon name="cancel" color="grey" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ fund.fund_name }}</q-item-label>
                <q-item-label caption class="text-grey-7">{{ fund.reason }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <div class="q-mt-md text-center">
          <q-card flat bordered class="bg-grey-2">
            <q-card-section>
              <div class="text-caption">Total Applied to Funds</div>
              <div class="text-h5 text-teal">{{ formatCurrency(result.total_applied) }}</div>
            </q-card-section>
          </q-card>
        </div>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right">
        <q-btn v-if="!showResult" flat label="Cancel" @click="close" />
        <q-btn
          v-if="!showResult"
          flat
          color="primary"
          label="Apply Funds"
          icon="savings"
          @click="applyFunds"
          :loading="loading"
        />
        <q-btn v-else flat label="Done" color="primary" @click="close" />
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

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import {
  apiV1BudgetsFundsFundIdCombineCombineFundToMaster,
  apiV1BudgetsNamesGetBudgetsNames,
  type BudgetNameResponse,
} from 'src/api'

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
const $q = useQuasar()

const visible = ref(true)
const loading = ref(false)
const searchMonth = ref(props.currentMonth)
const searchYear = ref(props.currentYear)
const availableFunds = ref<BudgetNameResponse[]>([])
const selectedFund = ref<number | null>(null)

const selectedFundDetails = computed(() => {
  if (!selectedFund.value) return null
  return availableFunds.value.find(f => f.id === selectedFund.value)
})

const formatCurrency = (value: number | null | undefined) =>
  value !== null && value !== undefined ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A'

async function searchFunds() {
  loading.value = true
  try {
    const response = await apiV1BudgetsNamesGetBudgetsNames({
      query: { month: searchMonth.value, year: searchYear.value }
    })
    
    // Filter out:
    // 1. The current fund itself
    // 2. Non-fund budgets (master_id === null)
    // 3. Funds already linked to the same master
    availableFunds.value = (response.data || []).filter(
      budget => 
        budget.id !== props.fundId && 
        (budget as any).master_id !== null &&
        (budget as any).master_id !== props.currentMasterId
    )
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load funds',
      caption: error instanceof Error ? error.message : 'Unknown error'
    })
  } finally {
    loading.value = false
  }
}

async function confirmCombine() {
  if (!selectedFund.value) {
    $q.notify({
      type: 'warning',
      message: 'Please select a fund to combine with'
    })
    return
  }

  loading.value = true
  try {
    await apiV1BudgetsFundsFundIdCombineCombineFundToMaster({
      path: { fund_id: props.fundId },
      body: { target_fund_id: selectedFund.value }
    })
    
    $q.notify({
      type: 'positive',
      message: 'Fund masters combined successfully',
      caption: 'The two fund masters have been combined into one',
      icon: 'merge_type'
    })
    
    close()
    emit('refresh')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to combine fund masters',
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

onMounted(() => {
  searchFunds()
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
          <template #avatar>
            <q-icon name="warning" />
          </template>
          <div>
            <div class="text-body2">
              <strong>Important:</strong> Combining fund masters will merge the balances of both masters.
              All funds from the selected master will be linked to this fund's master.
              This action cannot be undone.
            </div>
          </div>
        </q-banner>

        <!-- Search Controls -->
        <div class="text-subtitle2 q-mb-sm">Search for a fund to combine with:</div>
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-4">
            <q-select
              v-model="searchMonth"
              :options="[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]"
              label="Month"
              outlined
              dense
            />
          </div>
          <div class="col-4">
            <q-input
              v-model.number="searchYear"
              type="number"
              label="Year"
              outlined
              dense
            />
          </div>
          <div class="col-4">
            <q-btn
              color="primary"
              label="Search"
              icon="search"
              @click="searchFunds"
              :loading="loading"
              class="full-width"
            />
          </div>
        </div>

        <!-- Fund Selection -->
        <q-select
          v-model="selectedFund"
          :options="availableFunds"
          option-value="id"
          option-label="name"
          label="Select Fund to Combine With"
          outlined
          emit-value
          map-options
          :loading="loading"
        >
          <template #option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section>
                <q-item-label>{{ scope.opt.name }}</q-item-label>
                <q-item-label caption>
                  {{ scope.opt.month }}/{{ scope.opt.year }} 
                  <span v-if="scope.opt.fund_master_id"> | Master ID: {{ scope.opt.fund_master_id }}</span>
                </q-item-label>
              </q-item-section>
            </q-item>
          </template>
          <template #no-option>
            <q-item>
              <q-item-section class="text-grey">
                No funds found for the selected month/year
              </q-item-section>
            </q-item>
          </template>
        </q-select>

        <!-- Selected Fund Preview -->
        <q-card v-if="selectedFundDetails" flat bordered class="q-mt-md bg-green-1">
          <q-card-section>
            <div class="text-subtitle2 text-green-9 q-mb-xs">Selected Fund:</div>
            <div class="row q-col-gutter-sm">
              <div class="col-6">
                <div class="text-caption text-grey-7">Name</div>
                <div class="text-body2">{{ selectedFundDetails.name }}</div>
              </div>
              <div class="col-6">
                <div class="text-caption text-grey-7">Month/Year</div>
                <div class="text-body2">{{ selectedFundDetails.month }}/{{ selectedFundDetails.year }}</div>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Info Banner -->
        <q-banner class="bg-info text-white q-mt-md" rounded dense>
          <template #avatar>
            <q-icon name="info" />
          </template>
          <div class="text-body2">
            After combining, all funds from the selected master will point to <strong>{{ fundName }}'s</strong> master.
            The combined balance will be the sum of both master balances.
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
          @click="confirmCombine"
          :loading="loading"
          :disable="!selectedFund"
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

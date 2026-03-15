<script setup lang="ts">
import { ref } from 'vue'
import {
  useApplyFunds,
  formatCurrency,
} from 'src/modules/finance/presentation/composables/useApplyFunds'
import ApplyFundsResultSection from './ApplyFundsResultSection.vue'

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

const visible = ref(true)

const { loading, safeMode, result, showResult, wouldGoNegative, applyFunds } = useApplyFunds(
  props,
  () => emit('applied'),
)

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
          This will add each fund's increment amount to its current balance, by priority (1 =
          highest first).
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
          Safe mode will only apply increments up to the available balance, ensuring your balance
          doesn't go negative.
        </q-banner>

        <q-banner v-else class="bg-warning text-white q-mb-md" rounded dense>
          <template #avatar>
            <q-icon name="warning" />
          </template>
          Without safe mode, all increments will be applied even if it makes your balance negative.
          This will carry over to next month.
        </q-banner>
      </q-card-section>

      <!-- Results Section -->
      <ApplyFundsResultSection
        v-else-if="result"
        :result="result"
        :would-go-negative="wouldGoNegative"
      />

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

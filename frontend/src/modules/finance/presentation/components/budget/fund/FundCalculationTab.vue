<script setup lang="ts">
import type { FundCalculationResponse } from 'src/api'

interface Props {
  calculationData: FundCalculationResponse
  formatCurrency: (_value: number | null | undefined) => string
}

defineProps<Props>()
</script>

<template>
  <q-card-section>
    <!-- Fund Summary -->
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-6">
        <q-card flat bordered class="bg-grey-9">
          <q-card-section>
            <div class="text-caption text-grey-5">Master Balance</div>
            <div class="text-h5 text-blue-4">
              {{ formatCurrency(calculationData.master_balance) }}
            </div>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-6">
        <q-card flat bordered class="bg-grey-9">
          <q-card-section>
            <div class="text-caption text-grey-5">This Month</div>
            <div class="text-h5 text-white">
              {{ formatCurrency(calculationData.month_amount) }}
            </div>
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
        <div class="text-body1 text-white">
          {{ formatCurrency(calculationData.increment) }}
        </div>
      </div>
      <div class="col-4">
        <div class="text-caption text-grey-5">Max</div>
        <div class="text-body1 text-white">
          {{ formatCurrency(calculationData.max) }}
        </div>
      </div>
    </div>
  </q-card-section>
</template>

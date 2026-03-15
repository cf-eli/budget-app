<script setup lang="ts">
import type { ApplyFundIncrementsResponse } from 'src/api'
import { formatCurrency } from 'src/modules/finance/presentation/composables/useApplyFunds'

interface Props {
  result: ApplyFundIncrementsResponse
  wouldGoNegative: boolean
}

defineProps<Props>()
</script>

<template>
  <q-card-section>
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
              Added {{ formatCurrency(fund.amount_added!) }} → New total:
              {{ formatCurrency(fund.new_amount!) }}
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-item-label class="text-positive text-bold"
              >+{{ formatCurrency(fund.amount_added!) }}</q-item-label
            >
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
</template>

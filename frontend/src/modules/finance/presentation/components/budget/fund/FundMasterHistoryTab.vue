<script setup lang="ts">
import type { MasterFundDetailsResponse } from 'src/api'

interface Props {
  masterFundDetails: MasterFundDetailsResponse
  currentMonth: number
  currentYear: number
  formatCurrency: (_value: number | null | undefined) => string
}

defineProps<Props>()
</script>

<template>
  <q-card-section>
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
          This shows all funds across months that belong to the same master fund family. The master
          balance represents your cumulative savings over time.
        </div>
      </q-card-section>
    </q-card>
  </q-card-section>
</template>

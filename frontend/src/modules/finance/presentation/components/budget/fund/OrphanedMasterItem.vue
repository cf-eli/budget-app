<script setup lang="ts">
import type { OrphanedMasterInfo } from 'src/api'

interface Props {
  master: OrphanedMasterInfo
}

interface Emits {
  (_event: 'discontinue', _master: OrphanedMasterInfo): void
  (_event: 'addMonth', _master: OrphanedMasterInfo): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const formatCurrency = (value: number) =>
  `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
</script>

<template>
  <q-item class="orphaned-master-item">
    <q-item-section avatar>
      <q-icon name="account_balance_wallet" color="orange-9" />
    </q-item-section>

    <q-item-section>
      <q-item-label class="text-weight-bold">
        {{ master.name || `Master #${master.master_id}` }}
      </q-item-label>
      <q-item-label caption>
        <span v-if="master.last_fund_name">
          Last active: {{ master.last_fund_name }} ({{ master.last_active_month }}/{{
            master.last_active_year
          }})
        </span>
        <span v-else>No previous fund history</span>
      </q-item-label>
    </q-item-section>

    <q-item-section side>
      <q-item-label class="text-h6 text-orange-9">
        {{ formatCurrency(master.balance) }}
      </q-item-label>
    </q-item-section>

    <q-item-section side>
      <div class="row q-gutter-sm">
        <q-btn
          flat
          dense
          color="primary"
          label="Add to Month"
          icon="add"
          size="sm"
          @click="emit('addMonth', master)"
        >
          <q-tooltip>Create a fund for this month linked to this master</q-tooltip>
        </q-btn>
        <q-btn
          flat
          dense
          color="negative"
          label="Discontinue"
          icon="close"
          size="sm"
          @click="emit('discontinue', master)"
        >
          <q-tooltip>Withdraw balance and close this fund master</q-tooltip>
        </q-btn>
      </div>
    </q-item-section>
  </q-item>
</template>

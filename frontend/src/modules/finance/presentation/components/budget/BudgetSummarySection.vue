<script setup lang="ts">
interface Props {
  title: string
  icon: string
  iconColor: string
  income: number
  expenses: number
  flexibles: number
  carryover: number
  funds: number
  balance: number
  incomePrefix?: string
  expensesPrefix?: string
  flexiblesPrefix?: string
}

const props = withDefaults(defineProps<Props>(), {
  incomePrefix: '',
  expensesPrefix: '-',
  flexiblesPrefix: '-',
})

const formatCurrency = (value: number) => `$${value.toLocaleString()}`
</script>

<template>
  <div class="summary-section">
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h6 text-white">{{ props.title }}</div>
      <q-icon :name="props.icon" size="24px" :color="props.iconColor" />
    </div>

    <q-list dense class="text-white">
      <q-item class="q-px-none q-py-xs">
        <q-item-section>
          <q-item-label caption class="text-grey-5">Income</q-item-label>
          <q-item-label class="text-positive">{{ formatCurrency(props.income) }}</q-item-label>
        </q-item-section>
      </q-item>

      <q-item class="q-px-none q-py-xs">
        <q-item-section>
          <q-item-label caption class="text-grey-5">Expenses</q-item-label>
          <q-item-label class="text-negative">-{{ formatCurrency(props.expenses) }}</q-item-label>
        </q-item-section>
      </q-item>

      <q-item class="q-px-none q-py-xs">
        <q-item-section>
          <q-item-label caption class="text-grey-5">Flexible Expenses</q-item-label>
          <q-item-label class="text-amber">-{{ formatCurrency(props.flexibles) }}</q-item-label>
        </q-item-section>
      </q-item>

      <q-item v-if="props.carryover !== 0" class="q-px-none q-py-xs">
        <q-item-section>
          <q-item-label caption class="text-grey-5">Carryover from Previous Months</q-item-label>
          <q-item-label :class="props.carryover >= 0 ? 'text-positive' : 'text-negative'">
            {{ props.carryover >= 0 ? '+' : '' }}{{ formatCurrency(props.carryover) }}
          </q-item-label>
        </q-item-section>
      </q-item>

      <q-item v-if="props.funds > 0" class="q-px-none q-py-xs">
        <q-item-section>
          <q-item-label caption class="text-grey-5">Funds (Savings)</q-item-label>
          <q-item-label class="text-amber"> -{{ formatCurrency(props.funds) }} </q-item-label>
        </q-item-section>
      </q-item>

      <q-separator color="grey-7" class="q-my-sm" />

      <q-item class="q-px-none q-py-xs">
        <q-item-section>
          <q-item-label caption class="text-grey-5">Balance</q-item-label>
          <q-item-label
            class="text-h6 text-weight-bold"
            :class="props.balance >= 0 ? 'text-positive' : 'text-negative'"
          >
            {{ formatCurrency(Math.abs(props.balance)) }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </q-list>

    <slot />
  </div>
</template>

<style scoped>
.summary-section {
  background: #1e2027;
  border-radius: 8px;
  padding: 16px;
}
</style>

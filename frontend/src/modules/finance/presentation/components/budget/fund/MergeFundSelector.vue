<script setup lang="ts">
import type { BudgetNameResponse } from 'src/api'

interface Props {
  searchMonth: number
  searchYear: number
  availableFunds: BudgetNameResponse[]
  selectedFund: number | null
  selectedFundDetails: BudgetNameResponse | null | undefined
  loading: boolean
}

interface Emits {
  (_event: 'update:searchMonth', _value: number): void
  (_event: 'update:searchYear', _value: number): void
  (_event: 'update:selectedFund', _value: number | null): void
  (_event: 'search'): void
}

defineProps<Props>()
defineEmits<Emits>()
</script>

<template>
  <div class="text-subtitle2 q-mb-sm">Search for a fund to combine with:</div>
  <div class="row q-col-gutter-md q-mb-md">
    <div class="col-4">
      <q-select
        :model-value="searchMonth"
        :options="[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]"
        label="Month"
        outlined
        dense
        @update:model-value="$emit('update:searchMonth', $event)"
      />
    </div>
    <div class="col-4">
      <q-input
        :model-value="searchYear"
        type="number"
        label="Year"
        outlined
        dense
        @update:model-value="$emit('update:searchYear', Number($event))"
      />
    </div>
    <div class="col-4">
      <q-btn
        color="primary"
        label="Search"
        icon="search"
        :loading="loading"
        class="full-width"
        @click="$emit('search')"
      />
    </div>
  </div>

  <!-- Fund Selection -->
  <q-select
    :model-value="selectedFund"
    :options="availableFunds"
    option-value="id"
    option-label="name"
    label="Select Fund to Combine With"
    outlined
    emit-value
    map-options
    :loading="loading"
    @update:model-value="$emit('update:selectedFund', $event)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section>
          <q-item-label>{{ scope.opt.name }}</q-item-label>
          <q-item-label caption>
            {{ scope.opt.month }}/{{ scope.opt.year }}
            <span v-if="scope.opt.fund_master_id">
              | Master ID: {{ scope.opt.fund_master_id }}</span
            >
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
    <template #no-option>
      <q-item>
        <q-item-section class="text-grey"
          >No funds found for the selected month/year</q-item-section
        >
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
          <div class="text-body2">
            {{ (selectedFundDetails as any).month }}/{{ (selectedFundDetails as any).year }}
          </div>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

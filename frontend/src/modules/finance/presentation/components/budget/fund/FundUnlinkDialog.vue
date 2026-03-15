<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  masterBalance: number
  loading: boolean
  formatCurrency: (_value: number | null | undefined) => string
}

interface Emits {
  (_event: 'confirm', _keepAmount: number): void
  (_event: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const unlinkKeepAmount = ref(Math.floor(props.masterBalance / 2))
</script>

<template>
  <q-card style="min-width: 500px">
    <q-card-section>
      <div class="text-h6">Unlink & Split Balance</div>
    </q-card-section>

    <q-card-section>
      <div class="text-body2 q-mb-md">
        Unlinking will create a new master fund for this fund. You can choose how to split the
        current master balance between this fund and the remaining linked funds.
      </div>

      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-6">
          <q-card flat bordered class="bg-blue-1">
            <q-card-section>
              <div class="text-caption text-grey-7">Current Master Balance</div>
              <div class="text-h5 text-blue-9">
                {{ formatCurrency(masterBalance) }}
              </div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-6">
          <q-card flat bordered class="bg-orange-1">
            <q-card-section>
              <div class="text-caption text-grey-7">Remaining Balance</div>
              <div class="text-h5 text-orange-9">
                {{ formatCurrency(masterBalance - unlinkKeepAmount) }}
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
        :hint="`Amount this fund's new master will have. Remaining ${formatCurrency(masterBalance - unlinkKeepAmount)} stays with old master.`"
        :rules="[
          (val: number) => (val !== null && val !== undefined) || 'Amount is required',
          (val: number) => val >= 0 || 'Must be non-negative',
          (val: number) => val <= masterBalance || 'Cannot exceed master balance',
        ]"
      />

      <q-banner class="bg-warning text-dark q-mt-md" rounded dense>
        <template #avatar>
          <q-icon name="warning" />
        </template>
        <div class="text-body2">
          <strong>Warning:</strong> This action cannot be undone. The fund will be unlinked and the
          master balance will be split as specified.
        </div>
      </q-banner>
    </q-card-section>

    <q-card-actions align="right">
      <q-btn flat label="Cancel" @click="emit('cancel')" />
      <q-btn
        flat
        color="negative"
        label="Unlink & Split"
        icon="link_off"
        :loading="loading"
        @click="emit('confirm', unlinkKeepAmount)"
      />
    </q-card-actions>
  </q-card>
</template>

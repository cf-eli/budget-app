<script setup lang="ts">

interface Props {
    expenseType: string;
    amount: number;
    incomeType: string;
    range: {
        min: number;
        max: number;
    };
}

defineProps<Props>();
</script>




<template>

    <!-- <div v-if="expenseType === 'income'"> -->
    <q-input class="q-pt-sm" filled type="number" v-model="amount" label="Income*" lazy-rules :rules="[
        val => val !== null && val !== '' || 'Please enter an amount',
        val => val > 0 || 'Please enter a positive number'
    ]" />
    <div class="q-mx-auto flex justify-center">
        <q-btn-toggle v-model="incomeType"
            :options="[{ label: 'Fixed', value: 'fixed' }, { label: 'Estimated', value: 'estimated' }]" />
    </div>
    <div v-if="incomeType === 'estimated'">
        <div>
            <q-input class="q-pt-sm " filled type="number" v-model="range.min" label="Minimum*"
                hint="Enter the minimum value" lazy-rules :rules="[
                    val => val !== null && val !== '' || 'Please enter a minimum value',
                    val => val > 0 || 'Please enter a positive number'
                ]" />

            <q-input class="q-pt-sm " filled type="number" v-model="range.max" label="Maximum*"
                hint="Enter the maximum value" lazy-rules :rules="[
                    val => val !== null && val !== '' || 'Please enter a maximum value',
                    val => val > range.min || 'Maximum should be greater than minimum'
                ]" />
        </div>
    </div>
    <!-- </div> -->
</template>

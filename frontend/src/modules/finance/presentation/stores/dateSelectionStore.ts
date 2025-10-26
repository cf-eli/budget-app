import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDateSelectionStore = defineStore('dateSelection', () => {
  const now = new Date()
  const selectedMonth = ref(now.getMonth() + 1)
  const selectedYear = ref(now.getFullYear())

  function setMonthYear(month: number, year: number) {
    selectedMonth.value = month
    selectedYear.value = year
  }

  function getMonthYear() {
    return {
      month: selectedMonth.value,
      year: selectedYear.value,
    }
  }

  return {
    selectedMonth,
    selectedYear,
    setMonthYear,
    getMonthYear,
  }
})

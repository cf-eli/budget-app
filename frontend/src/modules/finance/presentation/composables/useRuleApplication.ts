import { ref, computed, watch, type Ref } from 'vue'
import { useQuasar } from 'quasar'
import type { RulePreviewItem } from 'src/api'
import { useRulesStore } from '../stores/rulesStore'

interface RuleApplicationOptions {
  visible: Ref<boolean> | (() => boolean)
  month: Ref<number> | (() => number)
  year: Ref<number> | (() => number)
  onApplied: () => void
  onClose: () => void
}

export function useRuleApplication(options: RuleApplicationOptions) {
  const $q = useQuasar()
  const rulesStore = useRulesStore()

  const previewItems = ref<RulePreviewItem[]>([])
  const overrideExisting = ref(false)
  const selectedIds = ref<Set<number>>(new Set())

  const selectedCount = computed(() => selectedIds.value.size)
  const hasPreview = computed(() => previewItems.value.length > 0)

  const visibleGetter =
    typeof options.visible === 'function' ? options.visible : () => options.visible.value
  const monthGetter =
    typeof options.month === 'function' ? options.month : () => options.month.value
  const yearGetter = typeof options.year === 'function' ? options.year : () => options.year.value

  watch(visibleGetter, async (visible) => {
    if (visible) {
      await loadPreview()
    }
  })

  async function loadPreview() {
    try {
      const response = await rulesStore.previewRuleApplication(
        monthGetter(),
        yearGetter(),
        overrideExisting.value,
      )
      if (response) {
        previewItems.value = response.assignments
        selectedIds.value = new Set(response.assignments.map((a) => a.transaction_id))
      }
    } catch {
      $q.notify({ type: 'negative', message: 'Failed to load rule preview' })
    }
  }

  function toggleSelection(transactionId: number) {
    if (selectedIds.value.has(transactionId)) {
      selectedIds.value.delete(transactionId)
    } else {
      selectedIds.value.add(transactionId)
    }
    selectedIds.value = new Set(selectedIds.value)
  }

  function selectAll() {
    selectedIds.value = new Set(previewItems.value.map((a) => a.transaction_id))
  }

  function selectNone() {
    selectedIds.value = new Set()
  }

  async function applyRules() {
    if (selectedIds.value.size === 0) return
    try {
      const response = await rulesStore.applyRules(
        Array.from(selectedIds.value),
        overrideExisting.value,
      )
      if (response) {
        $q.notify({
          type: 'positive',
          message: `Applied ${response.applied_count} assignments`,
        })
        options.onApplied()
        cancel()
      }
    } catch {
      $q.notify({ type: 'negative', message: 'Failed to apply rules' })
    }
  }

  function cancel() {
    options.onClose()
    previewItems.value = []
    selectedIds.value = new Set()
  }

  return {
    rulesStore,
    previewItems,
    overrideExisting,
    selectedIds,
    selectedCount,
    hasPreview,
    loadPreview,
    toggleSelection,
    selectAll,
    selectNone,
    applyRules,
    cancel,
  }
}

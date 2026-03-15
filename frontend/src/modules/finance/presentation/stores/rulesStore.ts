import { defineStore } from 'pinia'
import { ref } from 'vue'
// These imports will be available after npm run generate:client
import {
  apiV1RulesGetRulesEndpoint,
  apiV1RulesCreateRuleEndpoint,
  apiV1RulesRuleIdUpdateRuleEndpoint,
  apiV1RulesRuleIdDeleteRuleEndpoint,
  apiV1RulesReorderReorderRulesEndpoint,
  apiV1RulesPreviewPreviewRulesEndpoint,
  apiV1RulesApplyApplyRulesEndpoint,
  type RuleResponse,
  type RulePreviewResponse,
  type ApplyRulesResponse,
  type CreateRuleRequest,
  type UpdateRuleRequest,
} from 'src/api'

export const useRulesStore = defineStore('rules', () => {
  const rules = ref<RuleResponse[]>([])
  const loading = ref(false)
  const previewLoading = ref(false)
  const applyLoading = ref(false)

  async function fetchRules(includeInactive = false): Promise<void> {
    loading.value = true
    try {
      const response = await apiV1RulesGetRulesEndpoint({
        query: { include_inactive: includeInactive },
      })
      if (response.data) {
        rules.value = response.data
      }
    } catch (error) {
      console.error('Error fetching rules:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function createRule(data: CreateRuleRequest): Promise<RuleResponse | null> {
    loading.value = true
    try {
      const response = await apiV1RulesCreateRuleEndpoint({
        body: data,
      })
      if (response.data) {
        rules.value.push(response.data)
        return response.data
      }
      return null
    } catch (error) {
      console.error('Error creating rule:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateRule(
    ruleId: number,
    data: UpdateRuleRequest,
  ): Promise<RuleResponse | null> {
    loading.value = true
    try {
      const response = await apiV1RulesRuleIdUpdateRuleEndpoint({
        path: { rule_id: ruleId },
        body: data,
      })
      if (response.data) {
        const index = rules.value.findIndex((r) => r.id === ruleId)
        if (index !== -1) {
          rules.value[index] = response.data
        }
        return response.data
      }
      return null
    } catch (error) {
      console.error('Error updating rule:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function deleteRule(ruleId: number): Promise<boolean> {
    loading.value = true
    try {
      await apiV1RulesRuleIdDeleteRuleEndpoint({
        path: { rule_id: ruleId },
      })
      rules.value = rules.value.filter((r) => r.id !== ruleId)
      return true
    } catch (error) {
      console.error('Error deleting rule:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function reorderRules(ruleIds: number[]): Promise<boolean> {
    loading.value = true
    try {
      await apiV1RulesReorderReorderRulesEndpoint({
        body: { rule_ids: ruleIds },
      })
      // Reorder local array to match
      const reordered: RuleResponse[] = []
      for (const id of ruleIds) {
        const rule = rules.value.find((r) => r.id === id)
        if (rule) {
          reordered.push({ ...rule, priority: reordered.length })
        }
      }
      rules.value = reordered
      return true
    } catch (error) {
      console.error('Error reordering rules:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function previewRuleApplication(
    month: number,
    year: number,
    overrideExisting = false,
  ): Promise<RulePreviewResponse | null> {
    previewLoading.value = true
    try {
      const response = await apiV1RulesPreviewPreviewRulesEndpoint({
        body: {
          month,
          year,
          override_existing: overrideExisting,
        },
      })
      return response.data || null
    } catch (error) {
      console.error('Error previewing rules:', error)
      throw error
    } finally {
      previewLoading.value = false
    }
  }

  async function applyRules(
    transactionIds: number[],
    overrideExisting = false,
  ): Promise<ApplyRulesResponse | null> {
    applyLoading.value = true
    try {
      const response = await apiV1RulesApplyApplyRulesEndpoint({
        body: {
          transaction_ids: transactionIds,
          override_existing: overrideExisting,
        },
      })
      return response.data || null
    } catch (error) {
      console.error('Error applying rules:', error)
      throw error
    } finally {
      applyLoading.value = false
    }
  }

  return {
    rules,
    loading,
    previewLoading,
    applyLoading,
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    reorderRules,
    previewRuleApplication,
    applyRules,
  }
})

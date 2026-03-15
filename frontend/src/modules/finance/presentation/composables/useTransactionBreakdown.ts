import { ref, computed, watch } from 'vue'
import type { TransactionResponse } from 'src/api'
import {
  apiV1TransactionsTransactionIdBreakdownGetBreakdown,
  apiV1TransactionsLineItemsLineItemIdUpdateLineItemEndpoint,
  apiV1TransactionsTransactionIdBreakdownCreateBreakdown,
  apiV1TransactionsLineItemsLineItemIdDeleteLineItemEndpoint,
} from 'src/api'
import type { LineItem } from '../components/breakdown/types'

function toSignedAmount(amount: number, isExpense: boolean): number {
  return isExpense ? -Math.abs(amount) : Math.abs(amount)
}

function toLineItemBody(item: LineItem, isExpense: boolean) {
  return {
    description: item.description,
    amount: toSignedAmount(item.amount, isExpense),
    quantity: item.quantity ?? null,
    unit_price: item.unit_price ?? null,
    category: item.category ?? null,
    budget_id: item.budget_id ?? null,
    notes: item.notes ?? null,
  }
}

export function useTransactionBreakdown(
  transaction: () => TransactionResponse,
  visible: () => boolean,
  emitSaved: () => void,
  emitClose: () => void,
) {
  const lineItems = ref<LineItem[]>([])
  const showAddForm = ref(false)
  const editingItemIndex = ref<number | null>(null)
  const isExistingBreakdown = ref(false)
  const newLineItems = ref<LineItem[]>([])
  const deletedLineItemIds = ref<number[]>([])

  const transactionAbsAmount = computed(() => Math.abs(transaction().amount))
  const isExpense = computed(() => transaction().amount < 0)

  const totalAllocated = computed(() =>
    lineItems.value.reduce((sum, item) => sum + Math.abs(item.amount), 0),
  )
  const remaining = computed(() => transactionAbsAmount.value - totalAllocated.value)
  const isBalanced = computed(() => Math.abs(remaining.value) < 0.01)

  const suggestedFirstItem = computed(() => {
    if (lineItems.value.length === 0) {
      return {
        description: transaction().description || 'Item 1',
        amount: transactionAbsAmount.value,
        quantity: 1,
      }
    }
    return null
  })

  const editingItem = computed(() => {
    if (editingItemIndex.value !== null) {
      const item = lineItems.value[editingItemIndex.value]
      if (item) return item
    }
    return suggestedFirstItem.value
  })

  const maxAmountForForm = computed(() => {
    const current = editingItemIndex.value !== null ? lineItems.value[editingItemIndex.value] : null
    return current ? remaining.value + Math.abs(current.amount) : remaining.value
  })

  function editLineItem(index: number) {
    editingItemIndex.value = index
    showAddForm.value = true
  }

  function quickAddRemaining() {
    if (remaining.value > 0) {
      lineItems.value.push({
        description: `Item ${lineItems.value.length + 1}`,
        amount: remaining.value,
        quantity: 1,
      })
    }
  }

  function addLineItem(item: LineItem) {
    const normalizedItem = { ...item, amount: Math.abs(item.amount) }

    if (editingItemIndex.value !== null) {
      lineItems.value[editingItemIndex.value] = normalizedItem
      editingItemIndex.value = null
    } else {
      lineItems.value.push(normalizedItem)
      if (!normalizedItem.id) {
        newLineItems.value.push(normalizedItem)
      }
    }
    showAddForm.value = false
  }

  function deleteLineItem(index: number) {
    const item = lineItems.value[index]
    if (!item) return

    if (item.id) {
      deletedLineItemIds.value.push(item.id)
    } else {
      const newItemIndex = newLineItems.value.findIndex((i) => i === item)
      if (newItemIndex !== -1) newLineItems.value.splice(newItemIndex, 1)
    }
    lineItems.value.splice(index, 1)
  }

  async function saveBreakdown() {
    if (!isBalanced.value) {
      alert('Total must equal transaction amount')
      return
    }

    try {
      const txId = transaction().id
      const expense = isExpense.value

      if (isExistingBreakdown.value) {
        for (const itemId of deletedLineItemIds.value) {
          await apiV1TransactionsLineItemsLineItemIdDeleteLineItemEndpoint({
            path: { line_item_id: itemId },
          })
        }
        for (const item of lineItems.value) {
          if (item.id) {
            await apiV1TransactionsLineItemsLineItemIdUpdateLineItemEndpoint({
              path: { line_item_id: item.id },
              body: toLineItemBody(item, expense),
            })
          }
        }
        const itemsToCreate = lineItems.value.filter((item) => !item.id)
        if (itemsToCreate.length > 0) {
          await apiV1TransactionsTransactionIdBreakdownCreateBreakdown({
            path: { transaction_id: txId },
            body: {
              transaction_id: txId,
              line_items: itemsToCreate.map((item) => toLineItemBody(item, expense)),
            },
          })
        }
      } else {
        await apiV1TransactionsTransactionIdBreakdownCreateBreakdown({
          path: { transaction_id: txId },
          body: {
            transaction_id: txId,
            line_items: lineItems.value.map((item) => toLineItemBody(item, expense)),
          },
        })
      }

      emitSaved()
      emitClose()
    } catch (error) {
      console.error('Error saving breakdown:', error)
      alert('Failed to save breakdown. Please try again.')
    }
  }

  function resetState() {
    lineItems.value = []
    newLineItems.value = []
    deletedLineItemIds.value = []
    isExistingBreakdown.value = false
  }

  function cancel() {
    emitClose()
    resetState()
  }

  watch(visible, async (isVisible) => {
    if (isVisible && transaction().is_split) {
      try {
        const response = await apiV1TransactionsTransactionIdBreakdownGetBreakdown({
          path: { transaction_id: transaction().id },
        })
        lineItems.value = (response.data?.line_items || []).map((item) => ({
          ...item,
          amount: Math.abs(item.amount),
        }))
        isExistingBreakdown.value = true
        newLineItems.value = []
        deletedLineItemIds.value = []
      } catch (error) {
        console.error('Error loading breakdown:', error)
      }
    } else if (isVisible) {
      resetState()
    }
  })

  return {
    lineItems,
    showAddForm,
    editingItemIndex,
    isExistingBreakdown,
    transactionAbsAmount,
    isExpense,
    totalAllocated,
    remaining,
    isBalanced,
    editingItem,
    maxAmountForForm,
    editLineItem,
    quickAddRemaining,
    addLineItem,
    deleteLineItem,
    saveBreakdown,
    cancel,
  }
}

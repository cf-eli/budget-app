export const ruleApplicationColumns = [
  {
    name: 'select',
    label: '',
    field: 'transaction_id',
    align: 'center' as const,
    style: 'width: 40px',
  },
  {
    name: 'description',
    label: 'Description',
    field: 'transaction_description',
    align: 'left' as const,
    style: 'max-width: 220px',
    classes: 'cell-ellipsis',
  },
  {
    name: 'amount',
    label: 'Amount',
    field: 'transaction_amount',
    align: 'right' as const,
    style: 'width: 80px',
  },
  {
    name: 'rule',
    label: 'Rule',
    field: 'rule_name',
    align: 'left' as const,
    style: 'max-width: 150px',
    classes: 'cell-ellipsis',
  },
  {
    name: 'budget',
    label: 'Budget',
    field: 'target_budget_name',
    align: 'left' as const,
    style: 'max-width: 150px',
    classes: 'cell-ellipsis',
  },
  {
    name: 'type',
    label: 'Mark As',
    field: 'target_transaction_type',
    align: 'left' as const,
    style: 'max-width: 120px',
    format: (val: string | null) => {
      if (!val) return ''
      const labels: Record<string, string> = {
        transfer: 'Transfer',
        credit_payment: 'Credit Payment',
        loan_payment: 'Loan Payment',
      }
      return labels[val] || val
    },
  },
]

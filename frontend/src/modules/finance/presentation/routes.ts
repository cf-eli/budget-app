import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  // {
  //   path: '',
  //   component: () => import('src/modules/finance/presentation/pages/FinanceDashboard.vue'),
  //   // children: [{ path: '', component: () => import('pages/IndexPage.vue') }],
  // },
  {
    path: 'transactions',
    component: () => import('src/modules/finance/presentation/pages/FinanceTransactions.vue'),
    // children: [{ path: '', component: () => import('pages/IndexPage.vue') }],
  },
  {
    path: 'budgets',
    component: () => import('src/modules/finance/presentation/pages/FinanceBudgets.vue'),
    // children: [{ path: '', component: () => import('pages/IndexPage.vue') }],
  },
]

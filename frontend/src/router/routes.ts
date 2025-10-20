import type { RouteRecordRaw } from 'vue-router'
// import { routes as plaidRoutes } from 'src/modules/plaid/presentation/routes'
import { routes as financeRoutes } from 'src/modules/finance/presentation/routes'
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [...financeRoutes],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes

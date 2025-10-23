<template>
  <q-layout view="lHh Lpr lFf" class="dark-layout">
    <q-header elevated class="header-dark">
      <q-toolbar class="q-py-sm">
        <q-btn 
          flat 
          dense 
          round 
          icon="menu" 
          aria-label="Menu" 
          @click="toggleLeftDrawer"
          color="white"
        />
        
        <q-toolbar-title class="row items-center q-gutter-sm">
          <q-icon name="account_balance" size="28px" color="primary" />
          <span class="text-h6">Finance Dashboard</span>
        </q-toolbar-title>

        <q-badge color="grey-7" text-color="white" class="q-px-sm">
          v{{ $q.version }}
        </q-badge>
      </q-toolbar>
    </q-header>

    <q-drawer 
      v-model="leftDrawerOpen" 
      show-if-above 
      bordered
      class="drawer-dark"
      dark
    >
      <q-scroll-area class="fit">
        <q-list class="q-pa-md">
          <q-item-label header class="text-grey-4 text-weight-medium q-px-md q-mb-sm">
            Navigation
          </q-item-label>

          <q-item
            v-for="link in linksList"
            :key="link.title"
            clickable
            :to="link.link"
            class="nav-item q-mb-xs"
            active-class="nav-item-active"
          >
            <q-item-section avatar>
              <q-icon :name="link.icon" />
            </q-item-section>

            <q-item-section>
              <q-item-label class="text-weight-medium">{{ link.title }}</q-item-label>
              <q-item-label caption v-if="link.caption" class="text-grey-5">
                {{ link.caption }}
              </q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface NavLink {
  title: string;
  caption?: string;
  icon: string;
  link: string;
}

const baseUrl = "";

const linksList: NavLink[] = [
  {
    title: 'Connect to SimpleFin',
    icon: 'link',
    link: '/connect'
  },
  {
    title: 'Transactions',
    caption: 'View Transaction History',
    icon: 'receipt_long',
    link: baseUrl + 'transactions'
  },
  {
    title: 'Budgets',
    caption: 'Manage your budgets',
    icon: 'account_balance_wallet',
    link: baseUrl + 'budgets'
  },
];

const leftDrawerOpen = ref(false);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}
</script>

<style scoped>
.dark-layout {
  background: #16171d;
}

.header-dark {
  background: #2a2d35;
  border-bottom: 1px solid #3a3d45;
}

.drawer-dark {
  background: #1e2027;
  border-right: 1px solid #3a3d45;
}

.drawer-dark :deep(.q-scrollarea__content) {
  background: #1e2027;
}
.drawer-dark :deep(.q-drawer__content) {
  background: #1e2027;
}
.nav-item {
  border-radius: 8px;
  color: #9ca3af;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #2a2d35;
  color: #ffffff;
}

.nav-item-active {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: #ffffff;
}

.nav-item-active :deep(.q-item__label) {
  color: #ffffff;
}

.nav-item-active :deep(.q-item__label--caption) {
  color: rgba(255, 255, 255, 0.7);
}

.nav-item :deep(.q-icon) {
  color: currentColor;
}

/* Header title styling */
.q-toolbar-title {
  color: #ffffff;
  font-weight: 600;
}

.drawer-dark :deep(.q-item__label--caption),
.drawer-dark .text-grey-5 {
  color: #d1d5db !important; /* much lighter gray */
}

</style>
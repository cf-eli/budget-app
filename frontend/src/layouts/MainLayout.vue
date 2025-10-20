<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />

        <q-toolbar-title>
          Finance
        </q-toolbar-title>

        <div>Finance v{{ $q.version }}</div>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item-label header>
          Essential Links
        </q-item-label>

        <EssentialLink v-for="link in linksList" :key="link.title" v-bind="link" />
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import EssentialLink, { type EssentialLinkProps } from 'components/EssentialLink.vue';
const baseUrl = "" //#import.meta.env.BASE_URL;
const linksList: EssentialLinkProps[] = [
  {
    title: 'Connect to Plaid',
    // caption: 'View Transaction History',
    icon: 'school',
    link: '/'
  },
  // {
  //   title: 'Dashboard',
  //   // caption: 'View Transaction History',
  //   icon: 'school',
  //   link: '/'
  // },
  {
    title: 'Transaction',
    caption: 'View Transaction History',
    icon: 'school',
    link: baseUrl + 'transactions'
  },
  {
    title: 'Budget',
    caption: 'View budget',
    icon: 'code',
    link: baseUrl + 'budgets'
  },
];

const leftDrawerOpen = ref(false);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}
</script>

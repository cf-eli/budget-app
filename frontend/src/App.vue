


<script setup lang="ts">
import { client } from './api/client.gen';

client.setConfig({
  baseUrl: `${import.meta.env.VITE_GATEWAY_URL}`,
  // don't include cookies in requests if developing locally
  credentials: process.env.NODE_ENV === 'development' ? 'omit' : 'include'
});

</script>

<template>
  <router-view />
</template>


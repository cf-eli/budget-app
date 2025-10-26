<template>
  <q-item clickable :to="link" exact-active-class="link-active" active-class="">
    <q-item-section v-if="icon" avatar>
      <q-icon :name="icon" />
    </q-item-section>

    <q-item-section>
      <q-item-label>{{ title }}</q-item-label>
      <q-item-label caption>{{ caption }}</q-item-label>
    </q-item-section>
  </q-item>
</template>

<script setup lang="ts">
export interface EssentialLinkProps {
  title: string
  caption?: string
  link?: string
  icon?: string
}

withDefaults(defineProps<EssentialLinkProps>(), {
  caption: '',
  link: '/',
  icon: '',
})
</script>

<style scoped>
.link-active {
  color: blue;
  /* Active color */
  font-weight: bold;
  background-color: rgba(0, 0, 255, 0.1);
}

.q-item.q-item--clickable:hover {
  background-color: rgba(0, 0, 255, 0.1);
}
</style>

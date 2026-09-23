<script setup lang="ts">
useHead({
  title: 'PromptSplat',
  link: [{ rel: 'icon', href: '/favicon.ico' }],
  htmlAttrs: { lang: 'en' }
})
</script>

<template>
  <UApp>
    <UHeader title="PromptSplat">
      <template #right>
        <UButton
          to="/"
          label="Scenes"
          color="neutral"
          variant="ghost"
        />
        <UButton
          to="/results"
          label="Results"
          color="neutral"
          variant="ghost"
        />
      </template>
    </UHeader>

    <UMain>
      <NuxtPage />
    </UMain>
  </UApp>
</template>

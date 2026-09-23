<script setup lang="ts">
import type { SceneSummary } from '~/composables/useApi'

const { getScenes } = useApi()
const scenes = ref<SceneSummary[] | null>(null)
const error = ref(false)

onMounted(async () => {
  try {
    scenes.value = await getScenes()
  } catch {
    error.value = true
  }
})

const formatCount = (n: number) => `${(n / 1e6).toFixed(2)} M`

function formatMetrics(m: SceneSummary['metrics_3dgs']): string {
  const parts: string[] = []
  for (const [key, label, digits] of [['psnr', 'PSNR', 1], ['ssim', 'SSIM', 2], ['lpips', 'LPIPS', 2]] as const) {
    const v = m[key]
    if (typeof v === 'number') parts.push(`${label} ${v.toFixed(digits)}`)
  }
  return parts.join(' · ')
}
</script>

<template>
  <UContainer class="py-8">
    <h1 class="mb-6 text-2xl font-semibold">
      Scenes
    </h1>

    <p
      v-if="error"
      class="text-error"
    >
      API not reachable: is uvicorn running on :8000?
    </p>
    <p
      v-else-if="scenes && !scenes.length"
      class="text-muted"
    >
      No scenes yet: run the pipeline, or <code>python scripts/make_fixture_scene.py</code> on the laptop
    </p>

    <div
      v-else-if="scenes"
      class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
    >
      <UCard
        v-for="s in scenes"
        :key="s.scene_id"
      >
        <template #header>
          <h2 class="font-medium">
            {{ s.title }}
          </h2>
        </template>

        <p>{{ formatCount(s.num_gaussians) }} Gaussians</p>
        <p
          v-if="formatMetrics(s.metrics_3dgs)"
          class="text-sm text-muted"
        >
          {{ formatMetrics(s.metrics_3dgs) }}
        </p>
        <p class="text-sm text-muted">
          {{ s.variants.length }} mask variants
        </p>

        <template #footer>
          <UButton
            :to="`/scene/${encodeURIComponent(s.scene_id)}`"
            label="Open"
          />
        </template>
      </UCard>
    </div>
  </UContainer>
</template>

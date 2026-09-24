<script setup lang="ts">
import type { SceneDetail } from '~/composables/useApi'

const id = useRoute().params.id as string
const { getScene } = useApi()
const scene = ref<SceneDetail | null>(null)
const notFound = ref(false)
const loading = ref(true)
const viewerError = ref<string | null>(null)
const viewer = ref<{ fps: number } | null>(null)

onMounted(async () => {
  try {
    scene.value = await getScene(id)
  } catch {
    notFound.value = true
  }
})

const assetMb = computed(() => scene.value ? (scene.value.asset.bytes / 1e6).toFixed(0) : '')

function metric(key: string, digits: number): string {
  const v = scene.value?.metrics_3dgs?.[key]
  return typeof v === 'number' ? v.toFixed(digits) : '–'
}

function onError(message: string) {
  loading.value = false
  viewerError.value = message
}
</script>

<template>
  <UContainer
    v-if="notFound"
    class="py-8"
  >
    <p class="mb-4">
      Scene not found
    </p>
    <UButton
      to="/"
      label="Back to scenes"
    />
  </UContainer>

  <div
    v-else-if="scene"
    class="flex h-[calc(100vh-var(--ui-header-height))]"
  >
    <div class="flex-1 relative">
      <SplatViewer
        ref="viewer"
        :asset-url="scene.asset_url"
        :initial-view="scene.initial_view"
        :mesh-quaternion="scene.mesh_quaternion_xyzw"
        @ready="loading = false"
        @error="onError"
      />
      <div
        v-if="loading || viewerError"
        class="absolute inset-0 flex items-center justify-center pointer-events-none"
      >
        <p
          v-if="viewerError"
          class="text-error"
        >
          {{ viewerError }}
        </p>
        <p v-else>
          Loading scene ({{ assetMb }} MB)…
        </p>
      </div>
    </div>

    <aside class="w-80 border-l border-default overflow-y-auto p-4 space-y-4">
      <UCard>
        <template #header>
          <h1 class="font-medium">
            {{ scene.title }}
          </h1>
        </template>

        <p>{{ scene.num_gaussians.toLocaleString() }} Gaussians</p>
        <p class="text-sm text-muted">
          PSNR {{ metric('psnr', 2) }} · SSIM {{ metric('ssim', 3) }} · LPIPS {{ metric('lpips', 3) }}
          <template v-if="scene.metrics_3dgs?.lpips_net">
            ({{ scene.metrics_3dgs?.lpips_net }})
          </template>
        </p>
        <p class="text-sm text-muted">
          FPS {{ viewer?.fps.toFixed(0) }} · asset {{ assetMb }} MB
        </p>
        <p class="text-sm text-muted">
          Drag: orbit · Right-drag: pan · Wheel: zoom
        </p>
      </UCard>
      <!-- Phase B sections (T-B15) go below -->
    </aside>
  </div>
</template>

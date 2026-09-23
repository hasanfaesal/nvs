<script setup lang="ts">
// Source: https://github.com/sparkjsdev/spark @ v2.2.0, examples/hello-world/index.html (+ examples/nonlod, examples/interactivity)
// License: MIT. Changes: Vue component; LoD disabled; initial view from manifest; FPS; click events; camera state.
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { SparkRenderer, SplatMesh } from '@sparkjsdev/spark'
import type { InitialView } from '~/composables/useApi'

const props = defineProps<{
  assetUrl: string
  initialView: InitialView
  meshQuaternion: [number, number, number, number]
}>()
const emit = defineEmits<{
  ready: [{ numSplats: number }]
  pick: [{ u: number, v: number, width: number, height: number }]
  error: [message: string]
}>()

const container = ref<HTMLDivElement>()
const canvasEl = ref<HTMLCanvasElement>()
const fps = ref(0)

// Plain (non-reactive) three.js objects.
let renderer: THREE.WebGLRenderer | undefined
let camera: THREE.PerspectiveCamera
let mesh: SplatMesh | undefined
let controls: OrbitControls | undefined
let observer: ResizeObserver | undefined
let down = { x: 0, y: 0, t: 0 }

onMounted(async () => {
  const canvas = canvasEl.value!
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: false })
    renderer.setPixelRatio(devicePixelRatio)
    const scene = new THREE.Scene()
    const view = props.initialView
    camera = new THREE.PerspectiveCamera(view.fov_y_deg, 1, 0.01, 1000)
    camera.position.fromArray(view.position)
    camera.up.fromArray(view.up)

    // LoD off everywhere: merged LoD splats would break "splat i = Gaussian i" (C11).
    scene.add(new SparkRenderer({ renderer, enableLod: false }))
    mesh = new SplatMesh({ url: props.assetUrl, lod: false, enableLod: false })
    mesh.quaternion.set(...props.meshQuaternion)
    scene.add(mesh)

    controls = new OrbitControls(camera, canvas)
    controls.target.fromArray(view.target)

    const resize = () => {
      const w = container.value!.clientWidth
      const h = container.value!.clientHeight
      if (!w || !h) return
      renderer!.setSize(w, h, false)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    observer = new ResizeObserver(resize)
    observer.observe(container.value!)
    resize()

    let frames = 0
    let windowStart = performance.now()
    renderer.setAnimationLoop(() => {
      controls!.update()
      renderer!.render(scene, camera)
      frames++
      const now = performance.now()
      if (now - windowStart >= 500) {
        fps.value = (frames * 1000) / (now - windowStart)
        frames = 0
        windowStart = now
      }
    })

    await mesh.initialized
    emit('ready', { numSplats: mesh.packedSplats?.numSplats ?? 0 })
  } catch (e) {
    emit('error', e instanceof Error ? e.message : String(e))
  }
})

onBeforeUnmount(() => {
  renderer?.setAnimationLoop(null)
  observer?.disconnect()
  controls?.dispose()
  mesh?.dispose?.()
  renderer?.dispose()
})

function onPointerDown(e: PointerEvent) {
  down = { x: e.offsetX, y: e.offsetY, t: performance.now() }
}

function onPointerUp(e: PointerEvent) {
  const moved = Math.hypot(e.offsetX - down.x, e.offsetY - down.y)
  if (moved >= 4 || performance.now() - down.t >= 300) return
  const canvas = canvasEl.value!
  emit('pick', { u: e.offsetX, v: e.offsetY, width: canvas.clientWidth, height: canvas.clientHeight })
}

// C10.5: column-major three.js elements, CSS-pixel canvas size.
function getCameraState() {
  camera.updateMatrixWorld()
  const canvas = canvasEl.value!
  return {
    matrix_world: Array.from(camera.matrixWorld.elements),
    fov_y_deg: camera.fov,
    width: canvas.clientWidth,
    height: canvas.clientHeight
  }
}

function getMeshMatrixWorld(): number[] {
  mesh!.updateMatrixWorld()
  return Array.from(mesh!.matrixWorld.elements)
}

const getSplatMesh = () => mesh

defineExpose({ getCameraState, getMeshMatrixWorld, getSplatMesh, fps })
</script>

<template>
  <div
    ref="container"
    class="relative size-full"
  >
    <canvas
      ref="canvasEl"
      class="absolute inset-0 size-full"
      @pointerdown="onPointerDown"
      @pointerup="onPointerUp"
    />
  </div>
</template>

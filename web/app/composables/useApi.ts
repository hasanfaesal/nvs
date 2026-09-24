export type InitialView = { position: number[], target: number[], up: number[], fov_y_deg: number }
export type VariantInfo = { variant: string, seeds: number[] }
export type SceneSummary = {
  scene_id: string
  title: string
  num_gaussians: number
  asset_url: string
  metrics_3dgs: Record<string, number | string> | null
  variants: VariantInfo[]
}
export type SceneDetail = SceneSummary & {
  initial_view: InitialView
  mesh_quaternion_xyzw: [number, number, number, number]
  asset: { file: string, format: string, bytes: number }
  demo_queries: string[]
}

export function useApi() {
  const getScenes = () => $fetch<SceneSummary[]>('/api/scenes')
  const getScene = (id: string) => $fetch<SceneDetail>(`/api/scenes/${encodeURIComponent(id)}`)
  return { getScenes, getScene }
}

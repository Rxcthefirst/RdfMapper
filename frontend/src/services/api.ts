async function handle<T>(promise: Promise<Response>): Promise<T> {
  const res = await promise
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return (await res.json()) as T
  try { return (await res.json()) as T } catch { return (undefined as unknown) as T }
}

export const api = {
  listProjects: () => handle<any[]>(fetch('/api/projects/')),
  getProject: (projectId: string) => handle<any>(fetch(`/api/projects/${projectId}`)),
  createProject: (data: { name: string; description?: string }) =>
    handle<any>(fetch('/api/projects/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })),
  deleteProject: (projectId: string) =>
    handle<any>(fetch(`/api/projects/${projectId}`, {
      method: 'DELETE',
    })),
  uploadData: (projectId: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return handle<any>(fetch(`/api/projects/${projectId}/upload-data`, { method: 'POST', body: fd }))
  },
  uploadOntology: (projectId: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return handle<any>(fetch(`/api/projects/${projectId}/upload-ontology`, { method: 'POST', body: fd }))
  },
  previewData: (projectId: string, limit = 10) => handle<any>(fetch(`/api/projects/${projectId}/data-preview?limit=${limit}`)),
  analyzeOntology: (projectId: string) => handle<any>(fetch(`/api/projects/${projectId}/ontology-analysis`)),
  generateMappings: (projectId: string, params?: { use_semantic?: boolean; min_confidence?: number; output_format?: string }) => {
    const qs = new URLSearchParams()
    if (params?.use_semantic !== undefined) qs.set('use_semantic', String(params.use_semantic))
    if (params?.min_confidence !== undefined) qs.set('min_confidence', String(params.min_confidence))
    if (params?.output_format) qs.set('output_format', params.output_format)
    return handle<any>(fetch(`/api/mappings/${projectId}/generate?${qs.toString()}`, { method: 'POST' }))
  },
  convertSync: (projectId: string, params?: { output_format?: string; validate?: boolean }) => {
    const qs = new URLSearchParams()
    if (params?.output_format) qs.set('output_format', params.output_format)
    if (params?.validate !== undefined) qs.set('validate', String(params.validate))
    return handle<any>(fetch(`/api/conversion/${projectId}?${qs.toString()}`, { method: 'POST' }))
  },
  convertAsync: (projectId: string, params?: { output_format?: string; validate?: boolean }) => {
    const qs = new URLSearchParams()
    qs.set('use_background', 'true')
    if (params?.output_format) qs.set('output_format', params.output_format)
    if (params?.validate !== undefined) qs.set('validate', String(params.validate))
    return handle<any>(fetch(`/api/conversion/${projectId}?${qs.toString()}`, { method: 'POST' }))
  },
  jobStatus: (taskId: string) => handle<any>(fetch(`/api/conversion/job/${taskId}`)),
  downloadRdf: (projectId: string) => fetch(`/api/conversion/${projectId}/download`),
  fetchMappingYaml: (projectId: string) =>
    fetch(`/api/mappings/${projectId}?raw=true`).then(r => {
      if (r.status === 404) return null
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.text()
    }),
  uploadShapes: (projectId: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return handle<any>(fetch(`/api/projects/${projectId}/upload-shapes`, { method: 'POST', body: fd }))
  },
  uploadSkos: (projectId: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return handle<any>(fetch(`/api/projects/${projectId}/upload-skos`, { method: 'POST', body: fd }))
  },
  uploadExistingMapping: (projectId: string, file: File, options?: {
    chunk_size?: number
    on_error?: string
    skip_empty_values?: boolean
    aggregate_duplicates?: boolean
  }) => {
    const fd = new FormData()
    fd.append('file', file)
    const params = new URLSearchParams()
    if (options?.chunk_size) params.set('chunk_size', String(options.chunk_size))
    if (options?.on_error) params.set('on_error', options.on_error)
    if (options?.skip_empty_values !== undefined) params.set('skip_empty_values', String(options.skip_empty_values))
    if (options?.aggregate_duplicates !== undefined) params.set('aggregate_duplicates', String(options.aggregate_duplicates))
    const url = `/api/projects/${projectId}/upload-existing-mapping${params.toString() ? '?' + params.toString() : ''}`
    return handle<any>(fetch(url, { method: 'POST', body: fd }))
  },
  updateSettings: async (projectId: string, settings: any) => {
    const res = await fetch(`/api/projects/${projectId}/settings`, { method: 'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify(settings) })
    if(!res.ok) throw new Error(await res.text())
    return res.json()
  },
  removeSkos: async (projectId: string, file: string) => {
    const url = new URL(`/api/projects/${projectId}/skos`, window.location.origin)
    url.searchParams.set('file', file)
    const res = await fetch(url.toString(), { method: 'DELETE' })
    if(!res.ok) throw new Error(await res.text())
    return res.json()
  },
  removeShapes: async (projectId: string) => {
    const res = await fetch(`/api/projects/${projectId}/shapes`, { method: 'DELETE' })
    if(!res.ok) throw new Error(await res.text())
    return res.json()
  },
  overrideMapping: (projectId: string, column_name: string, property_uri: string) => {
    const params = new URLSearchParams({ column_name, property_uri });
    return handle<any>(fetch(`/api/mappings/${projectId}/override?${params.toString()}`, {
      method: 'POST'
    }));
  },
  overrideNestedMapping: (
    projectId: string,
    parentEntityIndex: number,
    nestedEntityIndex: number,
    columnName: string,
    propertyUri: string
  ) => {
    const params = new URLSearchParams({
      parent_entity_index: String(parentEntityIndex),
      nested_entity_index: String(nestedEntityIndex),
      column_name: columnName,
      property_uri: propertyUri
    });
    return handle<any>(fetch(`/api/mappings/${projectId}/override-nested?${params.toString()}`, {
      method: 'POST'
    }));
  },
  addNestedEntity: (
    projectId: string,
    parentEntityIndex: number,
    joinColumn: string,
    targetClass: string,
    iriTemplate: string,
    properties: Record<string, string>
  ) => {
    return handle<any>(fetch(`/api/mappings/${projectId}/add-nested-entity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        parent_entity_index: parentEntityIndex,
        join_column: joinColumn,
        target_class: targetClass,
        iri_template: iriTemplate,
        properties
      })
    }));
  },
  deleteNestedEntity: (projectId: string, parentEntityIndex: number, nestedEntityIndex: number) => {
    const params = new URLSearchParams({
      parent_entity_index: String(parentEntityIndex),
      nested_entity_index: String(nestedEntityIndex)
    });
    return handle<any>(fetch(`/api/mappings/${projectId}/nested-entity?${params.toString()}`, {
      method: 'DELETE'
    }));
  },
  getYARRRML: (projectId: string) =>
    handle<any>(fetch(`/api/mappings/${projectId}/yarrrml`)),
  downloadYARRRML: async (projectId: string) => {
    const res = await fetch(`/api/mappings/${projectId}/yarrrml`)
    if (!res.ok) throw new Error(await res.text().catch(() => `HTTP ${res.status}`))
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${projectId}-mapping.yarrrml.yaml`
    a.click()
    URL.revokeObjectURL(url)
    return { success: true }
  },
  downloadRML: async (projectId: string, format: 'turtle' | 'xml' = 'turtle') => {
    const res = await fetch(`/api/mappings/${projectId}/rml?format=${format}`)
    if (!res.ok) throw new Error(await res.text().catch(() => `HTTP ${res.status}`))
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = format === 'xml' ? `${projectId}-mapping.rdf` : `${projectId}-mapping.rml.ttl`
    a.click()
    URL.revokeObjectURL(url)
    return { success: true }
  },
  getMappingPreview: (projectId: string, limit = 50) =>
    handle<any>(fetch(`/api/projects/${projectId}/mapping-preview?limit=${limit}`)),
  deleteDataFile: (projectId: string) =>
    handle<any>(fetch(`/api/projects/${projectId}/data-file`, { method: 'DELETE' })),
  deleteOntologyFile: (projectId: string) =>
    handle<any>(fetch(`/api/projects/${projectId}/ontology-file`, { method: 'DELETE' })),
  deleteMappingFile: (projectId: string) =>
    handle<any>(fetch(`/api/projects/${projectId}/mapping-file`, { method: 'DELETE' })),
  getColumnEvidence: (projectId: string, columnName: string) =>
    handle<any>(fetch(`/api/mappings/${projectId}/evidence/${encodeURIComponent(columnName)}`)),
  getAllEvidence: (projectId: string) =>
    handle<any>(fetch(`/api/mappings/${projectId}/evidence`)),
}

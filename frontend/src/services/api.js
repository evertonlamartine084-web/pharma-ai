import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const proteinApi = {
  list: () => api.get('/proteins/'),
  get: (id) => api.get(`/proteins/${id}`),
  getPdb: (id) => api.get(`/proteins/${id}/pdb`),
  uploadPdb: (file, name, organism) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/proteins/upload-pdb?name=${encodeURIComponent(name)}&organism=${encodeURIComponent(organism)}`, form)
  },
  addSequence: (data) => api.post('/proteins/sequence', data),
  fetchAlphafold: (data) => api.post('/proteins/alphafold', data),
  seedLeishmania: () => api.post('/proteins/seed-leishmania'),
}

export const moleculeApi = {
  list: () => api.get('/molecules/'),
  get: (id) => api.get(`/molecules/${id}`),
  add: (data) => api.post('/molecules/add', data),
  uploadCsv: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/molecules/upload-csv', form)
  },
  generate: (data) => api.post('/molecules/generate', data),
  validate: (id) => api.post(`/molecules/validate/${id}`),
  seed: () => api.post('/molecules/seed'),
  export: (format) => api.post('/molecules/export', { format }),
}

export const analysisApi = {
  list: () => api.get('/analysis/'),
  get: (id) => api.get(`/analysis/${id}`),
  validate: (moleculeId) => api.post(`/analysis/validate/${moleculeId}`),
  adme: (moleculeId) => api.post(`/analysis/adme/${moleculeId}`),
  docking: (data) => api.post('/analysis/docking', data),
  pipeline: (moleculeId, proteinId) =>
    api.post(`/analysis/pipeline/${moleculeId}?protein_id=${proteinId}`),
}

export default api

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'
const api = axios.create({ baseURL: API_URL })

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
  addSmiles: (data) => api.post('/proteins/add-smiles', data),
  fetchPdb: (pdbId, name) => api.post(`/proteins/fetch-pdb?pdb_id=${encodeURIComponent(pdbId)}&name=${encodeURIComponent(name || '')}`),
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
  adme: (moleculeId, source = 'swissadme') => api.post(`/analysis/adme/${moleculeId}?source=${source}`),
  docking: (data) => api.post('/analysis/docking', data),
  pipeline: (moleculeId, proteinId) =>
    api.post(`/analysis/pipeline/${moleculeId}?protein_id=${proteinId}`),
}

export const reportApi = {
  moleculePdf: (id) => `${API_URL}/report/molecule/${id}`,
}

export const advisorApi = {
  analyze: (moleculeId, question = null) => api.post('/advisor/analyze', { molecule_id: moleculeId, question }),
}

export const similarityApi = {
  pair: (smiles1, smiles2) => api.post('/similarity/pair', { smiles1, smiles2 }),
  find: (moleculeId, topN = 10) => api.get(`/similarity/find/${moleculeId}?top_n=${topN}`),
  matrix: (limit = 20) => api.get(`/similarity/matrix?limit=${limit}`),
}

export default api

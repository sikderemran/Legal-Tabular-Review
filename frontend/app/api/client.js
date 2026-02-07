const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class LegalReviewAPI {
    constructor() {
        this.baseURL = API_BASE_URL
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                ...options,
            })

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }))
                throw new Error(error.detail || `HTTP error! status: ${response.status}`)
            }

            return await response.json()
        } catch (error) {
            console.error('API request failed:', error)
            throw error
        }
    }

    async uploadDocuments(files) {
        const formData = new FormData()

        files.forEach(file => {
            formData.append('files', file, file.name)
        })

        const response = await fetch(`${this.baseURL}/api/documents/upload`, {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: `Upload failed: ${response.status}` }))
            throw new Error(error.detail || `Upload failed: ${response.status}`)
        }

        return await response.json()
    }

    async listDocuments() {
        return this.request('/api/documents')
    }


    async getDocument(id) {
        return this.request(`/api/documents/${id}`)
    }

    async compareDocuments(documentIds) {
        return this.request(`/api/compare`, {
            method: 'POST',
            body: JSON.stringify({
                document_ids: documentIds
            })
        })
    }


    async extractDocument(id) {
        return this.request(`/api/documents/${id}/extract`, {
            method: 'POST',
        })
    }

}

export const api = new LegalReviewAPI()
'use client'

import { useState, useEffect } from 'react'
import DocumentList from '../components/DocumentList'
import { api } from '../../app/api/client'

export default function DocumentsPage() {
  const [stats, setStats] = useState({ total: 0, processed: 0, pending: 0 })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await api.listDocuments()
      const docs = data.documents || []
      
      setStats({
        total: docs.length,
        processed: docs.filter(d => d.status === 'completed').length,
        pending: docs.filter(d => d.status !== 'completed').length
      })
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  return (
    <div className="mx-2 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Documents</h1>
        <a href="/" className="btn btn-primary">
          Upload More
        </a>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Documents</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
            <div className="bg-primary-100 p-3 rounded-full">
              <span className="text-primary-600 font-bold">📄</span>
            </div>
          </div>
        </div>
        
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Processed</p>
              <p className="text-2xl font-bold">{stats.processed}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <span className="text-green-600 font-bold">✓</span>
            </div>
          </div>
        </div>
        
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending</p>
              <p className="text-2xl font-bold">{stats.pending}</p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <span className="text-yellow-600 font-bold">⏱️</span>
            </div>
          </div>
        </div>
      </div>

      <DocumentList />
    </div>
  )
}
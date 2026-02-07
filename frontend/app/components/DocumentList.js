'use client'

import { useState, useEffect } from 'react'
import { FileText, CheckCircle, XCircle, Clock, Download } from 'lucide-react'
import { api } from '../../app/api/client'
import toast from 'react-hot-toast'

export default function DocumentList() {
    const [documents, setDocuments] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedDocs, setSelectedDocs] = useState(new Set())
    const [extracting, setExtracting] = useState(null)

    useEffect(() => {
        loadDocuments()
    }, [])

    const loadDocuments = async () => {
        try {
            setLoading(true)
            const data = await api.listDocuments()
            setDocuments(data.documents || [])
        } catch (error) {
            console.error('Error loading documents:', error)
            toast.error('Failed to load documents')
        } finally {
            setLoading(false)
        }
    }

    const handleExtract = async (docId) => {
        try {
            setExtracting(docId)
            await api.extractDocument(docId)
            toast.success('Fields extracted successfully')
            loadDocuments() 
        } catch (error) {
            console.error('Error extracting:', error)
            toast.error('Failed to extract fields')
        } finally {
            setExtracting(null)
        }
    }

    const handleSelectDoc = (docId) => {
        const newSelected = new Set(selectedDocs)
        if (newSelected.has(docId)) {
            newSelected.delete(docId)
        } else {
            newSelected.add(docId)
        }
        setSelectedDocs(newSelected)
    }

    const handleCompare = async () => {
        if (selectedDocs.size < 2) {
            toast.error('Please select at least 2 documents to compare')
            return
        }

        try {
            const docIds = Array.from(selectedDocs)
            const result = await api.compareDocuments(docIds)

            window.location.href = `/compare/${result.comparison_id}`
        } catch (error) {
            console.error('Error comparing:', error)
            toast.error('Failed to compare documents')
        }
    }

    const formatDate = (dateString) => {
        const date = new Date(dateString)
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
    }

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' Bytes'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="h-5 w-5 text-green-500" />
            case 'error':
                return <XCircle className="h-5 w-5 text-red-500" />
            default:
                return <Clock className="h-5 w-5 text-yellow-500" />
        }
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Documents</h2>
                <button
                    onClick={loadDocuments}
                    className="btn btn-secondary"
                >
                    Refresh
                </button>
            </div>

            {selectedDocs.size >= 2 && (
                <div className="card p-4 bg-primary-50 border-primary-200">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="font-medium">
                                {selectedDocs.size} documents selected
                            </p>
                            <p className="text-sm text-gray-600">
                                Ready to compare
                            </p>
                        </div>
                        <button
                            onClick={handleCompare}
                            className="btn btn-primary"
                        >
                            Compare Selected
                        </button>
                    </div>
                </div>
            )}

            {documents.length === 0 ? (
                <div className="card p-8 text-center">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No documents uploaded</h3>
                    <p className="text-gray-600 mb-4">
                        Upload some legal documents to get started
                    </p>
                    <a href="/" className="btn btn-primary">
                        Go to Upload
                    </a>
                </div>
            ) : (
                <div className="overflow-hidden card">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Select
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Document
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Size
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Uploaded
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Fields
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {documents.map((doc) => (
                                    <tr key={doc.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <input
                                                type="checkbox"
                                                checked={selectedDocs.has(doc.id)}
                                                onChange={() => handleSelectDoc(doc.id)}
                                                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                                            />
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center">
                                                <FileText className="h-5 w-5 text-gray-400 mr-3" />
                                                <div>
                                                    <p className="font-medium text-gray-900">
                                                        {doc.original_filename}
                                                    </p>
                                                    <p className="text-sm text-gray-500">
                                                        {doc.type}
                                                    </p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                {getStatusIcon(doc.status)}
                                                <span className="ml-2 capitalize">{doc.status}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatFileSize(doc.size)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatDate(doc.upload_date)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${doc.extracted_fields_count > 0
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-gray-100 text-gray-800'
                                                }`}>
                                                {doc.extracted_fields_count} fields
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            {doc.status !== 'completed' && (
                                                <button
                                                    onClick={() => handleExtract(doc.id)}
                                                    disabled={extracting === doc.id}
                                                    className="text-primary-600 hover:text-primary-900 disabled:opacity-50"
                                                >
                                                    {extracting === doc.id ? 'Extracting...' : 'Extract'}
                                                </button>
                                            )}
                                            {doc.status === 'completed' && (
                                                <button
                                                    onClick={() => window.location.href = `/documents/${doc.id}`}
                                                    className="text-primary-600 hover:text-primary-900"
                                                >
                                                    View
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
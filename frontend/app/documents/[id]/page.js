'use client'

import { useParams } from 'next/navigation'
import { useState, useEffect } from 'react'
import { Download } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../../../app/api/client'

export default function DocumentDetailPage() {
    const params = useParams()

    const [doc, setDoc] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (params.id) loadDocument()
    }, [params.id])

    const loadDocument = async () => {
        try {
            setLoading(true)
            const data = await api.getDocument(params.id)
            setDoc(data)
        } catch (err) {
            console.error(err)
            toast.error('Failed to load document')
        } finally {
            setLoading(false)
        }
    }

    const renderField = (field) =>
        Object.entries(field || {}).map(([key, value]) => (
            <div key={key} className="mb-1">
                <strong>{key}:</strong>
                <pre className="whitespace-pre-wrap">
                    {typeof value === 'object'
                        ? JSON.stringify(value, null, 2)
                        : value}
                </pre>
            </div>
        ))

    const flattenField = (field) => {
        if (!field) return ''
        return Object.entries(field)
            .map(([key, value]) =>
                typeof value === 'object'
                    ? `${key}: ${JSON.stringify(value)}`
                    : `${key}: ${value}`
            )
            .join(' | ')
    }



    const exportCSV = () => {
        if (!doc) return

        const headers = [
            'Doc Type',
            'Confidentiality',
            'Governing Law',
            'Indemnification',
            'Jurisdiction',
            'Liability',
            'Parties',
            'Termination',
            'Warranties',
        ]

        const row = [
            doc.doc_type,
            flattenField(doc.extracted_fields.confidentiality),
            flattenField(doc.extracted_fields.governing_law),
            flattenField(doc.extracted_fields.indemnification),
            flattenField(doc.extracted_fields.jurisdiction),
            flattenField(doc.extracted_fields.liability),
            flattenField(doc.extracted_fields.parties),
            flattenField(doc.extracted_fields.termination),
            flattenField(doc.extracted_fields.warranties),
        ]

        const csv = [headers, row]
            .map(r =>
                r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')
            )
            .join('\n')

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)

        const link = window.document.createElement('a')
        link.href = url
        link.download = 'document.csv'
        link.click()
    }


    if (loading || !doc) return null

    return (
        <div className="overflow-hidden card">
            <div className="flex justify-end gap-2 mb-4">
                <button
                    onClick={exportCSV}
                    className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                    <Download size={16} />
                    CSV
                </button>
            </div>

            <div className="max-h-screen overflow-y-auto overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            {[
                                'Doc Type',
                                'Confidentiality',
                                'Governing Law',
                                'Indemnification',
                                'Jurisdiction',
                                'Liability',
                                'Parties',
                                'Termination',
                                'Warranties',
                            ].map(h => (
                                <th
                                    key={h}
                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                                >
                                    {h}
                                </th>
                            ))}
                        </tr>
                    </thead>

                    <tbody className="bg-white divide-y divide-gray-200">
                        {Object.keys(doc.extracted_fields || {}).length ? (
                            <tr className="hover:bg-gray-50 align-top">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {doc.doc_type}
                                </td>
                                <td className="px-6 py-4">
                                    {renderField(doc.extracted_fields.confidentiality)}
                                </td>
                                <td className="px-6 py-4">
                                    {renderField(doc.extracted_fields.governing_law)}
                                </td>
                                <td className="px-6 py-4">
                                    {renderField(doc.extracted_fields.indemnification)}
                                </td>
                                <td className="px-6 py-4">
                                    {renderField(doc.extracted_fields.jurisdiction)}
                                </td>
                                <td className="px-6 py-4">
                                    {renderField(doc.extracted_fields.liability)}
                                </td>
                                <td className="px-6 py-4">
                                    {renderField(doc.extracted_fields.parties)}
                                </td>
                                <td className="px-6 py-4">
                                    {renderField(doc.extracted_fields.termination)}
                                </td>
                                <td className="px-6 py-4">
                                    {renderField(doc.extracted_fields.warranties)}
                                </td>
                            </tr>
                        ) : (
                            <tr>
                                <td colSpan={9} className="text-center px-6 py-4">
                                    Relevant Data Not Found
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

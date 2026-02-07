'use client'

import { useParams } from 'next/navigation'
import { useState, useEffect } from 'react'
import { Download } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../../app/api/client'
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";

export default function DocumentComparePage() {

  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [compareResult, setCompareResult] = useState(null);
  const searchParams = useSearchParams();

  useEffect(() => {
    const docIdsParam = searchParams.get("docIds");
    if (!docIdsParam) return;

    const fetchComparison = async () => {
      try {
        const docIds = JSON.parse(decodeURIComponent(docIdsParam));
        const result = await api.compareDocuments(docIds);
        console.log(result.length)
        console.log(result)
        setCompareResult(result);
      } catch (error) {
        console.error("Error comparing documents:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [searchParams]);


  if (!compareResult || compareResult.length === 0) return <p>No documents to compare</p>;


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
        typeof value === 'object' ? `${key}: ${JSON.stringify(value)}` : `${key}: ${value}`
      )
      .join(' | ')
  }

  const exportCSV = () => {
    if (!compareResult || compareResult.length === 0) return
    const headers = ['Field', ...compareResult.map(doc => doc.doc_type)]
    const fieldNames = Object.keys(compareResult[0]?.extracted_fields || {})
    const rows = fieldNames.map(field => [
      field,
      ...compareResult.map(doc => flattenField(doc.extracted_fields?.[field]) || 'N/A')
    ])
    const csv = [headers, ...rows]
      .map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(','))
      .join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'compare_result.csv'
    link.click()
  }


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
        <table
          border="1"
          cellPadding="8"
          style={{ borderCollapse: "collapse", width: "100%", tableLayout: "fixed" }}
        >
          <thead>
            <tr>
              {compareResult.map((doc, index) => (
                <th
                  key={index}
                  style={{
                    width: `${100 / compareResult.length}%`,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {doc.doc_type}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.keys(compareResult[0]?.extracted_fields || {}).map((field, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-gray-50 align-top">
                {compareResult.map((doc, colIndex) => (
                  <td
                    key={colIndex}
                    className="px-6 py-4"
                    style={{
                      width: `${100 / compareResult.length}%`,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {renderField(doc.extracted_fields?.[field]) || "N/A"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

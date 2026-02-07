'use client'

import DocumentUploader from './components/DocumentUploader'
import DocumentList from './components/DocumentList'

export default function Home() {

  return (
    <div className="flex flex-col justify-center items-center">
      <DocumentUploader />
      <DocumentList/>
    </div>
  )
}
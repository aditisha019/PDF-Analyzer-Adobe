import React, { useState, useCallback } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState('single');
  const [files, setFiles] = useState([]);
  const [persona, setPersona] = useState('PhD student');
  const [jobToBeDone, setJobToBeDone] = useState('conduct research');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = useCallback((event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
    setError(null);
  }, []);

  const handleDragOver = useCallback((event) => {
    event.preventDefault();
  }, []);

  const handleDrop = useCallback((event) => {
    event.preventDefault();
    const droppedFiles = Array.from(event.dataTransfer.files);
    const pdfFiles = droppedFiles.filter(file => file.type === 'application/pdf');
    setFiles(pdfFiles);
    setError(null);
  }, []);

  const analyzeSinglePDF = async () => {
    if (!files.length) {
      setError('Please upload a PDF file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', files[0]);

      const response = await axios.post(`${API}/analyze-pdf`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error analyzing PDF');
    } finally {
      setLoading(false);
    }
  };

  const analyzeMultiplePDFs = async () => {
    if (files.length < 3 || files.length > 10) {
      setError('Please upload between 3 and 10 PDF files');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });
      formData.append('persona', persona);
      formData.append('job_to_be_done', jobToBeDone);

      const response = await axios.post(`${API}/analyze-multiple-pdfs`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error analyzing PDFs');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFiles([]);
    setResults(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              PDF Intelligence System
            </h1>
            <p className="text-lg text-gray-600">
              Transform PDFs into intelligent, interactive experiences
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="flex mb-6 bg-white rounded-lg shadow-sm border">
            <button
              onClick={() => setActiveTab('single')}
              className={`flex-1 py-3 px-6 text-center font-medium rounded-l-lg transition-colors ${
                activeTab === 'single'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Single PDF Analysis
            </button>
            <button
              onClick={() => setActiveTab('multiple')}
              className={`flex-1 py-3 px-6 text-center font-medium rounded-r-lg transition-colors ${
                activeTab === 'multiple'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Multi-PDF Intelligence
            </button>
          </div>

          {/* Main Content */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            {/* File Upload Area */}
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6 hover:border-blue-400 transition-colors"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <svg
                className="mx-auto h-12 w-12 text-gray-400 mb-4"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <p className="text-lg text-gray-600 mb-2">
                {activeTab === 'single' ? 'Upload a PDF file' : 'Upload 3-10 PDF files'}
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Drag and drop files here, or click to browse
              </p>
              <input
                type="file"
                accept=".pdf"
                multiple={activeTab === 'multiple'}
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer transition-colors"
              >
                Browse Files
              </label>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-800 mb-3">
                  Uploaded Files ({files.length})
                </h3>
                <div className="space-y-2">
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                      <div className="flex items-center">
                        <svg className="h-5 w-5 text-red-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z"/>
                          <path fillRule="evenodd" d="M3 8h14v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8zm5 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
                        </svg>
                        <span className="text-sm text-gray-700">{file.name}</span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {(file.size / (1024 * 1024)).toFixed(1)} MB
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Multi-PDF Settings */}
            {activeTab === 'multiple' && (
              <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    User Persona
                  </label>
                  <select
                    value={persona}
                    onChange={(e) => setPersona(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="PhD student">PhD Student</option>
                    <option value="investor">Investor</option>
                    <option value="researcher">Researcher</option>
                    <option value="manager">Manager</option>
                    <option value="student">Student</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Job to be Done
                  </label>
                  <select
                    value={jobToBeDone}
                    onChange={(e) => setJobToBeDone(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="conduct research">Conduct Research</option>
                    <option value="write literature review">Write Literature Review</option>
                    <option value="analyze revenue trends">Analyze Revenue Trends</option>
                    <option value="prepare presentation">Prepare Presentation</option>
                  </select>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex space-x-4 mb-6">
              <button
                onClick={activeTab === 'single' ? analyzeSinglePDF : analyzeMultiplePDFs}
                disabled={loading || files.length === 0}
                className="flex-1 py-3 px-6 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </div>
                ) : (
                  `Analyze ${activeTab === 'single' ? 'PDF' : 'PDFs'}`
                )}
              </button>
              <button
                onClick={resetForm}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                Reset
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex">
                  <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                  </svg>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}

            {/* Results Display */}
            {results && (
              <div className="border-t pt-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">
                  Analysis Results
                </h3>
                
                {activeTab === 'single' ? (
                  <div className="space-y-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="font-medium text-blue-900">Document Title</h4>
                      <p className="text-blue-800">{results.title}</p>
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium text-gray-900">Processing Info</h4>
                        <span className="text-sm text-gray-600">
                          {results.processing_time?.toFixed(2)}s
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">
                        {results.total_pages} pages • {results.headings?.length || 0} headings found
                      </p>
                    </div>

                    <div className="space-y-3">
                      <h4 className="font-medium text-gray-900">Detected Headings</h4>
                      {results.headings?.map((heading, index) => (
                        <div key={index} className="bg-white border rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${
                                heading.level === 1 ? 'bg-red-100 text-red-800' :
                                heading.level === 2 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-green-100 text-green-800'
                              }`}>
                                H{heading.level}
                              </span>
                              <p className="mt-2 text-gray-800">{heading.text}</p>
                            </div>
                            <div className="text-right text-sm text-gray-500">
                              <p>Page {heading.page_number}</p>
                              <p>{(heading.confidence * 100).toFixed(0)}% confidence</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="font-medium text-blue-900">Analysis Settings</h4>
                      <p className="text-blue-800">
                        Persona: {results.persona} • Job: {results.job_to_be_done}
                      </p>
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium text-gray-900">Processing Info</h4>
                        <span className="text-sm text-gray-600">
                          {results.processing_time?.toFixed(2)}s
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">
                        {results.total_documents} documents • {results.relevant_sections?.length || 0} relevant sections
                      </p>
                    </div>

                    <div className="space-y-3">
                      <h4 className="font-medium text-gray-900">Relevant Sections (Ranked)</h4>
                      {results.relevant_sections?.map((section, index) => (
                        <div key={index} className="bg-white border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center">
                              <span className="inline-block w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded-full flex items-center justify-center mr-3">
                                {section.importance_rank}
                              </span>
                              <div>
                                <h5 className="font-medium text-gray-900">{section.section_title}</h5>
                                <p className="text-sm text-gray-600">{section.document_name}</p>
                              </div>
                            </div>
                            <div className="text-right text-sm text-gray-500">
                              <p>Page {section.page_number}</p>
                              <p>{(section.relevance_score * 100).toFixed(0)}% relevance</p>
                            </div>
                          </div>
                          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                            {section.key_text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
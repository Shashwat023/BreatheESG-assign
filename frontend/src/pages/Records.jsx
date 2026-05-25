import React, { useEffect, useState } from 'react';
import api from '../services/api';
import Table from '../components/common/Table';
import Badge from '../components/common/Badge';
import { format } from 'date-fns';
import { X, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

export default function Records() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');

  const fetchRecords = () => {
    setLoading(true);
    api.get('/records/')
      .then(res => setRecords(res.data.results || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  const handleReview = async (status) => {
    if (!selectedRecord) return;
    try {
      await api.post(`/records/${selectedRecord.id}/review/`, {
        status,
        notes: reviewNotes
      });
      setSelectedRecord(null);
      setReviewNotes('');
      fetchRecords(); // refresh data
    } catch (err) {
      console.error('Review failed', err);
      alert('Failed to submit review');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'approved': return <Badge variant="success">Approved</Badge>;
      case 'rejected': return <Badge variant="danger">Rejected</Badge>;
      case 'pending_review': return <Badge variant="warning">Pending Review</Badge>;
      case 'needs_clarification': return <Badge variant="info">Needs Clarification</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  const columns = [
    { header: 'Category', accessor: 'category' },
    { header: 'Activity', render: (r) => `${parseFloat(r.activity_value).toFixed(2)} ${r.activity_unit}` },
    { header: 'CO2e (kg)', render: (r) => <span className="font-semibold">{parseFloat(r.co2e).toFixed(2)}</span> },
    { header: 'Flags', render: (r) => r.is_suspicious ? <Badge variant="danger"><AlertTriangle className="w-3 h-3 mr-1 inline"/> Suspicious</Badge> : <span className="text-gray-400">-</span> },
    { header: 'Status', render: (r) => getStatusBadge(r.status) },
    { header: 'Date', render: (r) => r.period_start ? format(new Date(r.period_start), 'PP') : '-' },
  ];

  return (
    <div className="flex relative h-[calc(100vh-8rem)]">
      {/* Main Table Area */}
      <div className={`flex-1 transition-all duration-300 ${selectedRecord ? 'mr-96' : ''} overflow-y-auto pr-4`}>
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">Normalized Records</h2>
            <p className="mt-1 text-sm text-gray-500">Click a record to review traceability and approve.</p>
          </div>
        </div>
        
        {loading ? (
          <div className="text-gray-500">Loading records...</div>
        ) : (
          <Table 
            columns={columns} 
            data={records} 
            onRowClick={(record) => {
              setSelectedRecord(record);
              setReviewNotes('');
            }} 
          />
        )}
      </div>

      {/* Slide-out Panel */}
      {selectedRecord && (
        <div className="w-96 bg-white border-l border-gray-200 absolute right-0 top-0 bottom-0 shadow-xl flex flex-col overflow-hidden z-20">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900">Review Record</h3>
            <button onClick={() => setSelectedRecord(null)} className="text-gray-400 hover:text-gray-500">
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Header Info */}
            <div>
              <div className="flex justify-between items-start mb-2">
                <span className="text-sm font-medium text-gray-500">Current Status</span>
                {getStatusBadge(selectedRecord.status)}
              </div>
              <h4 className="text-xl font-bold text-gray-900">{selectedRecord.category}</h4>
              <p className="text-sm text-gray-500">{selectedRecord.subcategory}</p>
            </div>

            {/* CO2e Math */}
            <div className="bg-primary-50 rounded-lg p-4 border border-primary-100">
              <h5 className="text-sm font-semibold text-primary-900 mb-2">CO2e Calculation</h5>
              <div className="flex justify-between text-sm text-primary-700 mb-1">
                <span>Normalized Value:</span>
                <span className="font-mono">{parseFloat(selectedRecord.normalized_value).toFixed(2)} {selectedRecord.normalized_unit}</span>
              </div>
              <div className="flex justify-between text-sm text-primary-700 mb-2 border-b border-primary-200 pb-2">
                <span>Emission Factor:</span>
                <span className="font-mono">× {parseFloat(selectedRecord.emission_factor_value).toFixed(4)}</span>
              </div>
              <div className="flex justify-between text-base font-bold text-primary-900">
                <span>Total CO2e:</span>
                <span>{parseFloat(selectedRecord.co2e).toFixed(2)} kg</span>
              </div>
            </div>

            {/* Source Traceability */}
            <div>
              <h5 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                <Database className="w-4 h-4 mr-2 text-gray-400" />
                Source Traceability
              </h5>
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre className="text-xs text-green-400 font-mono">
                  {JSON.stringify(selectedRecord.raw_data, null, 2)}
                </pre>
              </div>
            </div>
            
            {/* Review Notes */}
            {selectedRecord.status === 'pending_review' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Review Notes (Optional)</label>
                <textarea
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm border p-2"
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Reason for rejection or approval..."
                />
              </div>
            )}
          </div>

          {/* Actions */}
          {selectedRecord.status === 'pending_review' && (
            <div className="p-4 border-t border-gray-200 bg-gray-50 flex flex-col gap-3">
              <button
                onClick={() => handleReview('approved')}
                className="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-success-600 hover:bg-success-700"
              >
                <CheckCircle className="w-4 h-4 mr-2" /> Approve Record
              </button>
              <div className="flex gap-3">
                <button
                  onClick={() => handleReview('rejected')}
                  className="flex-1 flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <XCircle className="w-4 h-4 mr-2 text-danger-500" /> Reject
                </button>
                <button
                  onClick={() => handleReview('needs_clarification')}
                  className="flex-1 flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Ask Originator
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

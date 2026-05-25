import React, { useEffect, useState } from 'react';
import api from '../services/api';
import Table from '../components/common/Table';
import Badge from '../components/common/Badge';
import { format } from 'date-fns';
import { X, History, User, Calendar, Database, ArrowUpDown, Shield } from 'lucide-react';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAudit, setSelectedAudit] = useState(null);
  
  // Search and Filtering state
  const [searchQuery, setSearchQuery] = useState('');
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [ordering, setOrdering] = useState('-timestamp');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Related record context state
  const [relatedRecord, setRelatedRecord] = useState(null);
  const [loadingRelated, setLoadingRelated] = useState(false);

  const fetchLogs = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (page > 1) params.append('page', page);
    if (search) params.append('search', search);
    if (actionFilter) params.append('action', actionFilter);
    if (ordering) params.append('ordering', ordering);

    const queryString = params.toString() ? `?${params.toString()}` : '';

    api.get(`/audit/logs/${queryString}`)
      .then(res => {
        setLogs(res.data.results || []);
        setTotalCount(res.data.count || 0);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
  }, [page, actionFilter, ordering, search]);

  // Fetch related record context when an audit log is selected
  useEffect(() => {
    if (selectedAudit && selectedAudit.model_name === 'NormalizedEmissionRecord') {
      setLoadingRelated(true);
      api.get(`/records/${selectedAudit.object_id}/`)
        .then(res => setRelatedRecord(res.data))
        .catch(err => {
          console.error("Failed to fetch related record", err);
          setRelatedRecord(null);
        })
        .finally(() => setLoadingRelated(false));
    } else {
      setRelatedRecord(null);
    }
  }, [selectedAudit]);

  const handleSearchSubmit = (e) => {
    if (e) e.preventDefault();
    setPage(1);
    setSearch(searchQuery);
  };

  const getActionBadge = (action) => {
    switch (action) {
      case 'approve': return <Badge variant="success">Approved</Badge>;
      case 'reject': return <Badge variant="danger">Rejected</Badge>;
      case 'create': return <Badge variant="info">Created</Badge>;
      case 'update': return <Badge variant="warning">Updated</Badge>;
      case 'flag_suspicious': return <Badge variant="danger">Flagged Suspicious</Badge>;
      case 'ingest': return <Badge variant="info">Ingested</Badge>;
      default: return <Badge>{action}</Badge>;
    }
  };

  const getModificationSummary = (log) => {
    if (log.notes && log.notes.trim()) {
      return log.notes;
    }
    switch (log.action) {
      case 'create':
        return `Created new ${log.model_name}`;
      case 'update':
        if (log.new_value) {
          const keys = Object.keys(log.new_value);
          return `Updated fields: ${keys.join(', ')}`;
        }
        return `Updated ${log.model_name}`;
      case 'delete':
        return `Deleted ${log.model_name}`;
      case 'approve':
        return 'Approved emission record';
      case 'reject':
        return 'Rejected emission record';
      case 'flag_suspicious':
        return 'System flagged record as suspicious';
      case 'ingest':
        return 'System ingested upload batch';
      default:
        return `${log.action} action on ${log.model_name}`;
    }
  };

  const getStatusChange = (log) => {
    let oldStatus = '-';
    let newStatus = '-';
    
    if (log.old_value && log.old_value.status) {
      oldStatus = log.old_value.status;
    }
    if (log.new_value && log.new_value.status) {
      newStatus = log.new_value.status;
    }
    
    if (oldStatus === '-' && newStatus === '-') {
      if (log.action === 'approve') {
        oldStatus = 'pending_review';
        newStatus = 'approved';
      } else if (log.action === 'reject') {
        oldStatus = 'pending_review';
        newStatus = 'rejected';
      }
    }
    
    return { oldStatus, newStatus };
  };

  const columns = [
    { 
      header: 'Timestamp', 
      render: (log) => log.timestamp ? format(new Date(log.timestamp), 'PP pp') : '-' 
    },
    { 
      header: 'Analyst/User', 
      render: (log) => (
        <span className="flex items-center text-gray-700 font-medium">
          <User className="w-3.5 h-3.5 mr-1 text-gray-400" />
          {log.actor}
        </span>
      ) 
    },
    { 
      header: 'Action Type', 
      render: (log) => getActionBadge(log.action) 
    },
    { 
      header: 'Record ID', 
      render: (log) => <span className="font-mono text-gray-500">#{log.object_id}</span>
    },
    { 
      header: 'Prev Status', 
      render: (log) => {
        const { oldStatus } = getStatusChange(log);
        return oldStatus !== '-' ? (
          <span className="text-gray-600 capitalize">{oldStatus.replace('_', ' ')}</span>
        ) : (
          <span className="text-gray-400">-</span>
        );
      } 
    },
    { 
      header: 'New Status', 
      render: (log) => {
        const { newStatus } = getStatusChange(log);
        return newStatus !== '-' ? (
          <span className="text-gray-900 font-semibold capitalize">{newStatus.replace('_', ' ')}</span>
        ) : (
          <span className="text-gray-400">-</span>
        );
      } 
    },
    { 
      header: 'Modification Summary', 
      render: (log) => <span className="text-gray-600 truncate max-w-xs block">{getModificationSummary(log)}</span>
    },
  ];

  return (
    <div className="flex relative h-[calc(100vh-8rem)]">
      {/* Main Table Area */}
      <div className={`flex-1 transition-all duration-300 ${selectedAudit ? 'mr-96' : ''} overflow-y-auto pr-4`}>
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 flex items-center">
            <Shield className="w-6 h-6 mr-2 text-primary-600" />
            Immutable Audit Logs
          </h2>
          <p className="mt-1 text-sm text-gray-500">Legal audit trail tracking all data creations, updates, and reviewer actions.</p>
        </div>

        {/* Filters and Actions */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 mb-6 flex flex-wrap gap-4 items-end">
          {/* Search */}
          <form onSubmit={handleSearchSubmit} className="flex-1 min-w-[240px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Search Actor / Summary</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded-md text-sm p-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Search actor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>

          {/* Action Filter */}
          <div className="w-48">
            <label className="block text-xs font-medium text-gray-500 mb-1">Action</label>
            <select
              value={actionFilter}
              onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
              className="w-full border border-gray-300 rounded-md text-sm p-2 bg-white focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Actions</option>
              <option value="create">Created</option>
              <option value="update">Updated</option>
              <option value="approve">Approved</option>
              <option value="reject">Rejected</option>
              <option value="flag_suspicious">Flagged Suspicious</option>
              <option value="ingest">Ingested</option>
            </select>
          </div>

          {/* Sort Order */}
          <div className="w-48">
            <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
              <ArrowUpDown className="w-3 h-3 mr-1" />
              Timestamp Sort
            </label>
            <select
              value={ordering}
              onChange={(e) => { setOrdering(e.target.value); setPage(1); }}
              className="w-full border border-gray-300 rounded-md text-sm p-2 bg-white focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="-timestamp">Newest First</option>
              <option value="timestamp">Oldest First</option>
            </select>
          </div>

          {/* Reset Filters */}
          <button
            onClick={() => {
              setSearchQuery('');
              setSearch('');
              setActionFilter('');
              setOrdering('-timestamp');
              setPage(1);
            }}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            Reset
          </button>
        </div>

        {loading ? (
          <div className="text-gray-500 py-6">Loading audit trail...</div>
        ) : (
          <>
            <Table 
              columns={columns} 
              data={logs} 
              onRowClick={(log) => setSelectedAudit(log)} 
            />

            {/* Pagination Controls */}
            {totalCount > 50 && (
              <div className="flex justify-between items-center mt-6 bg-white p-4 rounded-lg border border-gray-200">
                <span className="text-sm text-gray-500">
                  Showing <span className="font-semibold">{(page - 1) * 50 + 1}</span> to <span className="font-semibold">{Math.min(page * 50, totalCount)}</span> of <span className="font-semibold">{totalCount}</span> logs
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={page === 1}
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    className="px-3 py-1 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Previous
                  </button>
                  <button
                    disabled={page * 50 >= totalCount}
                    onClick={() => setPage(p => p + 1)}
                    className="px-3 py-1 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Side Panel for Audit Log Detail */}
      {selectedAudit && (
        <div className="w-96 bg-white border-l border-gray-200 absolute right-0 top-0 bottom-0 shadow-xl flex flex-col overflow-hidden z-20">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <History className="w-4 h-4 mr-2 text-gray-500" />
              Audit Log Details
            </h3>
            <button onClick={() => setSelectedAudit(null)} className="text-gray-400 hover:text-gray-500">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Meta Info */}
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Action</span>
                {getActionBadge(selectedAudit.action)}
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Actor</span>
                <span className="font-semibold text-gray-800 flex items-center">
                  <User className="w-3.5 h-3.5 mr-1 text-gray-400" />
                  {selectedAudit.actor}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Timestamp</span>
                <span className="text-gray-700 flex items-center">
                  <Calendar className="w-3.5 h-3.5 mr-1 text-gray-400" />
                  {selectedAudit.timestamp ? format(new Date(selectedAudit.timestamp), 'PP pp') : '-'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Target Model</span>
                <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-800">{selectedAudit.model_name}</span>
              </div>
              <div className="flex justify-between text-sm border-b border-gray-200 pb-3">
                <span className="text-gray-500">Entity ID</span>
                <span className="font-mono text-gray-700 font-semibold">#{selectedAudit.object_id}</span>
              </div>
            </div>

            {/* Description Notes */}
            {selectedAudit.notes && (
              <div className="bg-gray-50 p-3 rounded border border-gray-200 text-sm text-gray-700">
                <h5 className="font-semibold text-xs text-gray-500 uppercase mb-1">Notes</h5>
                <p>{selectedAudit.notes}</p>
              </div>
            )}

            {/* State JSON Diffs */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">JSON State Diff</h4>
              
              {selectedAudit.old_value && Object.keys(selectedAudit.old_value).length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-danger-600 block mb-1">Previous Values (Before)</span>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 overflow-x-auto">
                    <pre className="text-xs text-red-800 font-mono">
                      {JSON.stringify(selectedAudit.old_value, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {selectedAudit.new_value && Object.keys(selectedAudit.new_value).length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-success-600 block mb-1">New Values (After)</span>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 overflow-x-auto">
                    <pre className="text-xs text-green-800 font-mono">
                      {JSON.stringify(selectedAudit.new_value, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {(!selectedAudit.old_value || Object.keys(selectedAudit.old_value).length === 0) &&
               (!selectedAudit.new_value || Object.keys(selectedAudit.new_value).length === 0) && (
                <div className="text-sm text-gray-500 italic bg-gray-50 p-3 rounded border border-gray-200">
                  No raw changes recorded in this entry.
                </div>
              )}
            </div>

            {/* Associated Normalized Record Context */}
            {selectedAudit.model_name === 'NormalizedEmissionRecord' && (
              <div className="border-t border-gray-200 pt-6">
                <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3 flex items-center">
                  <Database className="w-4 h-4 mr-2 text-gray-400" />
                  Related Record Current State
                </h4>
                
                {loadingRelated ? (
                  <div className="text-sm text-gray-500 italic">Fetching related record context...</div>
                ) : relatedRecord ? (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-semibold text-gray-500 uppercase">Category</span>
                      <span className="text-sm text-gray-900 font-semibold text-right max-w-[180px]">{relatedRecord.category}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-500">Activity</span>
                      <span className="font-medium text-gray-800">
                        {relatedRecord.activity_value ? parseFloat(relatedRecord.activity_value).toFixed(2) : '-'} {relatedRecord.activity_unit}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-500">CO2e Calculation</span>
                      <span className="font-semibold text-primary-700">
                        {relatedRecord.co2e ? parseFloat(relatedRecord.co2e).toFixed(2) : '-'} kg CO2e
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-sm border-t border-gray-200 pt-2">
                      <span className="text-gray-500">Current Status</span>
                      <span className="text-sm capitalize font-medium">{relatedRecord.status.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-500">Source Type</span>
                      <span className="text-sm capitalize font-medium">{relatedRecord.source_type}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-500">Tenant Org</span>
                      <span className="text-sm font-medium">{relatedRecord.organization_name}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-400 italic">
                    The related record could not be fetched (it may have been deleted).
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

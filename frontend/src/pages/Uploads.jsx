import React, { useEffect, useState } from 'react';
import api from '../services/api';
import Table from '../components/common/Table';
import Badge from '../components/common/Badge';
import { format } from 'date-fns';

export default function Uploads() {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/uploads/')
      .then(res => setUploads(res.data.results || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'complete': return <Badge variant="success">Complete</Badge>;
      case 'processing': return <Badge variant="warning">Processing</Badge>;
      case 'failed': return <Badge variant="danger">Failed</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  const columns = [
    { header: 'File Name', accessor: 'original_filename' },
    { header: 'Source Type', accessor: 'source_type', render: (r) => <span className="capitalize">{r.source_type}</span> },
    { header: 'Organization', accessor: 'organization_name' },
    { header: 'Total Rows', accessor: 'total_rows' },
    { header: 'Status', accessor: 'status', render: (r) => getStatusBadge(r.status) },
    { header: 'Timestamp', accessor: 'ingestion_timestamp', render: (r) => format(new Date(r.ingestion_timestamp), 'PP pp') },
  ];

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Data Uploads</h2>
        <p className="mt-1 text-sm text-gray-500">History of all ingestion batches processed by the platform.</p>
      </div>
      
      {loading ? (
        <div className="text-gray-500">Loading uploads...</div>
      ) : (
        <Table columns={columns} data={uploads} />
      )}
    </div>
  );
}

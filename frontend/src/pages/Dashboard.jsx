import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Activity, AlertCircle, CheckCircle2, FileText } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app, we'd have a specific dashboard stats endpoint.
    // For now, we'll fetch records to simulate KPI calculation.
    const fetchStats = async () => {
      try {
        const [uploadsRes, recordsRes] = await Promise.all([
          api.get('/uploads/?page_size=1000'),
          api.get('/records/?page_size=1000')
        ]);
        
        const records = recordsRes.data.results || [];
        const suspicious = records.filter(r => r.is_suspicious).length;
        const pending = records.filter(r => r.status === 'pending_review').length;
        const totalCo2e = records.reduce((sum, r) => sum + parseFloat(r.co2e || 0), 0);

        setStats({
          totalUploads: uploadsRes.data.count,
          suspiciousRows: suspicious,
          pendingReviews: pending,
          totalCo2e: totalCo2e.toFixed(2)
        });
      } catch (err) {
        console.error('Failed to load stats', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="text-gray-500">Loading dashboard...</div>;
  if (!stats) return <div className="text-red-500">Failed to load data</div>;

  const cards = [
    { name: 'Total Uploads', value: stats.totalUploads, icon: FileText, color: 'text-primary-600', bg: 'bg-primary-50' },
    { name: 'Pending Approvals', value: stats.pendingReviews, icon: Activity, color: 'text-warning-600', bg: 'bg-warning-50' },
    { name: 'Suspicious Rows', value: stats.suspiciousRows, icon: AlertCircle, color: 'text-danger-600', bg: 'bg-danger-50' },
    { name: 'Total CO2e (kg)', value: stats.totalCo2e, icon: CheckCircle2, color: 'text-success-600', bg: 'bg-success-50' },
  ];

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Overview</h2>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.name} className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className={`p-3 rounded-md ${card.bg}`}>
                      <Icon className={`h-6 w-6 ${card.color}`} aria-hidden="true" />
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">{card.name}</dt>
                      <dd>
                        <div className="text-2xl font-bold text-gray-900">{card.value}</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

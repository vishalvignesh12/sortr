'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Activity, AlertTriangle, CheckCircle, Clock, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  status: 'good' | 'warning' | 'error';
}

interface Alert {
  type: 'info' | 'warning' | 'error';
  message: string;
  time: string;
}

export function PerformanceMonitor() {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data in case API call fails
  const mockMetrics: PerformanceMetric[] = [
    { name: 'System Response', value: 94, unit: 'ms', status: 'good' },
    { name: 'Database Connection', value: 100, unit: '%', status: 'good' },
    { name: 'Cache Hit Rate', value: 87, unit: '%', status: 'good' },
    { name: 'Error Rate', value: 0.2, unit: '%', status: 'good' },
  ];

  const mockAlerts: Alert[] = [
    { type: 'info', message: 'System running optimally', time: '2 min ago' },
    { type: 'warning', message: 'Database query time increased', time: '1 hour ago' },
    { type: 'info', message: 'Daily backup completed', time: '6 hours ago' },
  ];

  useEffect(() => {
    const fetchPerformanceData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // In the full implementation, this would fetch data from the backend
        // Example: const response = await apiClient.get('/admin/stats');
        
        // For now, using mock data but in a real system, this would fetch
        // from the backend's monitoring endpoints
        setMetrics(mockMetrics);
        setAlerts(mockAlerts);
      } catch (err) {
        console.error('Error fetching performance data:', err);
        setError('Failed to load performance metrics. Using default values.');
        setMetrics(mockMetrics);
        setAlerts(mockAlerts);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPerformanceData();
  }, []);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 animate-spin" />
            <p>Loading performance data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {metrics.map((metric, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>{metric.name}</span>
                  <span className="font-medium">
                    {metric.value}{metric.unit}
                    <span className={`ml-2 ${
                      metric.status === 'good' ? 'text-green-500' : 
                      metric.status === 'warning' ? 'text-yellow-500' : 'text-red-500'
                    }`}>
                      {metric.status === 'good' ? (
                        <CheckCircle className="inline h-4 w-4" />
                      ) : (
                        <AlertTriangle className="inline h-4 w-4" />
                      )}
                    </span>
                  </span>
                </div>
                <Progress value={metric.value} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Recent Alerts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {alerts.map((alert, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className={`mt-1 h-2 w-2 rounded-full ${
                  alert.type === 'warning' ? 'bg-yellow-500' : 
                  alert.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
                }`}></div>
                <div className="flex-1">
                  <p className="text-sm">{alert.message}</p>
                  <p className="text-xs text-muted-foreground">{alert.time}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';

interface OccupancyData {
  day: string;
  occupancy: number;
}

interface RevenueData {
  month: string;
  revenue: number;
}

export function DashboardSummary() {
  const [occupancyData, setOccupancyData] = useState<OccupancyData[]>([]);
  const [revenueData, setRevenueData] = useState<RevenueData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data in case API call fails
  const mockOccupancyData: OccupancyData[] = [
    { day: 'Mon', occupancy: 45 },
    { day: 'Tue', occupancy: 52 },
    { day: 'Wed', occupancy: 68 },
    { day: 'Thu', occupancy: 72 },
    { day: 'Fri', occupancy: 85 },
    { day: 'Sat', occupancy: 92 },
    { day: 'Sun', occupancy: 78 },
  ];

  const mockRevenueData: RevenueData[] = [
    { month: 'Jan', revenue: 12400 },
    { month: 'Feb', revenue: 18900 },
    { month: 'Mar', revenue: 17200 },
    { month: 'Apr', revenue: 21000 },
    { month: 'May', revenue: 23500 },
    { month: 'Jun', revenue: 24890 },
  ];

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // In a real implementation, this would fetch analytics from the backend
        // Example: 
        // const occupancyResponse = await apiClient.get('/analytics/occupancy-trend');
        // const revenueResponse = await apiClient.get('/analytics/revenue');
        
        // For now, using mock data but in a real system, this would come from the backend
        setOccupancyData(mockOccupancyData);
        setRevenueData(mockRevenueData);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Using default values.');
        setOccupancyData(mockOccupancyData);
        setRevenueData(mockRevenueData);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analytics Charts</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 animate-spin" />
            <p>Loading analytics...</p>
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
          <CardTitle>Weekly Occupancy Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={occupancyData}>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="occupancy" 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                fillOpacity={0.2} 
                strokeWidth={2} 
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Monthly Revenue</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="revenue" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, TrendingDown, Clock, Car, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getSlotPredictions } from '@/lib/data';

interface PredictionData {
  title: string;
  value: string;
  change: string;
  trend: 'positive' | 'negative';
  time: string;
}

export function PredictionDisplay() {
  const [predictions, setPredictions] = useState<PredictionData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data in case API call fails
  const mockPredictions: PredictionData[] = [
    {
      title: "Tomorrow's Occupancy",
      value: "78%",
      change: "+5.2%",
      trend: "positive",
      time: "Based on historical data and weather forecast"
    },
    {
      title: "Peak Busy Period",
      value: "5:00 PM - 6:30 PM",
      change: "+30 min",
      trend: "positive",
      time: "Expected congestion window"
    },
    {
      title: "Available Spots (Next Hour)",
      value: "23",
      change: "-8",
      trend: "negative",
      time: "Predicted decrease in availability"
    },
    {
      title: "Average Stay Duration",
      value: "2.4 hrs",
      change: "-0.3",
      trend: "positive",
      time: "Efficiency improvement"
    }
  ];

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // In the full implementation, you would use the backend API
        // For now, we'll use mock data but you can implement API calls
        // to the backend prediction service
        // Example: const response = await getSlotPredictions('some-slot-id');
        
        // Using mock data for now - in a real implementation, this would
        // fetch data from the backend prediction API
        setPredictions(mockPredictions);
      } catch (err) {
        console.error('Error fetching predictions:', err);
        setError('Failed to load predictions. Using default values.');
        setPredictions(mockPredictions);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPredictions();
  }, []);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Predictive Analytics</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 animate-spin" />
            <p>Loading predictions...</p>
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
          <CardTitle>Predictive Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {predictions.map((prediction, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium">{prediction.title}</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold">{prediction.value}</span>
                    <span className={`text-sm ${
                      prediction.trend === 'positive' ? 'text-green-500' : 'text-red-500'
                    }`}>
                      {prediction.change}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>{prediction.time}</span>
                </div>
                <Progress 
                  value={prediction.trend === 'positive' 
                    ? Math.min(100, parseInt(prediction.value.replace('%', '')) || 50) 
                    : 100 - (parseInt(prediction.value.replace('%', '')) || 50)
                  } 
                  className="h-2" 
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
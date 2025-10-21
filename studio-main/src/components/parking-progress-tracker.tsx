'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Car, Clock, DollarSign, Calendar } from 'lucide-react';

const progressMetrics = [
  { 
    title: 'Monthly Target', 
    current: 85000, 
    target: 100000, 
    unit: '$',
    icon: DollarSign,
    color: 'bg-blue-500'
  },
  { 
    title: 'Daily Utilization', 
    current: 94, 
    target: 100, 
    unit: '%',
    icon: Car,
    color: 'bg-green-500'
  },
  { 
    title: 'Avg. Stay Duration', 
    current: 2.4, 
    target: 2.5, 
    unit: 'hrs',
    icon: Clock,
    color: 'bg-purple-500'
  },
  { 
    title: 'Maintenance Schedule', 
    current: 95, 
    target: 100, 
    unit: '%',
    icon: Calendar,
    color: 'bg-orange-500'
  },
];

export function ParkingProgressTracker() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Progress Tracking</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {progressMetrics.map((metric, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <metric.icon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{metric.title}</span>
                </div>
                <span className="text-sm font-medium">
                  {metric.current}{metric.unit} / {metric.target}{metric.unit}
                </span>
              </div>
              <Progress 
                value={(metric.current / metric.target) * 100} 
                className="h-2" 
                indicatorColor={metric.color}
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
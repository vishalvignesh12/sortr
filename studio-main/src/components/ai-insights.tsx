'use client';

import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Calendar, Clock, Car } from 'lucide-react';
import { ReactNode } from 'react';

const MotionDiv = dynamic(
  () => import('framer-motion').then((mod) => mod.motion.div),
  { ssr: false }
);

type InsightType = {
  title: string;
  description: string;
  impact: string;
  icon: React.ComponentType<{ className?: string }>;
  trend: 'positive' | 'negative';
};

export function AIInsights() {
  const insights: InsightType[] = [
    {
      title: "Peak Hours Prediction",
      description: "Predicted peak hours are 7-9 AM and 5-7 PM on weekdays",
      impact: "Optimize staff scheduling and pricing",
      icon: Clock,
      trend: "positive"
    },
    {
      title: "Demand Forecast",
      description: "Anticipated 15% increase in demand next week",
      impact: "Prepare for higher occupancy rates",
      icon: TrendingUp,
      trend: "positive"
    },
    {
      title: "Revenue Optimization",
      description: "Dynamic pricing could increase revenue by 12%",
      impact: "Consider implementing variable rates",
      icon: Car,
      trend: "positive"
    },
    {
      title: "Maintenance Alert",
      description: "Zone C needs maintenance in the next 3 days",
      impact: "Schedule maintenance to prevent issues",
      icon: Calendar,
      trend: "negative"
    }
  ];

  return (
    <MotionDiv 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <Card>
        <CardHeader>
          <MotionDiv
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <CardTitle>AI-Powered Insights</CardTitle>
          </MotionDiv>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.map((insight, index) => {
              const IconComponent = insight.icon;
              return (
                <MotionDiv 
                  key={index} 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  whileHover={{ y: -5, boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)" }}
                  className="border rounded-lg p-4 cursor-pointer transition-all duration-300"
                >
                  <div className="flex items-start gap-3">
                    <MotionDiv 
                      whileHover={{ scale: 1.1 }}
                      className={`p-2 rounded-lg ${
                        insight.trend === 'positive' 
                          ? 'bg-green-500/10 text-green-500' 
                          : 'bg-red-500/10 text-red-500'
                      }`}
                    >
                      <IconComponent className="h-5 w-5" />
                    </MotionDiv>
                    <div>
                      <h3 className="font-semibold">{insight.title}</h3>
                      <p className="text-sm text-muted-foreground mt-1">{insight.description}</p>
                      <p className="text-xs mt-2 text-primary">{insight.impact}</p>
                    </div>
                  </div>
                </MotionDiv>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </MotionDiv>
  );
}
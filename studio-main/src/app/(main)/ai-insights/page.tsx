'use client';

import dynamic from 'next/dynamic';
import { AIInsights } from '@/components/ai-insights';
import { AIParkingAssistant } from '@/components/ai-parking-assistant';
import { PredictionDisplay } from '@/components/prediction-display';

const MotionDiv = dynamic(
  () => import('framer-motion').then((mod) => mod.motion.div),
  { ssr: false }
);

export default function AIInsightsPage() {
  return (
    <MotionDiv 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <MotionDiv
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          AI Insights & Predictions
        </h1>
        <p className="mt-2 text-muted-foreground">
          Intelligent predictions and insights for parking management.
        </p>
      </MotionDiv>

      <MotionDiv
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        <div className="lg:col-span-2 space-y-4">
          <PredictionDisplay />
        </div>
        <div className="space-y-4">
          <AIParkingAssistant />
        </div>
      </MotionDiv>

      <MotionDiv
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <AIInsights />
      </MotionDiv>
    </MotionDiv>
  );
}
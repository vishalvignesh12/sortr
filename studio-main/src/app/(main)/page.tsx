'use client';

import { SlotGrid } from '@/components/slot-grid';
import { Dashboard } from '@/components/dashboard';
import { getSlots } from '@/lib/data';
import { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuth } from '@/context/AuthContext';
import { motion } from 'framer-motion';

export default function HomePage() {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <WelcomeSection />
      <Suspense fallback={<DashboardSkeleton />}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <DashboardLoader />
        </motion.div>
      </Suspense>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <h2 className="text-xl font-semibold mb-4">Slot Grid View</h2>
        <SlotGrid />
      </motion.div>
    </motion.div>
  );
}

function WelcomeSection() {
  const { user } = useAuth();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h1 className="text-3xl font-bold tracking-tight text-foreground">
        Welcome back, {user?.name || 'User'}!
      </h1>
      <p className="mt-2 text-muted-foreground">
        Here's the real-time status of all parking slots.
      </p>
    </motion.div>
  );
}

async function DashboardLoader() {
  const slots = await getSlots();
  return <Dashboard slots={slots} />;
}

function DashboardSkeleton() {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="h-24 rounded-lg" />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Skeleton className="h-64 rounded-lg" />
          <Skeleton className="h-48 rounded-lg" />
        </div>
        <Skeleton className="h-[500px] rounded-lg" />
      </div>
      
      <div>
        <Skeleton className="h-8 w-64 mb-4" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {Array.from({ length: 12 }).map((_, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
            >
              <Skeleton className="h-32 rounded-lg" />
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

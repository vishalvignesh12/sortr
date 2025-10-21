'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { ParkingSlot } from '@/lib/types';
import { Clock } from 'lucide-react';
import { formatDistanceStrict } from 'date-fns';
import { motion } from 'framer-motion';

type SlotCardProps = {
  slot: ParkingSlot;
  now: Date;
};

export function SlotCard({ slot, now }: SlotCardProps) {
  const isOccupied = slot.status === 'Occupied';

  const duration =
    isOccupied && slot.occupiedSince
      ? formatDistanceStrict(new Date(slot.occupiedSince), now)
      : 'N/A';

  return (
    <Link href={`/slot/${slot.id}`} className="block">
      <motion.div
        whileHover={{ y: -5, scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        <Card
          className={cn(
            'h-full transition-all duration-300 ease-in-out',
            isOccupied
              ? 'bg-card text-card-foreground border-destructive/50'
              : 'bg-green-500/20 text-green-800 dark:bg-green-500/10 dark:text-green-300 border-green-500/30'
          )}
        >
          <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-2xl font-bold">{slot.id}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">{slot.status}</div>
            {isOccupied && (
              <div className="mt-2 flex items-center text-xs opacity-80">
                <Clock className="mr-1 h-3 w-3" />
                <span>{duration}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </Link>
  );
}

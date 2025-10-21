'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Car, 
  MapPin, 
  Clock, 
  Calendar, 
  Navigation,
  Wifi,
  Coffee,
  Utensils,
  ShoppingBag
} from 'lucide-react';
import { format } from 'date-fns';
import { motion } from 'framer-motion';

interface Slot {
  id: string;
  status: 'Free' | 'Occupied';
  occupiedSince?: string;
  level?: string;
}

interface SlotGridProps {
  slots?: Slot[];
}

export function SlotGrid({ slots }: SlotGridProps) {
  // If no slots are provided, create a sample grid
  const slotList = slots || Array.from({ length: 45 }, (_, i) => {
    const level = ['A', 'B', 'C'][Math.floor(i / 15)];
    const number = (i % 15) + 1;
    const id = `${level}-${String(number).padStart(3, '0')}`;
    return {
      id,
      status: Math.random() > 0.7 ? 'Occupied' : 'Free',
      level
    };
  });

  // Group slots by level
  const slotsByLevel: Record<string, Slot[]> = {};
  slotList.forEach(slot => {
    if (!slotsByLevel[slot.level || 'A']) {
      slotsByLevel[slot.level || 'A'] = [];
    }
    slotsByLevel[slot.level || 'A'].push(slot);
  });

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex justify-between items-center"
      >
        <h2 className="text-2xl font-bold">Parking Levels</h2>
        <div className="flex gap-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm bg-green-500"></div>
            <span className="text-sm">Free</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm bg-red-500"></div>
            <span className="text-sm">Occupied</span>
          </div>
        </div>
      </motion.div>

      {Object.entries(slotsByLevel).map(([level, levelSlots], levelIndex) => (
        <motion.div
          key={level}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: levelIndex * 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Level {level}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-15 gap-2">
                {levelSlots.map((slot, index) => (
                  <motion.div
                    key={slot.id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: index * 0.01 }}
                  >
                    <Button
                      variant={slot.status === 'Occupied' ? "destructive" : "default"}
                      className={`h-12 w-12 p-0 text-xs flex-col gap-1 ${
                        slot.status === 'Occupied' ? 'bg-red-500 hover:bg-red-500' : 'bg-green-500 hover:bg-green-500'
                      }`}
                    >
                      <span className="font-bold">{slot.id.split('-')[1]}</span>
                      <span className="text-[0.6rem]">{slot.status === 'Occupied' ? 'BUSY' : 'FREE'}</span>
                    </Button>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Amenities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { icon: Wifi, text: 'Free WiFi', color: 'text-blue-500' },
                { icon: Coffee, text: 'Coffee Shop', color: 'text-amber-500' },
                { icon: Utensils, text: 'Food Court', color: 'text-green-500' },
                { icon: ShoppingBag, text: 'Shopping Area', color: 'text-purple-500' }
              ].map((amenity, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="flex items-center gap-2"
                >
                  <amenity.icon className={`h-5 w-5 ${amenity.color}`} />
                  <span>{amenity.text}</span>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
'use client';

import { useState } from 'react';
import { ParkingSlot } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Map, Car, Home } from 'lucide-react';

interface ParkingMapViewProps {
  slots: ParkingSlot[];
  selectedLevel: string;
  onLevelChange: (level: string) => void;
}

export function ParkingMapView({ slots, selectedLevel, onLevelChange }: ParkingMapViewProps) {
  // Get available levels
  const levels = Array.from(
    new Set(slots.map(slot => slot.id.split('-')[0]))
  ).sort();

  // Filter slots by selected level
  const filteredSlots = slots.filter(slot => 
    selectedLevel ? slot.id.startsWith(`${selectedLevel}-`) : true
  );

  // Sort slots by number (after the dash)
  const sortedSlots = [...filteredSlots].sort((a, b) => {
    const numA = parseInt(a.id.split('-')[1]);
    const numB = parseInt(b.id.split('-')[1]);
    return numA - numB;
  });

  // Group slots into rows (10 slots per row)
  const slotsPerRow = 10;
  const rows = [];
  for (let i = 0; i < sortedSlots.length; i += slotsPerRow) {
    rows.push(sortedSlots.slice(i, i + slotsPerRow));
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>
            <Map className="inline mr-2 h-5 w-5" />
            Parking Map {selectedLevel && `- Level ${selectedLevel}`}
          </CardTitle>
          
          <div className="flex space-x-2">
            {levels.map(level => (
              <Button
                key={level}
                variant={selectedLevel === level ? 'default' : 'outline'}
                size="sm"
                onClick={() => onLevelChange(level)}
              >
                {level}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {rows.map((row, rowIndex) => (
            <div key={rowIndex} className="flex space-x-2 justify-center">
              {row.map(slot => (
                <div 
                  key={slot.id} 
                  className={`
                    w-12 h-12 rounded-md flex items-center justify-center text-xs font-medium
                    ${slot.status === 'Free' 
                      ? 'bg-green-100 text-green-800 border border-green-300' 
                      : 'bg-red-100 text-red-800 border border-red-300'}
                  `}
                  title={`${slot.id} - ${slot.status}${slot.occupiedSince ? `\nOccupied since: ${new Date(slot.occupiedSince).toLocaleString()}` : ''}`}
                >
                  {slot.id.split('-')[1]}
                </div>
              ))}
            </div>
          ))}
          
          {sortedSlots.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No slots available for the selected level
            </div>
          )}
        </div>
        
        <div className="flex items-center mt-6 space-x-4">
          <div className="flex items-center">
            <div className="w-4 h-4 rounded bg-green-100 border border-green-300 mr-2"></div>
            <span className="text-sm">Free</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded bg-red-100 border border-red-300 mr-2"></div>
            <span className="text-sm">Occupied</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
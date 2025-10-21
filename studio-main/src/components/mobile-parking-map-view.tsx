'use client';

import { useState, useEffect } from 'react';
import { ParkingSlot } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Map as MapIcon, 
  Filter, 
  Car, 
  Home, 
  ChevronLeft, 
  ChevronRight,
  RotateCcw
} from 'lucide-react';

interface MobileParkingMapViewProps {
  slots: ParkingSlot[];
  selectedLevel: string;
  onLevelChange: (level: string) => void;
}

export function MobileParkingMapView({ slots, selectedLevel, onLevelChange }: MobileParkingMapViewProps) {
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

  // Group slots into rows (6 slots per row for mobile)
  const slotsPerRow = 6;
  const rows = [];
  for (let i = 0; i < sortedSlots.length; i += slotsPerRow) {
    rows.push(sortedSlots.slice(i, i + slotsPerRow));
  }

  // Pagination for large numbers of slots
  const [currentPage, setCurrentPage] = useState(0);
  const slotsPerPage = 18; // 3 rows of 6 slots each
  const totalPages = Math.ceil(rows.length / 3);

  const currentRows = rows.slice(
    currentPage * 3, 
    Math.min((currentPage + 1) * 3, rows.length)
  );

  return (
    <Card className="w-full">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 pb-4">
        <CardTitle className="flex items-center gap-2 flex-1">
          <MapIcon className="h-5 w-5" />
          Parking Map
        </CardTitle>
        
        <div className="flex flex-wrap gap-2">
          {levels.map(level => (
            <Button
              key={level}
              variant={selectedLevel === level ? 'default' : 'outline'}
              size="sm"
              onClick={() => {
                onLevelChange(level);
                setCurrentPage(0); // Reset to first page when level changes
              }}
              className="text-xs px-3 py-1"
            >
              {level}
            </Button>
          ))}
        </div>
      </div>
      
      <CardContent>
        <div className="mb-4 flex justify-between items-center text-sm">
          <span className="text-muted-foreground">
            Showing {Math.min(currentPage * 18 + 1, rows.length * 6)} - {Math.min((currentPage + 1) * 18, filteredSlots.length)} of {filteredSlots.length} slots
          </span>
          
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
              disabled={currentPage === 0}
              className="px-2 py-1 h-8"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            
            <span className="flex items-center px-2">
              {currentPage + 1} / {totalPages || 1}
            </span>
            
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
              disabled={currentPage === totalPages - 1 || totalPages === 0}
              className="px-2 py-1 h-8"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        <div className="space-y-2">
          {currentRows.length > 0 ? (
            currentRows.map((row, rowIndex) => (
              <div key={rowIndex} className="flex space-x-2 justify-center">
                {row.map(slot => (
                  <div 
                    key={slot.id} 
                    className={`
                      w-10 h-10 rounded-md flex items-center justify-center text-xs font-medium
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
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              {filteredSlots.length === 0 
                ? `No slots available for Level ${selectedLevel}` 
                : 'Loading slots...'}
            </div>
          )}
        </div>
        
        <div className="flex flex-wrap items-center justify-center gap-4 mt-6 pt-4 border-t">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-4 h-4 rounded bg-green-100 border border-green-300"></div>
            <span>Free</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-4 h-4 rounded bg-red-100 border border-red-300"></div>
            <span>Occupied</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(0)}
            className="text-xs px-3 py-1 ml-auto"
          >
            <RotateCcw className="h-3 w-3 mr-1" />
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
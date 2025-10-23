"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiClient } from '@/lib/http'
import { Loader2 } from 'lucide-react'

interface SlotOccupancy {
  slot_id: string
  occupancy: number
}

interface HeatmapData {
  date: string
  zone_id: string | null
  hours: Record<number, SlotOccupancy[]>
}

interface Zone {
  zone_id: string
  name: string
  slot_count: number
}

export function OccupancyHeatmap() {
  const [currentHour, setCurrentHour] = useState(new Date().getHours())
  const [selectedZone, setSelectedZone] = useState<string>('all')
  const [zones, setZones] = useState<Zone[]>([])
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchZones()
  }, [])

  useEffect(() => {
    fetchHeatmapData()
  }, [selectedZone])

  const fetchZones = async () => {
    try {
      const response = await apiClient.get('/v1/heatmaps/zones')
      setZones(response.zones || [])
    } catch (error) {
      console.error('Error fetching zones:', error)
    }
  }

  const fetchHeatmapData = async () => {
    setLoading(true)
    try {
      const today = new Date().toISOString().split('T')[0]
      const zoneParam = selectedZone !== 'all' ? `&zone_id=${selectedZone}` : ''
      const response = await apiClient.get(`/v1/heatmaps/occupancy/hourly?date=${today}${zoneParam}`)
      setHeatmapData(response)
    } catch (error) {
      console.error('Error fetching heatmap data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getColorForOccupancy = (percentage: number): string => {
    if (percentage <= 40) return 'bg-green-300'
    if (percentage <= 70) return 'bg-yellow-300'
    if (percentage <= 90) return 'bg-orange-400'
    return 'bg-red-500'
  }

  const formatHour = (hour: number): string => {
    const period = hour >= 12 ? 'PM' : 'AM'
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
    return `${displayHour}:00 ${period}`
  }

  const currentSlots = heatmapData?.hours?.[currentHour] || []

  // Group slots by row (parse from slot_id like "A1" -> row "A")
  const groupedSlots = currentSlots.reduce((acc, slot) => {
    const match = slot.slot_id.match(/^([A-Z]+)/)
    const row = match ? match[1] : 'Other'
    if (!acc[row]) acc[row] = []
    acc[row].push(slot)
    return acc
  }, {} as Record<string, SlotOccupancy[]>)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Occupancy Heatmap</CardTitle>
        <CardDescription>
          Visual representation of parking occupancy patterns throughout the day
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Controls */}
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Zone Filter</label>
            <Select value={selectedZone} onValueChange={setSelectedZone}>
              <SelectTrigger>
                <SelectValue placeholder="Select zone" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Zones</SelectItem>
                {zones.map((zone) => (
                  <SelectItem key={zone.zone_id} value={zone.zone_id}>
                    {zone.name} ({zone.slot_count} slots)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Time: {formatHour(currentHour)}</label>
              <span className="text-xs text-muted-foreground">Slide to view different hours</span>
            </div>
            <Slider
              value={[currentHour]}
              onValueChange={(value) => setCurrentHour(value[0])}
              max={23}
              min={0}
              step={1}
              className="w-full"
            />
          </div>
        </div>

        {/* Heatmap Display */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : currentSlots.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>No data available for this time period</p>
          </div>
        ) : (
          <div className="space-y-2">
            {Object.entries(groupedSlots)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([row, slots]) => (
                <div key={row} className="flex items-center gap-2">
                  <div className="w-8 text-sm font-medium text-muted-foreground">{row}</div>
                  <div className="flex-1 flex flex-wrap gap-1">
                    {slots
                      .sort((a, b) => {
                        const numA = parseInt(a.slot_id.replace(/[A-Z]/g, ''))
                        const numB = parseInt(b.slot_id.replace(/[A-Z]/g, ''))
                        return numA - numB
                      })
                      .map((slot) => (
                        <div
                          key={slot.slot_id}
                          className={`
                            w-12 h-12 rounded flex items-center justify-center text-xs font-medium
                            ${getColorForOccupancy(slot.occupancy)}
                            hover:ring-2 hover:ring-blue-500 cursor-pointer transition-all
                          `}
                          title={`${slot.slot_id}: ${slot.occupancy.toFixed(1)}% occupied`}
                        >
                          {slot.occupancy.toFixed(0)}%
                        </div>
                      ))}
                  </div>
                </div>
              ))}
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 pt-4 border-t">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-green-300" />
            <span className="text-xs">0-40%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-yellow-300" />
            <span className="text-xs">41-70%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-orange-400" />
            <span className="text-xs">71-90%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-red-500" />
            <span className="text-xs">91-100%</span>
          </div>
        </div>

        {/* Stats Summary */}
        {currentSlots.length > 0 && (
          <div className="grid grid-cols-3 gap-4 pt-4 border-t">
            <div className="text-center">
              <p className="text-2xl font-bold">
                {(currentSlots.reduce((sum, s) => sum + s.occupancy, 0) / currentSlots.length).toFixed(1)}%
              </p>
              <p className="text-xs text-muted-foreground">Average Occupancy</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">
                {Math.max(...currentSlots.map(s => s.occupancy)).toFixed(1)}%
              </p>
              <p className="text-xs text-muted-foreground">Peak Slot</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">
                {Math.min(...currentSlots.map(s => s.occupancy)).toFixed(1)}%
              </p>
              <p className="text-xs text-muted-foreground">Lowest Slot</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

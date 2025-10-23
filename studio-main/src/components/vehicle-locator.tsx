"use client"

import { useState } from 'react'
import { Search, X, Loader2, MapPin, Clock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { searchVehicleByPlate } from '@/lib/api'

interface VehicleLocation {
  licensePlate: string
  slotId: string
  zoneId: string
  vehicleType: string
  firstSeen: Date
  lastSeen: Date
  status: 'active' | 'exited'
}

interface VehicleLocatorProps {
  onVehicleFound?: (location: VehicleLocation) => void
  onHighlightSlot?: (slotId: string) => void
}

export function VehicleLocator({ onVehicleFound, onHighlightSlot }: VehicleLocatorProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [result, setResult] = useState<VehicleLocation | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (searchQuery.length < 4) {
      setError('Please enter at least 4 characters')
      return
    }

    setIsSearching(true)
    setError(null)
    setResult(null)

    try {
      const location = await searchVehicleByPlate(searchQuery)

      if (location) {
        setResult(location)
        onVehicleFound?.(location)

        // Highlight slot on map
        if (location.status === 'active') {
          onHighlightSlot?.(location.slotId)
        }
      } else {
        setError(`Vehicle ${searchQuery.toUpperCase()} not found. Please check the plate number.`)
      }
    } catch (err) {
      console.error('Search error:', err)
      setError('Unable to search. Please try again.')
    } finally {
      setIsSearching(false)
    }
  }

  const handleClear = () => {
    setSearchQuery('')
    setResult(null)
    setError(null)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const formatDuration = (firstSeen: Date) => {
    const now = new Date()
    const diff = now.getTime() - new Date(firstSeen).getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Find your vehicle (enter plate)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
          onKeyPress={handleKeyPress}
          className="pl-10 pr-20 text-lg"
          disabled={isSearching}
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {searchQuery && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
          <Button
            onClick={handleSearch}
            disabled={isSearching || searchQuery.length < 4}
            size="sm"
          >
            {isSearching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              'Search'
            )}
          </Button>
        </div>
      </div>

      {/* Results */}
      <AnimatePresence mode="wait">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="p-4 bg-destructive/10 border-destructive/20">
              <p className="text-sm text-destructive">{error}</p>
            </Card>
          </motion.div>
        )}

        {result && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="p-6">
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-xl font-bold">{result.licensePlate}</h3>
                    <p className="text-sm text-muted-foreground capitalize">
                      {result.vehicleType}
                    </p>
                  </div>
                  {result.status === 'active' ? (
                    <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      Currently Parked
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                      Exited
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-blue-500" />
                    <div>
                      <p className="text-xs text-muted-foreground">Location</p>
                      <p className="font-semibold">{result.slotId}</p>
                      {result.zoneId && (
                        <p className="text-xs text-muted-foreground">{result.zoneId}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-orange-500" />
                    <div>
                      <p className="text-xs text-muted-foreground">Duration</p>
                      <p className="font-semibold">
                        {formatDuration(result.firstSeen)}
                      </p>
                    </div>
                  </div>
                </div>

                {result.status === 'active' && onHighlightSlot && (
                  <Button
                    onClick={() => onHighlightSlot(result.slotId)}
                    variant="outline"
                    className="w-full"
                  >
                    <MapPin className="h-4 w-4 mr-2" />
                    View on Map
                  </Button>
                )}

                {result.status === 'exited' && (
                  <p className="text-sm text-muted-foreground pt-2">
                    Vehicle exited on {new Date(result.lastSeen).toLocaleString()}
                  </p>
                )}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

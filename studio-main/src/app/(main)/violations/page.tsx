"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AlertTriangle, CheckCircle, Clock, MapPin, Car } from 'lucide-react'
import { apiClient } from '@/lib/http'
import { motion } from 'framer-motion'

interface Violation {
  id: string
  violation_type: string
  slot_id: string
  zone_id: string
  license_plate?: string
  vehicle_type?: string
  severity: 'low' | 'medium' | 'high'
  status: 'active' | 'resolved' | 'dismissed'
  detected_at: string
  resolved_at?: string
}

export default function ViolationsPage() {
  const [violations, setViolations] = useState<Violation[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('active')

  useEffect(() => {
    fetchViolations(activeTab)
  }, [activeTab])

  const fetchViolations = async (status: string) => {
    setLoading(true)
    try {
      const response = await apiClient.get(`/v1/violations?status=${status}&limit=100&sort_by=detected_at&sort_order=desc`)
      setViolations(response.violations || [])
    } catch (error) {
      console.error('Error fetching violations:', error)
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200'
      case 'medium':
        return 'bg-orange-100 text-orange-700 border-orange-200'
      case 'low':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getViolationTypeLabel = (type: string) => {
    switch (type) {
      case 'overstay':
        return 'Overstay'
      case 'wrong_vehicle_type':
        return 'Wrong Vehicle Type'
      case 'unauthorized':
        return 'Unauthorized Parking'
      default:
        return type
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))

    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60))
      return `${minutes}m ago`
    } else if (hours < 24) {
      return `${hours}h ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Parking Violations</h1>
          <p className="text-muted-foreground">Monitor and manage parking violations</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="active">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Active
          </TabsTrigger>
          <TabsTrigger value="resolved">
            <CheckCircle className="h-4 w-4 mr-2" />
            Resolved
          </TabsTrigger>
          <TabsTrigger value="dismissed">
            Dismissed
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4 mt-6">
          {loading ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">Loading violations...</p>
              </CardContent>
            </Card>
          ) : violations.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No {activeTab} violations</h3>
                <p className="text-muted-foreground">
                  {activeTab === 'active' ? 'All parking slots are in compliance' : `No ${activeTab} violations found`}
                </p>
              </CardContent>
            </Card>
          ) : (
            violations.map((violation, index) => (
              <motion.div
                key={violation.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className={getSeverityColor(violation.severity)}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="space-y-3 flex-1">
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className="font-semibold">
                            {getViolationTypeLabel(violation.violation_type)}
                          </Badge>
                          <Badge variant="secondary" className={getSeverityColor(violation.severity)}>
                            {violation.severity.toUpperCase()}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="text-xs text-muted-foreground">Location</p>
                              <p className="font-semibold">{violation.slot_id}</p>
                              {violation.zone_id && (
                                <p className="text-xs">{violation.zone_id}</p>
                              )}
                            </div>
                          </div>

                          {violation.license_plate && (
                            <div className="flex items-center gap-2">
                              <Car className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <p className="text-xs text-muted-foreground">License Plate</p>
                                <p className="font-semibold">{violation.license_plate}</p>
                              </div>
                            </div>
                          )}

                          {violation.vehicle_type && (
                            <div className="flex items-center gap-2">
                              <Car className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <p className="text-xs text-muted-foreground">Vehicle</p>
                                <p className="font-semibold capitalize">{violation.vehicle_type}</p>
                              </div>
                            </div>
                          )}

                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="text-xs text-muted-foreground">Detected</p>
                              <p className="font-semibold">{formatTimestamp(violation.detected_at)}</p>
                            </div>
                          </div>
                        </div>

                        {violation.resolved_at && (
                          <p className="text-sm text-muted-foreground">
                            Resolved on {new Date(violation.resolved_at).toLocaleString()}
                          </p>
                        )}
                      </div>

                      {violation.status === 'active' && (
                        <div className="flex gap-2 ml-4">
                          <Button size="sm" variant="outline">
                            View Details
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

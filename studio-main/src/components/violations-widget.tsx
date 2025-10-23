"use client"

import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/http'
import Link from 'next/link'

interface ViolationsSummary {
  total: number
  high: number
  medium: number
  low: number
}

export function ViolationsWidget() {
  const [summary, setSummary] = useState<ViolationsSummary>({ total: 0, high: 0, medium: 0, low: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchViolationsSummary()

    // Refresh every 30 seconds
    const interval = setInterval(fetchViolationsSummary, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchViolationsSummary = async () => {
    try {
      const response = await apiClient.get('/v1/violations?status=active&limit=100')

      const violations = response.violations || []
      const high = violations.filter((v: any) => v.severity === 'high').length
      const medium = violations.filter((v: any) => v.severity === 'medium').length
      const low = violations.filter((v: any) => v.severity === 'low').length

      setSummary({
        total: violations.length,
        high,
        medium,
        low
      })
    } catch (error) {
      console.error('Error fetching violations:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Active Violations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </CardContent>
      </Card>
    )
  }

  if (summary.total === 0) {
    return (
      <Card className="bg-green-50 dark:bg-green-950">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-300">
            <CheckCircle2 className="h-5 w-5" />
            No Active Violations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-green-600 dark:text-green-400">
            All parking slots are in compliance
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-orange-200 dark:border-orange-800">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          Active Violations
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold">{summary.total}</span>
          <span className="text-sm text-muted-foreground">Total Active</span>
        </div>

        <div className="space-y-2">
          {summary.high > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse" />
                <span className="text-sm">High Severity</span>
              </div>
              <Badge variant="destructive">{summary.high}</Badge>
            </div>
          )}

          {summary.medium > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-orange-500 rounded-full" />
                <span className="text-sm">Medium Severity</span>
              </div>
              <Badge variant="secondary" className="bg-orange-100 text-orange-700">
                {summary.medium}
              </Badge>
            </div>
          )}

          {summary.low > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-yellow-500 rounded-full" />
                <span className="text-sm">Low Severity</span>
              </div>
              <Badge variant="secondary" className="bg-yellow-100 text-yellow-700">
                {summary.low}
              </Badge>
            </div>
          )}
        </div>

        <Link href="/violations">
          <Button variant="outline" className="w-full">
            View All Violations
          </Button>
        </Link>
      </CardContent>
    </Card>
  )
}

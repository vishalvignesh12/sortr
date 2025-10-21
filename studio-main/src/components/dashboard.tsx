'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SlotCard } from '@/components/slot-card';
import { SlotGrid } from '@/components/slot-grid';
import { ParkingSlot } from '@/lib/types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Car, DollarSign, TrendingUp, Clock } from 'lucide-react';
import { motion } from 'framer-motion';

interface DashboardProps {
  slots: ParkingSlot[];
}

// Mock data for charts
const occupancyData = [
  { level: 'Level A', occupancy: 75 },
  { level: 'Level B', occupancy: 85 },
  { level: 'Level C', occupancy: 45 },
];

const revenueData = [
  { day: 'Mon', revenue: 1200 },
  { day: 'Tue', revenue: 1900 },
  { day: 'Wed', revenue: 1500 },
  { day: 'Thu', revenue: 2100 },
  { day: 'Fri', revenue: 2800 },
  { day: 'Sat', revenue: 3200 },
  { day: 'Sun', revenue: 2400 },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28'];

export function Dashboard({ slots }: DashboardProps) {
  // Calculate statistics
  const totalSlots = slots.length;
  const occupiedSlots = slots.filter(slot => slot.status === 'Occupied').length;
  const freeSlots = totalSlots - occupiedSlots;
  const occupancyRate = totalSlots > 0 ? Math.round((occupiedSlots / totalSlots) * 100) : 0;

  // Get a few sample slots for display
  const sampleSlots = slots.slice(0, 6);

  // Data for pie chart
  const pieData = [
    { name: 'Occupied', value: occupiedSlots },
    { name: 'Free', value: freeSlots },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Stats Overview */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {[
          { title: 'Total Slots', value: totalSlots, desc: 'All levels', icon: Car },
          { title: 'Occupied', value: occupiedSlots, desc: 'Currently in use', icon: Car },
          { title: 'Free', value: freeSlots, desc: 'Available now', icon: Car },
          { title: 'Occupancy', value: `${occupancyRate}%`, desc: 'Current rate', icon: TrendingUp }
        ].map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.desc}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Charts */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader>
              <CardTitle>Occupancy by Level</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={occupancyData}>
                  <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
                  <XAxis dataKey="level" />
                  <YAxis />
                  <Tooltip />
                  <Bar 
                    dataKey="occupancy" 
                    fill="#3b82f6" 
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Occupancy Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Recent Activity - Sample Slots */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
      >
        <h3 className="text-lg font-semibold mb-4">Recently Updated Slots</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sampleSlots.map((slot, index) => (
            <motion.div
              key={slot.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.6 + index * 0.1 }}
            >
              <SlotCard key={slot.id} slot={slot} now={new Date()} />
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
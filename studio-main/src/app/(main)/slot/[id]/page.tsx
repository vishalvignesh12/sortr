import { notFound } from 'next/navigation';
import { getSlot } from '@/lib/data';
import { SlotCard } from '@/components/slot-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Car, Clock, Calendar, MapPin } from 'lucide-react';
import { format } from 'date-fns';

interface SlotPageProps {
  params: {
    id: string;
  };
}

export default async function SlotPage({ params }: SlotPageProps) {
  const slot = await getSlot(params.id);

  if (!slot) {
    notFound();
  }

  const isOccupied = slot.status === 'Occupied';
  const occupiedSince = slot.occupiedSince ? new Date(slot.occupiedSince) : null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Slot {slot.id}
        </h1>
        <p className="mt-2 text-muted-foreground">
          Detailed information about this parking slot.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Car className="h-5 w-5" />
                  Slot Details
                </span>
                <Badge 
                  variant={isOccupied ? "destructive" : "default"} 
                  className={isOccupied ? "bg-red-500 hover:bg-red-500" : "bg-green-500 hover:bg-green-500"}
                >
                  {slot.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground">Slot ID</h3>
                  <p className="text-lg font-semibold">{slot.id}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground">Status</h3>
                  <p className={`text-lg font-semibold ${isOccupied ? 'text-red-500' : 'text-green-500'}`}>
                    {slot.status}
                  </p>
                </div>
                
                {isOccupied && occupiedSince && (
                  <>
                    <div>
                      <h3 className="text-sm font-medium text-muted-foreground">Occupied Since</h3>
                      <p className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {format(occupiedSince, 'MMM d, yyyy h:mm a')}
                      </p>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-muted-foreground">Duration</h3>
                      <p className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {Math.floor((Date.now() - occupiedSince.getTime()) / (1000 * 60 * 60))} hours
                      </p>
                    </div>
                  </>
                )}
              </div>
              
              <div className="mt-6 flex gap-4">
                <Button disabled={!isOccupied}>
                  Mark as Free
                </Button>
                <Button variant="outline" disabled={isOccupied}>
                  Reserve Slot
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Location</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPin className="h-4 w-4" />
                <span>Parking Level {slot.id.charAt(0)}, Section A</span>
              </div>
              <div className="mt-4 h-64 bg-muted rounded-lg flex items-center justify-center">
                <p className="text-muted-foreground">Interactive parking map would be displayed here</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <div className="sticky top-24">
            <SlotCard 
              slot={slot} 
              now={new Date()} 
            />
            
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="h-2 w-2 rounded-full bg-primary mt-2"></div>
                    <div>
                      <p className="text-sm font-medium">Slot created</p>
                      <p className="text-xs text-muted-foreground">Jan 1, 2024</p>
                    </div>
                  </div>
                  {isOccupied && (
                    <div className="flex items-start gap-3">
                      <div className="h-2 w-2 rounded-full bg-destructive mt-2"></div>
                      <div>
                        <p className="text-sm font-medium">Slot occupied</p>
                        <p className="text-xs text-muted-foreground">
                          {occupiedSince ? format(occupiedSince, 'MMM d, h:mm a') : 'N/A'}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
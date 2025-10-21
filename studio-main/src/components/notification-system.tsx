'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Bell, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Info,
  XCircle
} from 'lucide-react';

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  timestamp: Date;
  read: boolean;
}

interface NotificationSystemProps {
  initialNotifications?: Notification[];
}

export function NotificationSystem({ initialNotifications = [] }: NotificationSystemProps) {
  const [notifications, setNotifications] = useState<Notification[]>(initialNotifications);
  const [showAll, setShowAll] = useState(false);

  // Auto-add some demo notifications
  useEffect(() => {
    if (notifications.length === 0) {
      // Simulate receiving notifications
      const demoNotifications: Notification[] = [
        {
          id: '1',
          title: 'Parking Availability',
          message: 'Level A has 5 spots available in section A2',
          type: 'info',
          timestamp: new Date(Date.now() - 5 * 60000), // 5 minutes ago
          read: false
        },
        {
          id: '2',
          title: 'Reservation Confirmed',
          message: 'Your parking spot A-015 has been reserved for today',
          type: 'success',
          timestamp: new Date(Date.now() - 15 * 60000), // 15 minutes ago
          read: false
        },
        {
          id: '3',
          title: 'Low Availability',
          message: 'Level C is reaching capacity, consider other levels',
          type: 'warning',
          timestamp: new Date(Date.now() - 30 * 60000), // 30 minutes ago
          read: true
        }
      ];
      setNotifications(demoNotifications);
    }
  }, [notifications.length]);

  const unreadCount = notifications.filter(n => !n.read).length;
  
  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      id: Math.random().toString(36).substring(7),
      ...notification,
      timestamp: new Date(),
      read: false
    };
    setNotifications(prev => [newNotification, ...prev]);
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, read: true } : notif
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, read: true }))
    );
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const visibleNotifications = showAll 
    ? notifications 
    : notifications.slice(0, 5);

  const getIcon = (type: NotificationType) => {
    switch (type) {
      case 'success': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning': return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'error': return <XCircle className="h-5 w-5 text-destructive" />;
      default: return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getTypeColor = (type: NotificationType) => {
    switch (type) {
      case 'success': return 'border-green-200 bg-green-50';
      case 'warning': return 'border-yellow-200 bg-yellow-50';
      case 'error': return 'border-destructive/30 bg-destructive/10';
      default: return 'border-blue-200 bg-blue-50';
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notifications
          </CardTitle>
          <CardDescription>
            Updates about parking availability and system status
          </CardDescription>
        </div>
        {notifications.length > 0 && (
          <div className="flex gap-2">
            {unreadCount > 0 && (
              <Button variant="outline" size="sm" onClick={markAllAsRead}>
                Mark all as read
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={clearAll}>
              Clear all
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {notifications.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Bell className="h-12 w-12 mx-auto text-muted" />
            <p className="mt-2">No notifications yet</p>
            <p className="text-sm">You'll see updates about parking availability here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {visibleNotifications.map((notification) => (
              <div 
                key={notification.id} 
                className={`p-3 rounded-lg border ${getTypeColor(notification.type)} ${!notification.read ? 'ring-1 ring-primary/20' : ''}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3 flex-1">
                    {getIcon(notification.type)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{notification.title}</h4>
                        {!notification.read && (
                          <Badge variant="secondary" className="text-xs">New</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {notification.message}
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        {notification.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {!notification.read && (
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => markAsRead(notification.id)}
                        className="h-6 w-6 p-0"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </Button>
                    )}
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => removeNotification(notification.id)}
                      className="h-6 w-6 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            
            {notifications.length > 5 && (
              <Button 
                variant="outline" 
                className="w-full mt-2"
                onClick={() => setShowAll(!showAll)}
              >
                {showAll ? 'Show Less' : `Show All ${notifications.length} Notifications`}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
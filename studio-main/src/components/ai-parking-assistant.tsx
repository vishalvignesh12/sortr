'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Bot, MessageCircle, Sparkles, Clock } from 'lucide-react';

export function AIParkingAssistant() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          AI Parking Assistant
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="bg-muted p-4 rounded-lg">
            <p className="text-sm">Hello! I'm your parking assistant. How can I help you today?</p>
          </div>
          
          <div className="space-y-2">
            <Button variant="secondary" className="w-full justify-start">
              <MessageCircle className="h-4 w-4 mr-2" />
              Find available parking near entrance
            </Button>
            <Button variant="secondary" className="w-full justify-start">
              <Sparkles className="h-4 w-4 mr-2" />
              Predict when spot will open
            </Button>
            <Button variant="secondary" className="w-full justify-start">
              <Clock className="h-4 w-4 mr-2" />
              Estimate parking costs
            </Button>
          </div>
          
          <div className="flex gap-2">
            <Input placeholder="Ask a question..." className="flex-1" />
            <Button variant="outline">
              <MessageCircle className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
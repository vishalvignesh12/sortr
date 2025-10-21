// This is a placeholder page for initializing parking data
// You can access this page at /api/init (but we'll create an API route instead)

import { initializeParkingSlots } from '@/lib/api';

export const dynamic = 'force-dynamic';

export default async function InitPage() {
  try {
    await initializeParkingSlots();
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
          <h1 className="text-2xl font-bold text-green-600 mb-4">Success!</h1>
          <p className="text-gray-700 mb-6">Parking slots have been initialized successfully in the database.</p>
          <a 
            href="/" 
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error initializing parking slots:', error);
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error!</h1>
          <p className="text-gray-700 mb-6">Failed to initialize parking slots. Check the console for details.</p>
          <p className="text-sm text-gray-500 mb-6">Error: {(error as Error).message}</p>
          <a 
            href="/" 
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    );
  }
}
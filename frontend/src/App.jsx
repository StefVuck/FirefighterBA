import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import TimePrediction from './components/ui/timeprediction';
import axios from 'axios';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Clock, TrendingDown, TrendingUp, AlertCircle } from 'lucide-react';

// Update once not hosting on same machine as backend
const API_URL = 'http://localhost:5000/api';

const BABoardDashboard = () => {
  const [firefighters, setFirefighters] = useState([]); 
  const [activeEntries, setActiveEntries] = useState([]);
  const [inactiveEntries, setInactiveEntries] = useState([]);
  const [newEntry, setNewEntry] = useState({
    firefighter_id: '',
    pressure: '',
    location: '',
    remarks: ''
  });
  const [pressureUpdates, setPressureUpdates] = useState({});
  const [showConfirmation, setShowConfirmation] = useState(null);
  const [locationUpdates, setLocationUpdates] = useState({});

  // Fetch both firefighters and BA entries
  const fetchData = async () => {
    try {
      const [firefightersRes, entriesRes] = await Promise.all([
        axios.get(`${API_URL}/firefighters`),
        axios.get(`${API_URL}/ba-entries`)
      ]);
      
      if (firefightersRes.data && Array.isArray(firefightersRes.data)) {
        setFirefighters(firefightersRes.data);
      }
      
      if (entriesRes.data && Array.isArray(entriesRes.data)) {
        setActiveEntries(entriesRes.data.filter(entry => entry.active));
        setInactiveEntries(entriesRes.data.filter(entry => !entry.active));
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  // This useEffect hook implements a real-time data fetching strategy that is crucial for a BA monitoring system
  // We use Promise.all for concurrent API calls to minimize load time and ensure data consistency
  // A cleanup pattern with mounted flag prevents memory leaks and race conditions
  // Auto-refresh every 30 seconds keeps the dashboard current while being mindful of server load
  useEffect(() => {
    // Flag to track if component is mounted, prevents state updates after unmount
    let mounted = true;
    
    // Encapsulated fetch function with safety checks
    const fetchDataSafely = async () => {
      try {
        // Concurrent API calls for optimal performance
        const [firefightersRes, entriesRes] = await Promise.all([
          axios.get(`${API_URL}/firefighters`),
          axios.get(`${API_URL}/ba-entries`)
        ]);
        
        // Prevent state updates if component unmounted during API call
        if (!mounted) return;
        
        // Safely update firefighters state if valid data received
        if (firefightersRes.data && Array.isArray(firefightersRes.data)) {
          setFirefighters(firefightersRes.data);
        }
        
        // Update BA entries, separating active from inactive
        if (entriesRes.data && Array.isArray(entriesRes.data)) {
          setActiveEntries(entriesRes.data.filter(entry => entry.active));
          setInactiveEntries(entriesRes.data.filter(entry => !entry.active));
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    // Initial data fetch
    fetchDataSafely();
    // Set up polling interval for real-time updates
    const interval = setInterval(fetchDataSafely, 30000);
    
    // Cleanup function to prevent memory leaks and invalid state updates
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Handles the creation of a new Breathing Apparatus (BA) entry
  // Validates pressure requirements and submits entry to backend
  const handleAddBAEntry = async () => {
    // Validate required fields are present
    if (!newEntry.firefighter_id || !newEntry.pressure) return;

    // Ensure pressure meets minimum safety requirement of 120 BAR
    if (Number(newEntry.pressure) < 120) {
      alert('Pressure cannot be below 120 BAR');
      return;
    }

    try {
      // Submit new BA entry to backend API
      await axios.post(`${API_URL}/ba-entries`, {
        firefighter_id: Number(newEntry.firefighter_id),
        initial_pressure: Number(newEntry.pressure),
        location: newEntry.location,
        remarks: newEntry.remarks
      });

      // Refresh data and reset form
      fetchData();
      setNewEntry({ firefighter_id: '', pressure: '', location: '', remarks: '' });
    } catch (error) {
      console.error('Error adding BA entry:', error);
    }
  };

  // Handles updating the pressure reading for an existing BA entry
  // Includes safety checks and confirmation for low pressure situations
  const handlePressureUpdateClick = async (id) => {
    const newPressure = Number(pressureUpdates[id]);
    // Validate pressure value exists
    if (!newPressure) return;

    // Ensure pressure meets minimum safety requirement
    if (newPressure < 120) {
      alert('Pressure cannot be below 120 BAR');
      return;
    }

    // Show confirmation dialog if pressure is at/below critical level (150 BAR)
    // This will trigger entry completion when confirmed
    if (newPressure <= 150) {
      setShowConfirmation({
        id,
        pressure: newPressure,
        message: `Warning: Pressure is at or below 150 BAR. This will mark the BA entry as inactive. Continue?`
      });
      return;
    }

    try {
      // Update pressure in backend
      await axios.put(`${API_URL}/ba-entries/${id}`, {
        current_pressure: newPressure
      });
      
      // Clear pressure update input field
      setPressureUpdates(prev => ({
        ...prev,
        [id]: ''
      }));
      
      // Refresh data to show updated values
      fetchData();
    } catch (error) {
      console.error('Error updating pressure:', error);
    }
  };

  // Renders a card component for a single BA (Breathing Apparatus) entry
  // Parameters: entry: BA Object, isActive: Active or Complete BA entry bool
  const renderBAEntryCard = (entry, isActive = true) => {
    // Find the corresponding firefighter details from the firefighters array
    const firefighter = firefighters.find(ff => ff.id === entry.firefighter_id);
    
    return (
      // Apply red border if estimated time is less than 20 minutes
      <Card key={entry.id} className={`${entry.estimated_time < 20 ? 'border-red-500' : ''}`}>
        <CardContent className="p-4">
          {/* Grid layout with 6 columns for entry information */}
          <div className="grid grid-cols-6 gap-4 items-center">
            {/* Column 1: Firefighter identification */}
            <div>
              <div className="font-semibold">
                {firefighter ? `${firefighter.first_name} ${firefighter.last_name}` : 'Unknown'}
              </div>
              <div className="text-sm text-gray-500">
                {new Date(entry.entry_time).toLocaleTimeString()}
              </div>
            </div>

            {/* Column 2: Pressure readings and update form */}
            <div>
              <div className="font-medium">{entry.current_pressure} BAR</div>
              {/* Only show pressure update controls for active entries */}
              {isActive && (
                <div className="flex gap-2 mt-1">
                  <Input
                    type="number"
                    placeholder="New pressure"
                    value={pressureUpdates[entry.id] || ''}
                    onChange={(e) => setPressureUpdates(prev => ({
                      ...prev,
                      [entry.id]: e.target.value
                    }))}
                    min={120}
                    max={300}
                  />
                  <Button
                    size="sm"
                    onClick={() => handlePressureUpdateClick(entry.id)}
                    disabled={!pressureUpdates[entry.id]}
                  >
                    Update
                  </Button>
                </div>
              )}
            </div>

            {/* Column 3: Time prediction */}
            <div>
              <TimePrediction 
                firefighter={firefighter} 
                entry={entry}
              />
            </div>

            {/* Column 4: Location */}
            <div>{entry.location}</div>

            {/* Column 5: Remarks */}
            <div>{entry.remarks}</div>

            {/* Column 6: Warning message for low air remaining */}
            {isActive && entry.estimated_time < 20 && (
              <Alert variant="destructive" className="col-span-6 mt-2">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Warning: Low air remaining. Time to exit: {entry.estimated_time} minutes
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="p-4 max-w-6xl mx-auto">
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md">
            <h3 className="text-lg font-semibold mb-4">Confirm Update</h3>
            <p className="mb-4">{showConfirmation.message}</p>
            <div className="flex justify-end gap-4">
              <Button variant="outline" onClick={() => setShowConfirmation(null)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={confirmPressureUpdate}>
                Confirm
              </Button>
            </div>
          </div>
        </div>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>BA Board Management System</CardTitle>
        </CardHeader>
        <CardContent>

          {/* Core section for adding new entries*/}
          <div className="grid grid-cols-5 gap-4 mb-4">
            <Select
              value={newEntry.firefighter_id}
              onValueChange={(value) => setNewEntry({ ...newEntry, firefighter_id: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select Firefighter" />
              </SelectTrigger>
              <SelectContent>
                {firefighters.filter(ff => ff.active).map((ff) => (
                  <SelectItem key={ff.id} value={ff.id.toString()}>
                    {ff.first_name} {ff.last_name} ({ff.badge_number})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="number"
              placeholder="Pressure (BAR)"
              value={newEntry.pressure}
              onChange={(e) => setNewEntry({ ...newEntry, pressure: e.target.value })}
              min={120}
              max={300}
            />
            <Input
              placeholder="Location"
              value={newEntry.location}
              onChange={(e) => setNewEntry({ ...newEntry, location: e.target.value })}
            />
            <Input
              placeholder="Remarks"
              value={newEntry.remarks}
              onChange={(e) => setNewEntry({ ...newEntry, remarks: e.target.value })}
            />
            <Button onClick={handleAddBAEntry}>Add BA Entry</Button>
          </div>
        </CardContent>
      </Card>
        
      {/* Active BA Section*/}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-4">Active BA Entries</h2>
          <div className="grid gap-4">
            {activeEntries.map(entry => renderBAEntryCard(entry, true))}
          </div>
        </div>


      {/* Inactive BA Section (if there is any)*/}
        {inactiveEntries.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Inactive BA Entries</h2>
            <div className="grid gap-4">
              {inactiveEntries.map(entry => renderBAEntryCard(entry, false))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BABoardDashboard;
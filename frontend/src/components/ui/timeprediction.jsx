import React, { useEffect, useState } from 'react';
import { Clock, TrendingDown, TrendingUp } from 'lucide-react';
import axios from 'axios';

const TimePrediction = ({ firefighter, entry }) => {
  const [predictions, setPredictions] = useState({ default: null, custom: null });
  const [trend, setTrend] = useState(null);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const response = await axios.get(`http://localhost:5000/api/firefighters/${firefighter.id}/predictions/${entry.current_pressure}`);
        setPredictions(response.data);
        
        // Calculate trend
        const timeSinceUpdate = (new Date() - new Date(entry.updated_time)) / 1000 / 60; // minutes
        if (timeSinceUpdate > 0) {
          const pressureDrop = entry.initial_pressure - entry.current_pressure;
          const rate = pressureDrop / timeSinceUpdate; // bars per minute
          setTrend({
            rate,
            // High consumption if 20% higher than model prediction
            isHigh: rate > (entry.initial_pressure - 150) / predictions.default * 1.2
          });
        }
      } catch (error) {
        console.error('Error fetching predictions:', error);
      }
    };

    if (firefighter && entry.current_pressure) {
      fetchPredictions();
    }
  }, [firefighter, entry]);

  return (
    <div className="flex items-center gap-2">
      <Clock className="inline" size={16} />
      <span className="font-medium">{predictions.custom || predictions.default}</span>
      {predictions.custom !== predictions.default && (
        <span className="text-red-500">({predictions.default})</span>
      )} min
      {trend && (
        <span 
          className={trend.isHigh ? "text-red-500" : "text-green-500"} 
          title={`Consumption rate: ${trend.rate.toFixed(2)} bar/min`}
        >
          {trend.isHigh ? 
            <TrendingUp className="inline" size={16} /> : 
            <TrendingDown className="inline" size={16} />}
        </span>
      )}
    </div>
  );
};

export default TimePrediction;
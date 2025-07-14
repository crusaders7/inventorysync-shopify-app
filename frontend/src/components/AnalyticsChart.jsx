import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { Card, Text } from '@shopify/polaris';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function AnalyticsChart({ type = 'line', title, data, height = 300 }) {
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      x: {
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
    },
  };

  const ChartComponent = type === 'bar' ? Bar : Line;

  return (
    <Card>
      <div style={{ padding: '20px' }}>
        <Text variant="headingMd" as="h3">{title}</Text>
        <div style={{ marginTop: '16px', height: `${height}px` }}>
          <ChartComponent data={data} options={options} />
        </div>
      </div>
    </Card>
  );
}

export default AnalyticsChart;
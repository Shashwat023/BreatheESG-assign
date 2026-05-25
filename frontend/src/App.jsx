import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Uploads from './pages/Uploads';
import Records from './pages/Records';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="uploads" element={<Uploads />} />
          <Route path="records" element={<Records />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

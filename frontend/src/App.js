import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Navbar from './components/navbar';
import "bootstrap/dist/css/bootstrap.min.css";
import AddProduct from './pages/AddProduct';
import EditProduct from './pages/EditProduct';
import PrivateRoute from './components/PrivateRoute'; 

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        {/* Wrap restricted routes with PrivateRoute */}
        <Route path="/dashboard" element={<PrivateRoute><Navbar /><Dashboard /></PrivateRoute>} />
        <Route path="/add-product" element={<PrivateRoute><Navbar /><AddProduct /></PrivateRoute>}/>
        <Route path="/edit-product/:productId" element={<PrivateRoute><Navbar /><EditProduct /></PrivateRoute>}/>
      </Routes>
    </Router>
  );
}

export default App;

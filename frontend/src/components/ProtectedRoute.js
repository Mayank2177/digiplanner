import React from 'react';
import { Navigate } from 'react-router-dom';
import { isLoggedIn } from '../api/client';

// Guards routes that require a real JWT (issued by /api/v1/auth/login or
// /api/v1/auth/signup). DashboardPage also checks this on mount, but this
// wrapper stops the page from ever rendering (and firing API calls that
// would 401) for a signed-out visitor who lands on /dashboard directly.
const ProtectedRoute = ({ children }) => {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

export default ProtectedRoute;

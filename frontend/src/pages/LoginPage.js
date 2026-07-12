import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Receipt, Eye, EyeOff, Mail, Lock, 
  ArrowRight, Shield
} from 'lucide-react';
import '../styles/LoginPage.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }
    
    return newErrors;
  };

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      
      // Simulate Google OAuth process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate successful Google authentication
      console.log('Google authentication successful');
      
      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error) {
      alert('❌ Google sign in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    try {
      setLoading(true);
      
      // Simulate Microsoft OAuth process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate successful Microsoft authentication
      console.log('Microsoft authentication successful');
      
      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error) {
      alert('❌ Microsoft sign in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const newErrors = validateForm();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setLoading(true);
    
    // Simulate API call
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simulate successful login
      console.log('Login successful:', formData.email);
      
      // Store user session (in real app, this would be JWT token, etc.)
      localStorage.setItem('userEmail', formData.email);
      localStorage.setItem('isLoggedIn', 'true');
      
      // Show success message briefly
      const successMessage = document.createElement('div');
      successMessage.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        background: linear-gradient(135deg, #10B981, #14B8A6);
        color: white; padding: 16px 24px; border-radius: 12px;
        font-weight: 600; box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
      `;
      successMessage.textContent = `✅ Welcome back, ${formData.email.split('@')[0]}!`;
      document.body.appendChild(successMessage);
      
      // Remove message and redirect after short delay
      setTimeout(() => {
        document.body.removeChild(successMessage);
        navigate('/dashboard');
      }, 1000);
      
    } catch (error) {
      alert('❌ Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <Link to="/" className="logo-link">
            <div className="logo-mark">
              <Receipt size={24} color="#fff" strokeWidth={1.8} />
            </div>
            <span className="logo-text">
              DigiPlanner<span className="gradient-text">Pro</span>
            </span>
          </Link>
          
          <div className="login-title">
            <h1>Welcome Back</h1>
            <p>Sign in to your DigiPlanner account</p>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">
              <Mail size={16} />
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={errors.email ? 'error' : ''}
              placeholder="john@company.com"
            />
            {errors.email && <span className="error-text">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">
              <Lock size={16} />
              Password
            </label>
            <div className="password-input">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={errors.password ? 'error' : ''}
                placeholder="••••••••"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.password && <span className="error-text">{errors.password}</span>}
          </div>

          <div className="form-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="rememberMe"
                checked={formData.rememberMe}
                onChange={handleChange}
              />
              <span className="checkmark"></span>
              Remember me
            </label>
            <Link to="/forgot-password" className="forgot-link">
              Forgot password?
            </Link>
          </div>

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? (
              <>
                <div className="loading-spinner"></div>
                Signing In...
              </>
            ) : (
              <>
                Sign In
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        <div className="login-divider">
          <span>or</span>
        </div>

        <div className="social-login">
          <button className="social-btn google" onClick={handleGoogleLogin}>
            <div className="google-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
            </div>
            Continue with Google
          </button>
          <button className="social-btn microsoft" onClick={handleMicrosoftLogin}>
            <div className="microsoft-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M11.4 11.4H2V2h9.4v9.4z" fill="#f25022"/>
                <path d="M22 11.4h-9.4V2H22v9.4z" fill="#00a4ef"/>
                <path d="M11.4 22H2v-9.4h9.4V22z" fill="#ffb900"/>
                <path d="M22 22h-9.4v-9.4H22V22z" fill="#7fba00"/>
              </svg>
            </div>
            Continue with Microsoft
          </button>
        </div>

        <div className="login-footer">
          <p>
            Don't have an account? 
            <Link to="/signup"> Create one here</Link>
          </p>
        </div>

        <div className="security-notice">
          <Shield size={14} />
          <span>Your data is protected with enterprise-grade security</span>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
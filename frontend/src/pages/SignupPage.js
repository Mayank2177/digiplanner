import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Receipt, Eye, EyeOff, Mail, Lock, User, 
  Building2, Phone, CheckCircle2, ArrowRight,
  Shield, Zap, BarChart3
} from 'lucide-react';
import '../styles/SignupPage.css';

const SignupPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    company: '',
    phone: '',
    agreeToTerms: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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
    
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }
    
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    if (!formData.company.trim()) {
      newErrors.company = 'Company name is required';
    }
    
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = 'You must agree to the terms and conditions';
    }
    
    return newErrors;
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
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate successful account creation
      console.log('Account created:', formData);
      
      // Store user session
      localStorage.setItem('userEmail', formData.email);
      localStorage.setItem('userName', `${formData.firstName} ${formData.lastName}`);
      localStorage.setItem('isLoggedIn', 'true');
      
      // Show success message
      const successMessage = document.createElement('div');
      successMessage.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        background: linear-gradient(135deg, #10B981, #14B8A6);
        color: white; padding: 16px 24px; border-radius: 12px;
        font-weight: 600; box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
      `;
      successMessage.textContent = `🎉 Welcome to DigiPlanner, ${formData.firstName}!`;
      document.body.appendChild(successMessage);
      
      // Remove message and redirect after short delay
      setTimeout(() => {
        document.body.removeChild(successMessage);
        navigate('/dashboard');
      }, 1500);
      
    } catch (error) {
      alert('❌ Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    try {
      setLoading(true);
      
      // Simulate Google OAuth process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate successful Google account creation
      const mockGoogleUser = {
        email: 'user@gmail.com',
        firstName: 'Google',
        lastName: 'User'
      };
      
      // Store user session
      localStorage.setItem('userEmail', mockGoogleUser.email);
      localStorage.setItem('userName', `${mockGoogleUser.firstName} ${mockGoogleUser.lastName}`);
      localStorage.setItem('isLoggedIn', 'true');
      
      console.log('Google signup successful');
      
      // Show success message
      const successMessage = document.createElement('div');
      successMessage.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        background: linear-gradient(135deg, #10B981, #14B8A6);
        color: white; padding: 16px 24px; border-radius: 12px;
        font-weight: 600; box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
      `;
      successMessage.textContent = `🎉 Welcome to DigiPlanner!`;
      document.body.appendChild(successMessage);
      
      // Remove message and redirect after short delay
      setTimeout(() => {
        document.body.removeChild(successMessage);
        navigate('/dashboard');
      }, 1000);
      
    } catch (error) {
      alert('❌ Google signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftSignup = async () => {
    try {
      setLoading(true);
      
      // Simulate Microsoft OAuth process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate successful Microsoft account creation
      const mockMicrosoftUser = {
        email: 'user@outlook.com',
        firstName: 'Microsoft',
        lastName: 'User'
      };
      
      // Store user session
      localStorage.setItem('userEmail', mockMicrosoftUser.email);
      localStorage.setItem('userName', `${mockMicrosoftUser.firstName} ${mockMicrosoftUser.lastName}`);
      localStorage.setItem('isLoggedIn', 'true');
      
      console.log('Microsoft signup successful');
      
      // Show success message
      const successMessage = document.createElement('div');
      successMessage.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        background: linear-gradient(135deg, #10B981, #14B8A6);
        color: white; padding: 16px 24px; border-radius: 12px;
        font-weight: 600; box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
      `;
      successMessage.textContent = `🎉 Welcome to DigiPlanner!`;
      document.body.appendChild(successMessage);
      
      // Remove message and redirect after short delay
      setTimeout(() => {
        document.body.removeChild(successMessage);
        navigate('/dashboard');
      }, 1000);
      
    } catch (error) {
      alert('❌ Microsoft signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: Zap,
      title: 'AI-Powered OCR',
      description: 'Automatically extract data from receipts with 99% accuracy'
    },
    {
      icon: Shield,
      title: 'Secure & Compliant',
      description: 'Bank-grade security with GDPR and SOX compliance'
    },
    {
      icon: BarChart3,
      title: 'Smart Analytics',
      description: 'Real-time insights and automated expense categorization'
    }
  ];

  return (
    <div className="signup-page">
      {/* Left Side - Form */}
      <div className="signup-container">
        <div className="signup-form-wrapper">
          <div className="signup-header">
            <Link to="/" className="logo-link">
              <div className="logo-mark">
                <Receipt size={24} color="#fff" strokeWidth={1.8} />
              </div>
              <span className="logo-text">
                DigiPlanner<span className="gradient-text">Pro</span>
              </span>
            </Link>
            
            <div className="signup-title">
              <h1>Create Your Account</h1>
              <p>Join thousands of businesses automating their expense management</p>
            </div>
          </div>

          {/* Social Signup Options */}
          <div className="social-signup">
            <button className="social-btn google" onClick={handleGoogleSignup}>
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
            <button className="social-btn microsoft" onClick={handleMicrosoftSignup}>
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

          <div className="signup-divider">
            <span>or sign up with email</span>
          </div>

          <form className="signup-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="firstName">
                  <User size={16} />
                  First Name
                </label>
                <input
                  type="text"
                  id="firstName"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  className={errors.firstName ? 'error' : ''}
                  placeholder="John"
                />
                {errors.firstName && <span className="error-text">{errors.firstName}</span>}
              </div>
              
              <div className="form-group">
                <label htmlFor="lastName">
                  <User size={16} />
                  Last Name
                </label>
                <input
                  type="text"
                  id="lastName"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  className={errors.lastName ? 'error' : ''}
                  placeholder="Doe"
                />
                {errors.lastName && <span className="error-text">{errors.lastName}</span>}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="email">
                <Mail size={16} />
                Work Email
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
              <label htmlFor="company">
                <Building2 size={16} />
                Company Name
              </label>
              <input
                type="text"
                id="company"
                name="company"
                value={formData.company}
                onChange={handleChange}
                className={errors.company ? 'error' : ''}
                placeholder="Acme Corporation"
              />
              {errors.company && <span className="error-text">{errors.company}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="phone">
                <Phone size={16} />
                Phone Number (Optional)
              </label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+91 98765 43210"
              />
            </div>

            <div className="form-row">
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
              
              <div className="form-group">
                <label htmlFor="confirmPassword">
                  <Lock size={16} />
                  Confirm Password
                </label>
                <div className="password-input">
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={errors.confirmPassword ? 'error' : ''}
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                {errors.confirmPassword && <span className="error-text">{errors.confirmPassword}</span>}
              </div>
            </div>

            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="agreeToTerms"
                  checked={formData.agreeToTerms}
                  onChange={handleChange}
                  className={errors.agreeToTerms ? 'error' : ''}
                />
                <span className="checkmark">
                  {formData.agreeToTerms && <CheckCircle2 size={14} />}
                </span>
                I agree to the <Link to="/terms">Terms of Service</Link> and <Link to="/privacy">Privacy Policy</Link>
              </label>
              {errors.agreeToTerms && <span className="error-text">{errors.agreeToTerms}</span>}
            </div>

            <button type="submit" className="signup-btn" disabled={loading}>
              {loading ? (
                <>
                  <div className="loading-spinner"></div>
                  Creating Account...
                </>
              ) : (
                <>
                  Create Account
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <div className="signup-footer">
            <p>Already have an account? <Link to="/login">Sign in</Link></p>
          </div>
        </div>
      </div>

      {/* Right Side - Features */}
      <div className="signup-features">
        <div className="features-content">
          <h2>Why Choose DigiPlanner?</h2>
          <p>Transform your expense management with AI-powered automation</p>
          
          <div className="features-list">
            {features.map((feature, index) => (
              <div key={index} className="feature-item">
                <div className="feature-icon">
                  <feature.icon size={20} />
                </div>
                <div className="feature-content">
                  <h4>{feature.title}</h4>
                  <p>{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
          
          <div className="trust-badges">
            <div className="trust-item">
              <Shield size={16} />
              <span>SOC 2 Certified</span>
            </div>
            <div className="trust-item">
              <CheckCircle2 size={16} />
              <span>GDPR Compliant</span>
            </div>
            <div className="trust-item">
              <Lock size={16} />
              <span>256-bit Encryption</span>
            </div>
          </div>
        </div>
        
        <div className="signup-bg-pattern"></div>
      </div>
    </div>
  );
};

export default SignupPage;
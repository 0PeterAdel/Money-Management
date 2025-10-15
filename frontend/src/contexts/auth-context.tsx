import React, { createContext, useContext, useEffect, useState } from 'react';
import { authService } from '@/services/api';
import type { 
  AuthUser, 
  LoginRequest, 
  SignupRequest, 
  PasswordChangeRequest,
  VerifyOTPRequest 
} from '@/types/api';

interface AuthContextType {
  user: AuthUser | null;
  login: (credentials: LoginRequest) => Promise<void>;
  signup: (userData: SignupRequest) => Promise<{ requiresOTP: boolean }>;
  verifyOTP: (data: VerifyOTPRequest) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (data: PasswordChangeRequest) => Promise<void>;
  deleteAccount: (password: string) => Promise<void>;
  updateUser: (user: AuthUser) => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in (has valid token)
    const loadUser = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        // Token invalid or expired, clear storage
        authService.clearTokens();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authService.login(credentials);
      setUser(response.user);
    } catch (error) {
      throw error;
    }
  };

  const signup = async (userData: SignupRequest) => {
    try {
      const response = await authService.signup(userData);
      // Don't set user yet if OTP verification is required
      return { requiresOTP: response.requiresOTP };
    } catch (error) {
      throw error;
    }
  };

  const verifyOTP = async (data: VerifyOTPRequest) => {
    try {
      const response = await authService.verifyOTP(data);
      setUser(response.user);
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      // Logout anyway even if API call fails
      console.error('Logout error:', error);
    } finally {
      authService.clearTokens();
      setUser(null);
    }
  };

  const changePassword = async (data: PasswordChangeRequest) => {
    try {
      await authService.changePassword(data);
    } catch (error) {
      throw error;
    }
  };

  const deleteAccount = async (password: string) => {
    try {
      await authService.deleteAccount(password);
      authService.clearTokens();
      setUser(null);
    } catch (error) {
      throw error;
    }
  };

  const updateUser = (updatedUser: AuthUser) => {
    setUser(updatedUser);
  };

  const value = {
    user,
    login,
    signup,
    verifyOTP,
    logout,
    changePassword,
    deleteAccount,
    updateUser,
    isLoading,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
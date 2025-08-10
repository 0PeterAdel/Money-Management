import React, { createContext, useContext, useEffect, useState } from 'react';
import { authService } from '@/services/api';
import type { AuthUser, LoginRequest, UserCreate } from '@/types/api';

interface AuthContextType {
  user: AuthUser | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
  updateUser: (user: AuthUser) => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    setIsLoading(false);
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      const user = await authService.login(credentials);
      setUser(user);
    } catch (error) {
      throw error;
    }
  };

  const register = async (userData: UserCreate) => {
    try {
      const user = await authService.register(userData);
      setUser({
        id: user.id,
        name: user.name,
        username: user.username,
        telegram_id: user.telegram_id,
      });
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const updateUser = (updatedUser: AuthUser) => {
    setUser(updatedUser);
  };

  const value = {
    user,
    login,
    register,
    logout,
    updateUser,
    isLoading,
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
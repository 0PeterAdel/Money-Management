import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type {
  User,
  UserCreate,
  Group,
  GroupCreate,
  Category,
  Expense,
  ExpenseRequest,
  PendingAction,
  VoteRequest,
  Debt,
  WalletDepositRequest,
  WalletWithdrawalRequest,
  WalletBalanceResponse,
  WalletTransaction,
  BalanceSummary,
  LinkTelegramRequest,
  MessageResponse,
  LoginRequest,
  SignupRequest,
  TokenResponse,
  RefreshTokenRequest,
  VerifyOTPRequest,
  PasswordResetRequest,
  PasswordResetConfirm,
  PasswordChangeRequest,
  AuthUser,
  UpdateUserRequest,
  AdminUserListParams,
  AdminUserListResponse,
  AdminUserUpdate,
  AdminStatsResponse,
  NotificationRequest,
  OTPConfigResponse,
  OTPConfigUpdate,
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user';

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: Error | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });
  failedQueue = [];
};

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Wait for the refresh to complete
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (!refreshToken) {
        // No refresh token, clear everything and reject
        authService.clearTokens();
        processQueue(new Error('No refresh token available'));
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        // Try to refresh the token
        const response = await axios.post<TokenResponse>(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token: new_refresh_token } = response.data;

        localStorage.setItem(TOKEN_KEY, access_token);
        if (new_refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_KEY, new_refresh_token);
        }

        processQueue();
        isRefreshing = false;

        // Retry the original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as Error);
        isRefreshing = false;
        authService.clearTokens();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Enhanced Auth Service with JWT
export const authService = {
  async login(credentials: LoginRequest): Promise<{ user: AuthUser; tokens: TokenResponse }> {
    const response = await api.post<TokenResponse>('/api/v1/auth/login', credentials);
    const { access_token, refresh_token } = response.data;

    // Store tokens
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);

    // Get user info from token or fetch from API
    const user = await this.getCurrentUser();

    return { user, tokens: response.data };
  },

  async signup(userData: SignupRequest): Promise<{ message: string; requiresOTP: boolean }> {
    const response = await api.post<MessageResponse>('/api/v1/auth/signup', userData);
    // Check if OTP verification is required based on system config
    const requiresOTP = response.data.message?.includes('OTP') || false;
    return { message: response.data.message, requiresOTP };
  },

  async verifyOTP(data: VerifyOTPRequest): Promise<{ user: AuthUser; tokens: TokenResponse }> {
    const response = await api.post<TokenResponse>('/api/v1/auth/verify-otp', data);
    const { access_token, refresh_token } = response.data;

    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);

    const user = await this.getCurrentUser();
    return { user, tokens: response.data };
  },

  async logout(): Promise<void> {
    try {
      await api.post('/api/v1/auth/logout');
    } finally {
      this.clearTokens();
    }
  },

  async refreshToken(): Promise<TokenResponse> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post<TokenResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });

    const { access_token, refresh_token: new_refresh_token } = response.data;
    localStorage.setItem(TOKEN_KEY, access_token);
    if (new_refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, new_refresh_token);
    }

    return response.data;
  },

  async requestPasswordReset(email: string): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>('/api/v1/auth/request-password-reset', {
      email,
    });
    return response.data;
  },

  async resetPassword(data: PasswordResetConfirm): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>('/api/v1/auth/reset-password', data);
    return response.data;
  },

  async changePassword(data: PasswordChangeRequest): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>('/api/v1/auth/change-password', data);
    return response.data;
  },

  async deleteAccount(password: string): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>('/api/v1/auth/delete-account', {
      password,
    });
    return response.data;
  },

  async getCurrentUser(): Promise<AuthUser> {
    // First check localStorage
    const cachedUser = localStorage.getItem(USER_KEY);
    if (cachedUser) {
      return JSON.parse(cachedUser);
    }

    // Fetch from API (assumes /api/v1/users/me or decode from token)
    // For now, we'll decode basic info from the JWT token
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      throw new Error('No authentication token');
    }

    // Decode JWT payload (middle part)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const user: AuthUser = {
        id: parseInt(payload.sub),
        username: payload.username,
        name: payload.name || payload.username,
        email: payload.email || '',
        role: payload.role?.toUpperCase() || 'USER',
        is_active: true,
        is_banned: false,
        created_at: new Date().toISOString(),
      };

      localStorage.setItem(USER_KEY, JSON.stringify(user));
      return user;
    } catch (error) {
      throw new Error('Invalid token');
    }
  },

  clearTokens(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem(TOKEN_KEY);
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },
};

// User service
export const userService = {
  async createUser(userData: UserCreate): Promise<User> {
    const response = await api.post('/users', userData);
    return response.data;
  },

  async getUsers(skip = 0, limit = 100): Promise<User[]> {
    const response = await api.get('/users', { params: { skip, limit } });
    return response.data;
  },

  async getUserByName(username: string): Promise<User> {
    const response = await api.get(`/users/by-name/${username}`);
    return response.data;
  },

  async linkTelegram(linkData: LinkTelegramRequest): Promise<User> {
    const response = await api.post('/users/link-telegram', linkData);
    return response.data;
  },

  async deleteUser(userId: number): Promise<MessageResponse> {
    const response = await api.delete(`/users/${userId}`);
    return response.data;
  },

  async updateProfile(userData: UpdateUserRequest): Promise<User> {
    const response = await api.put('/users/profile', userData);
    return response.data;
  },

  async changePassword(passwordData: ChangePasswordRequest): Promise<MessageResponse> {
    const response = await api.put('/users/change-password', passwordData);
    return response.data;
  },
};

// Group service
export const groupService = {
  async createGroup(groupData: GroupCreate): Promise<Group> {
    const response = await api.post('/groups', groupData);
    return response.data;
  },

  async getGroups(skip = 0, limit = 100): Promise<Group[]> {
    const response = await api.get('/groups', { params: { skip, limit } });
    return response.data;
  },

  async getUserGroups(userId: number): Promise<Group[]> {
    const response = await api.get(`/users/${userId}/groups`);
    return response.data;
  },

  async addMemberToGroup(groupId: number, userId: number): Promise<Group> {
    const response = await api.post(`/groups/${groupId}/add_member/${userId}`);
    return response.data;
  },

  async removeMemberFromGroup(groupId: number, userId: number): Promise<MessageResponse> {
    const response = await api.delete(`/groups/${groupId}/remove_member/${userId}`);
    return response.data;
  },

  async getGroupById(groupId: number): Promise<Group> {
    const response = await api.get(`/groups/${groupId}`);
    return response.data;
  },

  async joinGroup(groupId: number): Promise<Group> {
    const response = await api.post(`/groups/${groupId}/join`);
    return response.data;
  },
};

// Category service
export const categoryService = {
  async getCategories(): Promise<Category[]> {
    const response = await api.get('/categories');
    return response.data;
  },
};

// Expense service
export const expenseService = {
  async createExpense(expenseData: ExpenseRequest): Promise<PendingAction> {
    const response = await api.post('/expenses', expenseData);
    return response.data;
  },

  async getExpenses(skip = 0, limit = 100): Promise<{ data: Expense[] }> {
    const response = await api.get('/expenses', { params: { skip, limit } });
    return { data: response.data };
  },
};

// Debt service
export const debtService = {
  async getDebtsHistory(): Promise<Debt[]> {
    const response = await api.get('/debts/history');
    return response.data;
  },
};

// Wallet service
export const walletService = {
  async depositToWallet(groupId: number, depositData: WalletDepositRequest): Promise<PendingAction> {
    const response = await api.post(`/groups/${groupId}/wallet/deposit`, depositData);
    return response.data;
  },

  async getWalletBalance(groupId: number): Promise<WalletBalanceResponse> {
    const response = await api.get(`/groups/${groupId}/wallet/balance`);
    return response.data;
  },

  async withdrawFromWallet(groupId: number, withdrawalData: WalletWithdrawalRequest): Promise<WalletBalanceResponse> {
    const response = await api.post(`/groups/${groupId}/wallet/withdraw`, withdrawalData);
    return response.data;
  },

  async settleDebts(groupId: number, userId?: number): Promise<MessageResponse> {
    const response = await api.post(`/groups/${groupId}/wallet/settle-debts`, {
      user_id: userId,
    });
    return response.data;
  },

  // Personal wallet methods (simplified for demo)
  async getBalance(): Promise<{ data: { balance: number } }> {
    // This would typically be a user-specific endpoint
    return { data: { balance: 1000 } }; // Mock data
  },

  async getTransactions(): Promise<{ data: WalletTransaction[] }> {
    // This would typically be a user-specific endpoint
    return { data: [] }; // Mock data
  },

  async deposit(data: { amount: number }): Promise<void> {
    // This would typically be a user-specific endpoint
    console.log('Deposit:', data);
  },

  async withdraw(data: { amount: number }): Promise<void> {
    // This would typically be a user-specific endpoint
    console.log('Withdraw:', data);
  },
};

// Action/Voting service
export const actionService = {
  async castVote(actionId: number, voteData: VoteRequest): Promise<PendingAction> {
    const response = await api.post(`/actions/${actionId}/vote`, voteData);
    return response.data;
  },

  async getPendingActions(userId: number): Promise<PendingAction[]> {
    const response = await api.get('/actions/pending', { params: { user_id: userId } });
    return response.data;
  },

  async voteOnAction(actionId: number, voteData: { approve: boolean }): Promise<PendingAction> {
    const response = await api.post(`/actions/${actionId}/vote`, voteData);
    return response.data;
  },
};

// Balance service
export const balanceService = {
  async getBalanceSummary(): Promise<BalanceSummary[]> {
    const response = await api.get('/balance-summary');
    return response.data;
  },
};

// Admin Panel Service
export const adminService = {
  async getUsers(params?: AdminUserListParams): Promise<AdminUserListResponse> {
    const response = await api.get<AdminUserListResponse>('/api/v1/admin/users', { params });
    return response.data;
  },

  async getUser(userId: number): Promise<AuthUser> {
    const response = await api.get<AuthUser>(`/api/v1/admin/users/${userId}`);
    return response.data;
  },

  async updateUser(userId: number, data: AdminUserUpdate): Promise<AuthUser> {
    const response = await api.patch<AuthUser>(`/api/v1/admin/users/${userId}`, data);
    return response.data;
  },

  async deleteUser(userId: number): Promise<MessageResponse> {
    const response = await api.delete<MessageResponse>(`/api/v1/admin/users/${userId}`);
    return response.data;
  },

  async banUser(userId: number): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>(`/api/v1/admin/users/${userId}/ban`);
    return response.data;
  },

  async unbanUser(userId: number): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>(`/api/v1/admin/users/${userId}/unban`);
    return response.data;
  },

  async notifyUser(userId: number, data: NotificationRequest): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>(`/api/v1/admin/users/${userId}/notify`, data);
    return response.data;
  },

  async getStats(): Promise<AdminStatsResponse> {
    const response = await api.get<AdminStatsResponse>('/api/v1/admin/stats');
    return response.data;
  },

  async getOTPConfig(): Promise<OTPConfigResponse> {
    const response = await api.get<OTPConfigResponse>('/api/v1/admin/config/otp');
    return response.data;
  },

  async updateOTPConfig(data: OTPConfigUpdate): Promise<OTPConfigResponse> {
    const response = await api.put<OTPConfigResponse>('/api/v1/admin/config/otp', data);
    return response.data;
  },
};

export default api;
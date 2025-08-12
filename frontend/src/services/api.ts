import axios from 'axios';
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
  AuthUser,
  UpdateUserRequest,
  ChangePasswordRequest,
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth service (simulated since backend doesn't have JWT)
export const authService = {
  async login(credentials: LoginRequest): Promise<AuthUser> {
    // Since the backend doesn't have a login endpoint, we'll verify by getting user by name
    const user = await userService.getUserByName(credentials.username);
    // In a real implementation, you'd verify the password here
    // For now, we'll store the credentials in localStorage
    localStorage.setItem('auth_user', JSON.stringify(user));
    localStorage.setItem('auth_credentials', JSON.stringify(credentials));
    return user;
  },

  async register(userData: UserCreate): Promise<User> {
    const user = await userService.createUser(userData);
    // Auto-login after registration
    const authUser: AuthUser = {
      id: user.id,
      name: user.name,
      username: user.username,
      telegram_id: user.telegram_id,
    };
    localStorage.setItem('auth_user', JSON.stringify(authUser));
    localStorage.setItem('auth_credentials', JSON.stringify({
      username: userData.name,
      password: userData.password,
    }));
    return user;
  },

  logout(): void {
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_credentials');
  },

  getCurrentUser(): AuthUser | null {
    const userStr = localStorage.getItem('auth_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  isAuthenticated(): boolean {
    return !!this.getCurrentUser();
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

export default api;
// API Types based on backend models

export interface User {
  id: number;
  name: string;
  username: string;
  telegram_id?: string;
}

export interface UserCreate {
  name: string;
  password: string;
  telegram_id?: string;
}

export interface Category {
  id: number;
  name: string;
}

export interface Group {
  id: number;
  name: string;
  description?: string;
  members: User[];
  owner_id: number;
  total_balance?: number;
  created_at: string;
}

export interface GroupCreate {
  name: string;
  description?: string;
}

export interface Expense {
  id: number;
  description: string;
  total_amount: number;
  amount: number;
  category: Category;
  date?: string;
  created_at: string;
  paid_by_user_id?: number;
  payer?: User;
  group_id: number;
  status?: ActionStatus;
}

export interface ExpenseRequest {
  description: string;
  total_amount: number;
  group_id: number;
  participant_ids: number[];
  category_name: string;
  paid_by_user_id: number;
}

export interface Debt {
  id: number;
  total_amount: number;
  remaining_amount: number;
  is_settled: boolean;
  expense_id: number;
  debtor: User;
  creditor: User;
  payments: Payment[];
}

export interface Payment {
  id: number;
  amount: number;
  date: string;
}

export interface WalletTransaction {
  id: number;
  amount: number;
  type: WalletTransactionType;
  status: ActionStatus;
  description: string;
  date: string;
  group_id: number;
  user_id: number;
}

export interface WalletDepositRequest {
  user_id: number;
  amount: number;
  description?: string;
}

export interface WalletWithdrawalRequest {
  user_id: number;
  amount: number;
  password: string;
}

export interface MemberWalletBalance {
  user: User;
  balance: number;
}

export interface WalletBalanceResponse {
  group_id: number;
  total_wallet_balance: number;
  member_balances: MemberWalletBalance[];
}

export interface PendingAction {
  id: number;
  action_type: ActionType;
  status: ActionStatus;
  details: any;
  description: string;
  initiator: User;
  votes: ActionVote[];
  votes_for?: number;
  votes_against?: number;
  required_votes: number;
  created_at: string;
}

export interface ActionVote {
  voter: User;
  vote?: boolean;
}

export interface VoteRequest {
  voter_id: number;
  approve: boolean;
}

export interface BalanceSummary {
  debtor: User;
  creditor: User;
  amount: number;
}

export interface LinkTelegramRequest {
  username: string;
  password: string;
  telegram_id: string;
}

export interface MessageResponse {
  message: string;
}

export interface WalletTransaction {
  id: number;
  type: WalletTransactionType;
  amount: number;
  created_at: string;
  user: User;
}

export interface CreateGroupRequest {
  name: string;
  description?: string;
}

export interface CreateExpenseRequest {
  description: string;
  amount: number;
  group_id: number;
  category: string;
}

export interface UpdateUserRequest {
  name: string;
  telegram_id?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface DepositRequest {
  amount: number;
}

export interface WithdrawRequest {
  amount: number;
}

// Enums
export type ActionStatus = "PENDING" | "CONFIRMED" | "REJECTED";

export type ActionType = "EXPENSE" | "WALLET_DEPOSIT" | "MEMBER_ADD" | "MEMBER_REMOVE";

export type WalletTransactionType = "DEPOSIT" | "EXPENSE" | "WITHDRAWAL" | "SETTLEMENT";

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthUser {
  id: number;
  name: string;
  username: string;
  telegram_id?: string;
}
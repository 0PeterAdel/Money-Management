import { useState, useEffect } from 'react';
import { Plus, Minus, ArrowUpRight, ArrowDownLeft, Wallet as WalletIcon, History } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { walletService } from '@/services/api';
import type { WalletTransaction } from '@/types/api';
import { formatCurrency, formatDate } from '@/lib/utils';

export default function Wallet() {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showDepositForm, setShowDepositForm] = useState(false);
  const [showWithdrawForm, setShowWithdrawForm] = useState(false);
  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    loadWalletData();
  }, []);

  const loadWalletData = async () => {
    try {
      setIsLoading(true);
      const [balanceResponse, transactionsResponse] = await Promise.all([
        walletService.getBalance(),
        walletService.getTransactions(),
      ]);
      setBalance(balanceResponse.data.balance);
      setTransactions(transactionsResponse.data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load wallet data',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const amount = parseFloat(depositAmount);
      if (amount <= 0) {
        toast({
          title: 'Error',
          description: 'Please enter a valid amount',
          variant: 'destructive',
        });
        return;
      }

      await walletService.deposit({ amount });
      toast({
        title: 'Success',
        description: 'Deposit successful',
      });
      setDepositAmount('');
      setShowDepositForm(false);
      loadWalletData();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to process deposit',
        variant: 'destructive',
      });
    }
  };

  const handleWithdraw = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const amount = parseFloat(withdrawAmount);
      if (amount <= 0) {
        toast({
          title: 'Error',
          description: 'Please enter a valid amount',
          variant: 'destructive',
        });
        return;
      }

      if (amount > balance) {
        toast({
          title: 'Error',
          description: 'Insufficient balance',
          variant: 'destructive',
        });
        return;
      }

      await walletService.withdraw({ amount });
      toast({
        title: 'Success',
        description: 'Withdrawal successful',
      });
      setWithdrawAmount('');
      setShowWithdrawForm(false);
      loadWalletData();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to process withdrawal',
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Wallet</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Manage your personal wallet balance
        </p>
      </div>

      {/* Balance Card */}
      <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm font-medium">Current Balance</p>
              <p className="text-3xl font-bold mt-1">{formatCurrency(balance)}</p>
            </div>
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
              <WalletIcon className="w-8 h-8" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Button
          onClick={() => setShowDepositForm(true)}
          className="h-16 text-lg"
          size="lg"
        >
          <Plus className="w-5 h-5 mr-2" />
          Deposit Money
        </Button>
        <Button
          onClick={() => setShowWithdrawForm(true)}
          variant="outline"
          className="h-16 text-lg"
          size="lg"
        >
          <Minus className="w-5 h-5 mr-2" />
          Withdraw Money
        </Button>
      </div>

      {/* Deposit Form */}
      {showDepositForm && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <ArrowDownLeft className="w-5 h-5 mr-2 text-green-600" />
              Deposit Money
            </CardTitle>
            <CardDescription>
              Add money to your wallet balance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleDeposit} className="space-y-4">
              <div>
                <Label htmlFor="depositAmount">Amount</Label>
                <Input
                  id="depositAmount"
                  type="number"
                  step="0.01"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  placeholder="0.00"
                  required
                />
              </div>
              <div className="flex space-x-2">
                <Button type="submit">Deposit</Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowDepositForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Withdraw Form */}
      {showWithdrawForm && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <ArrowUpRight className="w-5 h-5 mr-2 text-red-600" />
              Withdraw Money
            </CardTitle>
            <CardDescription>
              Withdraw money from your wallet balance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleWithdraw} className="space-y-4">
              <div>
                <Label htmlFor="withdrawAmount">Amount</Label>
                <Input
                  id="withdrawAmount"
                  type="number"
                  step="0.01"
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  placeholder="0.00"
                  max={balance}
                  required
                />
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Available balance: {formatCurrency(balance)}
                </p>
              </div>
              <div className="flex space-x-2">
                <Button type="submit">Withdraw</Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowWithdrawForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <History className="w-5 h-5 mr-2" />
            Transaction History
          </CardTitle>
          <CardDescription>
            Your recent wallet transactions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {transactions.length === 0 ? (
            <div className="text-center py-8">
              <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No transactions yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Your transaction history will appear here
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        transaction.type === 'DEPOSIT'
                          ? 'bg-green-100 dark:bg-green-900'
                          : 'bg-red-100 dark:bg-red-900'
                      }`}
                    >
                      {transaction.type === 'DEPOSIT' ? (
                        <ArrowDownLeft className="w-5 h-5 text-green-600 dark:text-green-400" />
                      ) : (
                        <ArrowUpRight className="w-5 h-5 text-red-600 dark:text-red-400" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white capitalize">
                        {transaction.type}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(transaction.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p
                      className={`font-semibold ${
                        transaction.type === 'DEPOSIT'
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {transaction.type === 'DEPOSIT' ? '+' : '-'}
                      {formatCurrency(transaction.amount)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
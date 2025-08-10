import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Receipt,
  Bell,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Plus,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';
import { useToast } from '@/hooks/use-toast';
import { formatCurrency } from '@/lib/utils';
import {
  groupService,
  actionService,
  debtService,
} from '@/services/api';
import type { Group, PendingAction, Debt } from '@/types/api';

export default function Dashboard() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [groups, setGroups] = useState<Group[]>([]);
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);
  const [debts, setDebts] = useState<Debt[]>([]);

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadDashboardData();
    }
  }, [user]);

  const loadDashboardData = async () => {
    if (!user) return;

    try {
      setIsLoading(true);
      const [userGroups, userPendingActions, allDebts] = await Promise.all([
        groupService.getUserGroups(user.id),
        actionService.getPendingActions(user.id),
        debtService.getDebtsHistory(),
      ]);

      setGroups(userGroups);
      setPendingActions(userPendingActions);
      
      // Filter debts related to the current user
      const userDebts = allDebts.filter(
        debt => debt.debtor.id === user.id || debt.creditor.id === user.id
      );
      setDebts(userDebts);
    } catch (error) {
      toast({
        title: 'Error loading dashboard',
        description: 'Failed to load dashboard data. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const totalOwed = debts
    .filter(debt => debt.debtor.id === user?.id && !debt.is_settled)
    .reduce((sum, debt) => sum + debt.remaining_amount, 0);

  const totalOwedToMe = debts
    .filter(debt => debt.creditor.id === user?.id && !debt.is_settled)
    .reduce((sum, debt) => sum + debt.remaining_amount, 0);

  const netBalance = totalOwedToMe - totalOwed;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome back, {user?.name}!
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-1">
            Here's your financial overview
          </p>
        </div>
        <div className="flex space-x-2">
          <Link to="/expenses/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Expense
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Balance</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${netBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(netBalance)}
            </div>
            <p className="text-xs text-muted-foreground">
              {netBalance >= 0 ? 'You are owed more' : 'You owe more'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">You Owe</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(totalOwed)}
            </div>
            <p className="text-xs text-muted-foreground">
              Outstanding debts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Owed to You</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(totalOwedToMe)}
            </div>
            <p className="text-xs text-muted-foreground">
              Money you're owed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Actions</CardTitle>
            <Bell className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {pendingActions.length}
            </div>
            <p className="text-xs text-muted-foreground">
              Require your vote
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Groups */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="w-5 h-5 mr-2" />
              Your Groups
            </CardTitle>
            <CardDescription>
              Groups you're a member of
            </CardDescription>
          </CardHeader>
          <CardContent>
            {groups.length === 0 ? (
              <div className="text-center py-6">
                <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  You're not a member of any groups yet
                </p>
                <Link to="/groups">
                  <Button variant="outline">Create or Join Groups</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {groups.slice(0, 3).map((group) => (
                  <div
                    key={group.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div>
                      <h4 className="font-medium">{group.name}</h4>
                      <p className="text-sm text-gray-500">
                        {group.members.length} members
                      </p>
                    </div>
                    <Link to={`/groups/${group.id}`}>
                      <Button variant="ghost" size="sm">View</Button>
                    </Link>
                  </div>
                ))}
                {groups.length > 3 && (
                  <Link to="/groups">
                    <Button variant="outline" className="w-full">View All Groups</Button>
                  </Link>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pending Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="w-5 h-5 mr-2" />
              Pending Actions
            </CardTitle>
            <CardDescription>
              Actions requiring your vote
            </CardDescription>
          </CardHeader>
          <CardContent>
            {pendingActions.length === 0 ? (
              <div className="text-center py-6">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  No pending actions
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingActions.slice(0, 3).map((action) => (
                  <div
                    key={action.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div>
                      <h4 className="font-medium">
                        {action.action_type === 'EXPENSE' ? 'Expense' : 'Wallet Deposit'}
                      </h4>
                      <p className="text-sm text-gray-500">
                        By {action.initiator.name}
                      </p>
                    </div>
                    <Link to="/notifications">
                      <Button variant="ghost" size="sm">Vote</Button>
                    </Link>
                  </div>
                ))}
                {pendingActions.length > 3 && (
                  <Link to="/notifications">
                    <Button variant="outline" className="w-full">View All</Button>
                  </Link>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Debts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Receipt className="w-5 h-5 mr-2" />
            Recent Debts
          </CardTitle>
          <CardDescription>
            Your latest financial transactions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {debts.length === 0 ? (
            <div className="text-center py-6">
              <Receipt className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">
                No debts to display
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {debts.slice(0, 5).map((debt) => (
                <div
                  key={debt.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${debt.is_settled ? 'bg-green-500' : 'bg-orange-500'}`} />
                    <div>
                      <p className="font-medium">
                        {debt.debtor.id === user?.id
                          ? `You owe ${debt.creditor.name}`
                          : `${debt.debtor.name} owes you`
                        }
                      </p>
                      <p className="text-sm text-gray-500">
                        {debt.is_settled ? 'Settled' : `${formatCurrency(debt.remaining_amount)} remaining`}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatCurrency(debt.total_amount)}</p>
                  </div>
                </div>
              ))}
              <Link to="/debts">
                <Button variant="outline" className="w-full">View All Debts</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
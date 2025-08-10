import { useState, useEffect } from 'react';
import { Bell, Check, X, Clock, Users, DollarSign, Vote } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/auth-context';
import { actionService } from '@/services/api';
import type { PendingAction } from '@/types/api';
import { formatCurrency, formatDate } from '@/lib/utils';

export default function Notifications() {
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    loadPendingActions();
  }, []);

  const loadPendingActions = async () => {
    if (!user) return;
    try {
      setIsLoading(true);
      const response = await actionService.getPendingActions(user.id);
      setPendingActions(response);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load notifications',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVote = async (actionId: number, approve: boolean) => {
    try {
      await actionService.voteOnAction(actionId, { approve });
      toast({
        title: 'Success',
        description: `Vote ${approve ? 'approved' : 'rejected'} successfully`,
      });
      loadPendingActions();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to submit vote',
        variant: 'destructive',
      });
    }
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'expense':
        return <DollarSign className="w-5 h-5" />;
      case 'member_add':
      case 'member_remove':
        return <Users className="w-5 h-5" />;
      default:
        return <Bell className="w-5 h-5" />;
    }
  };

  const getActionColor = (actionType: string) => {
    switch (actionType) {
      case 'expense':
        return 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400';
      case 'member_add':
        return 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400';
      case 'member_remove':
        return 'bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-400';
      default:
        return 'bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-400';
    }
  };

  const getActionTitle = (action: PendingAction) => {
    switch (action.action_type) {
      case 'EXPENSE':
        return `New Expense: ${action.description}`;
      case 'MEMBER_ADD':
        return `Add Member: ${action.description}`;
      case 'MEMBER_REMOVE':
        return `Remove Member: ${action.description}`;
      default:
        return action.description;
    }
  };

  const getActionDescription = (action: PendingAction) => {
    const details = action.details as any;
    switch (action.action_type) {
      case 'EXPENSE':
        return `Amount: ${formatCurrency(details?.amount || 0)} • Group: ${details?.group_name || 'Unknown'}`;
      case 'MEMBER_ADD':
      case 'MEMBER_REMOVE':
        return `Group: ${details?.group_name || 'Unknown'}`;
      default:
        return `Group: ${details?.group_name || 'Unknown'}`;
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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Notifications</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Review and vote on pending actions
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Pending Actions
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {pendingActions.length}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                <Clock className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Expense Actions
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {pendingActions.filter(a => a.action_type === 'EXPENSE').length}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Member Actions
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {pendingActions.filter(a => a.action_type.includes('member')).length}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
                <Users className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Actions */}
      {pendingActions.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Bell className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No pending notifications
            </h3>
            <p className="text-gray-600 dark:text-gray-400 text-center">
              You're all caught up! New notifications will appear here when actions require your vote.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {pendingActions.map((action) => (
            <Card key={action.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${getActionColor(action.action_type)}`}>
                      {getActionIcon(action.action_type)}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 dark:text-white mb-1">
                        {getActionTitle(action)}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        {getActionDescription(action)}
                      </p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {formatDate(action.created_at)}
                        </span>
                        <span className="flex items-center">
                          <Vote className="w-3 h-3 mr-1" />
                          {action.votes_for || 0} for, {action.votes_against || 0} against
                        </span>
                        <span className="flex items-center">
                          <Users className="w-3 h-3 mr-1" />
                          {action.required_votes} votes needed
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <Button
                      size="sm"
                      onClick={() => handleVote(action.id, true)}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Check className="w-4 h-4 mr-1" />
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleVote(action.id, false)}
                      className="border-red-300 text-red-600 hover:bg-red-50 dark:border-red-600 dark:text-red-400 dark:hover:bg-red-900"
                    >
                      <X className="w-4 h-4 mr-1" />
                      Reject
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
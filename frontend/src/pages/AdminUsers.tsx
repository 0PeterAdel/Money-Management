import { useEffect, useState } from 'react';
import { Search, MoreVertical, Trash2, Ban, CheckCircle, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { adminService } from '@/services/api';
import type { AuthUser, UserRole } from '@/types/api';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

export default function AdminUsers() {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<AuthUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<AuthUser | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showBanDialog, setShowBanDialog] = useState(false);
  const [showUnbanDialog, setShowUnbanDialog] = useState(false);
  const [showNotifyDialog, setShowNotifyDialog] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    filterUsers();
  }, [users, searchTerm, roleFilter, statusFilter]);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const response = await adminService.getUsers();
      setUsers(response.users);
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Failed to load users';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const filterUsers = () => {
    let filtered = [...users];

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (user) =>
          user.username.toLowerCase().includes(term) ||
          user.name.toLowerCase().includes(term) ||
          user.email.toLowerCase().includes(term)
      );
    }

    // Role filter
    if (roleFilter !== 'all') {
      filtered = filtered.filter((user) => user.role.toLowerCase() === roleFilter);
    }

    // Status filter
    if (statusFilter === 'active') {
      filtered = filtered.filter((user) => user.is_active && !user.is_banned);
    } else if (statusFilter === 'inactive') {
      filtered = filtered.filter((user) => !user.is_active);
    } else if (statusFilter === 'banned') {
      filtered = filtered.filter((user) => user.is_banned);
    }

    setFilteredUsers(filtered);
  };

  const handleBanUser = async () => {
    if (!selectedUser) return;
    
    try {
      await adminService.banUser(selectedUser.id);
      toast({
        title: 'User banned',
        description: `${selectedUser.username} has been banned successfully.`,
      });
      loadUsers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to ban user',
        variant: 'destructive',
      });
    } finally {
      setShowBanDialog(false);
      setSelectedUser(null);
    }
  };

  const handleUnbanUser = async () => {
    if (!selectedUser) return;
    
    try {
      await adminService.unbanUser(selectedUser.id);
      toast({
        title: 'User unbanned',
        description: `${selectedUser.username} has been unbanned successfully.`,
      });
      loadUsers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to unban user',
        variant: 'destructive',
      });
    } finally {
      setShowUnbanDialog(false);
      setSelectedUser(null);
    }
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    
    try {
      await adminService.deleteUser(selectedUser.id);
      toast({
        title: 'User deleted',
        description: `${selectedUser.username} has been deleted successfully.`,
      });
      loadUsers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to delete user',
        variant: 'destructive',
      });
    } finally {
      setShowDeleteDialog(false);
      setSelectedUser(null);
    }
  };

  const handleNotifyUser = async () => {
    if (!selectedUser || !notificationMessage.trim()) return;
    
    try {
      await adminService.notifyUser(selectedUser.id, {
        message: notificationMessage,
        priority: 'high',
      });
      toast({
        title: 'Notification sent',
        description: `Message sent to ${selectedUser.username} successfully.`,
      });
      setNotificationMessage('');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error?.response?.data?.detail || 'Failed to send notification',
        variant: 'destructive',
      });
    } finally {
      setShowNotifyDialog(false);
      setSelectedUser(null);
    }
  };

  const getUserStatusBadge = (user: AuthUser) => {
    if (user.is_banned) {
      return <Badge variant="destructive">Banned</Badge>;
    }
    if (!user.is_active) {
      return <Badge variant="secondary">Inactive</Badge>;
    }
    return <Badge variant="default" className="bg-green-600">Active</Badge>;
  };

  const getRoleBadge = (role: UserRole) => {
    if (role === 'ADMIN') {
      return <Badge variant="default" className="bg-purple-600">Admin</Badge>;
    }
    return <Badge variant="outline">User</Badge>;
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">User Management</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage user accounts, roles, and permissions
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative md:col-span-2">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search by username, name, or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="user">Users</SelectItem>
                <SelectItem value="admin">Admins</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="banned">Banned</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Users ({filteredUsers.length})</CardTitle>
              <CardDescription>A list of all users in the system</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center space-x-4 p-4 border rounded-lg animate-pulse">
                  <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 dark:text-gray-400">No users found matching your criteria</p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900 dark:text-white">{user.name}</h3>
                        {getRoleBadge(user.role)}
                        {getUserStatusBadge(user)}
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        @{user.username} • {user.email}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500">
                        Joined {new Date(user.created_at).toLocaleDateString()}
                        {user.last_login && ` • Last login ${new Date(user.last_login).toLocaleDateString()}`}
                      </p>
                    </div>
                  </div>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => {
                        setSelectedUser(user);
                        setShowNotifyDialog(true);
                      }}>
                        <Mail className="w-4 h-4 mr-2" />
                        Send Notification
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      {user.is_banned ? (
                        <DropdownMenuItem onClick={() => {
                          setSelectedUser(user);
                          setShowUnbanDialog(true);
                        }}>
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Unban User
                        </DropdownMenuItem>
                      ) : (
                        <DropdownMenuItem onClick={() => {
                          setSelectedUser(user);
                          setShowBanDialog(true);
                        }}>
                          <Ban className="w-4 h-4 mr-2" />
                          Ban User
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-red-600 dark:text-red-400"
                        onClick={() => {
                          setSelectedUser(user);
                          setShowDeleteDialog(true);
                        }}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete User
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete <strong>{selectedUser?.username}</strong>? 
              This action cannot be undone. All user data will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setSelectedUser(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteUser} className="bg-red-600 hover:bg-red-700">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Ban Confirmation Dialog */}
      <AlertDialog open={showBanDialog} onOpenChange={setShowBanDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Ban User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to ban <strong>{selectedUser?.username}</strong>? 
              The user will be immediately logged out and unable to access the system.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setSelectedUser(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleBanUser} className="bg-red-600 hover:bg-red-700">
              Ban User
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Unban Confirmation Dialog */}
      <AlertDialog open={showUnbanDialog} onOpenChange={setShowUnbanDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Unban User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to unban <strong>{selectedUser?.username}</strong>? 
              The user will be able to access the system again.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setSelectedUser(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleUnbanUser}>
              Unban User
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Notification Dialog */}
      <Dialog open={showNotifyDialog} onOpenChange={setShowNotifyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Notification</DialogTitle>
            <DialogDescription>
              Send a notification to <strong>{selectedUser?.username}</strong>
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="message">Message</Label>
              <Textarea
                id="message"
                placeholder="Enter your notification message..."
                value={notificationMessage}
                onChange={(e) => setNotificationMessage(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowNotifyDialog(false);
                setSelectedUser(null);
                setNotificationMessage('');
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleNotifyUser} disabled={!notificationMessage.trim()}>
              Send Notification
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

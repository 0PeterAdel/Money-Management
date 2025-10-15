import { useEffect, useState } from 'react';
import { Settings, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { adminService } from '@/services/api';
import type { OTPConfigResponse, OTPMethod } from '@/types/api';

export default function AdminSettings() {
  const [otpConfig, setOTPConfig] = useState<OTPConfigResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [otpMethod, setOTPMethod] = useState<OTPMethod>('disabled');
  const [otpExpiry, setOTPExpiry] = useState<number>(5);
  const { toast } = useToast();

  useEffect(() => {
    loadOTPConfig();
  }, []);

  const loadOTPConfig = async () => {
    setIsLoading(true);
    try {
      const config = await adminService.getOTPConfig();
      setOTPConfig(config);
      setOTPMethod(config.otp_method);
      setOTPExpiry(config.otp_expiry_minutes);
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Failed to load OTP configuration';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveOTPConfig = async () => {
    setIsSaving(true);
    try {
      const updatedConfig = await adminService.updateOTPConfig({
        otp_method: otpMethod,
        otp_expiry_minutes: otpExpiry,
      });
      setOTPConfig(updatedConfig);
      toast({
        title: 'Settings saved',
        description: 'OTP configuration has been updated successfully.',
      });
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Failed to save OTP configuration';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const hasChanges = () => {
    if (!otpConfig) return false;
    return otpMethod !== otpConfig.otp_method || otpExpiry !== otpConfig.otp_expiry_minutes;
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">System Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Configure system-wide settings and preferences
        </p>
      </div>

      {isLoading ? (
        <Card className="animate-pulse">
          <CardHeader>
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-64"></div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* OTP Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                <CardTitle>OTP Configuration</CardTitle>
              </div>
              <CardDescription>
                Configure how One-Time Passwords are delivered to users during signup and password reset
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="otp-method">OTP Delivery Method</Label>
                <Select value={otpMethod} onValueChange={(value) => setOTPMethod(value as OTPMethod)}>
                  <SelectTrigger id="otp-method">
                    <SelectValue placeholder="Select OTP method" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="disabled">
                      <div>
                        <div className="font-medium">Disabled</div>
                        <div className="text-sm text-gray-500">No OTP verification required</div>
                      </div>
                    </SelectItem>
                    <SelectItem value="email">
                      <div>
                        <div className="font-medium">Email</div>
                        <div className="text-sm text-gray-500">Send OTP codes via email</div>
                      </div>
                    </SelectItem>
                    <SelectItem value="telegram">
                      <div>
                        <div className="font-medium">Telegram</div>
                        <div className="text-sm text-gray-500">Send OTP codes via Telegram bot</div>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {otpMethod === 'disabled' && 'Users will be automatically activated after registration'}
                  {otpMethod === 'email' && 'OTP codes will be sent to user email addresses'}
                  {otpMethod === 'telegram' && 'OTP codes will be sent via Telegram bot (requires bot setup)'}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="otp-expiry">OTP Expiration Time (minutes)</Label>
                <Input
                  id="otp-expiry"
                  type="number"
                  min="1"
                  max="60"
                  value={otpExpiry}
                  onChange={(e) => setOTPExpiry(parseInt(e.target.value) || 5)}
                  disabled={otpMethod === 'disabled'}
                />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  How long OTP codes remain valid before expiring
                </p>
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {hasChanges() ? (
                    <span className="text-amber-600 dark:text-amber-400">● Unsaved changes</span>
                  ) : (
                    <span className="text-green-600 dark:text-green-400">✓ All changes saved</span>
                  )}
                </div>
                <Button
                  onClick={handleSaveOTPConfig}
                  disabled={!hasChanges() || isSaving}
                >
                  {isSaving ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      <Save className="w-4 h-4 mr-2" />
                      Save Changes
                    </div>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Current Configuration Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Current Configuration</CardTitle>
              <CardDescription>Active system configuration</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700">
                  <dt className="text-sm font-medium text-gray-600 dark:text-gray-400">OTP Method</dt>
                  <dd className="text-sm font-semibold text-gray-900 dark:text-white capitalize">
                    {otpConfig?.otp_method || 'Loading...'}
                  </dd>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700">
                  <dt className="text-sm font-medium text-gray-600 dark:text-gray-400">OTP Expiration</dt>
                  <dd className="text-sm font-semibold text-gray-900 dark:text-white">
                    {otpConfig?.otp_expiry_minutes || 0} minutes
                  </dd>
                </div>
                <div className="flex justify-between items-center py-2">
                  <dt className="text-sm font-medium text-gray-600 dark:text-gray-400">Authentication</dt>
                  <dd className="text-sm font-semibold text-gray-900 dark:text-white">
                    JWT (Active)
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* System Information */}
          <Card>
            <CardHeader>
              <CardTitle>System Information</CardTitle>
              <CardDescription>General system details</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700">
                  <dt className="text-sm font-medium text-gray-600 dark:text-gray-400">Application</dt>
                  <dd className="text-sm font-semibold text-gray-900 dark:text-white">
                    Money Manager v2.0
                  </dd>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700">
                  <dt className="text-sm font-medium text-gray-600 dark:text-gray-400">Architecture</dt>
                  <dd className="text-sm font-semibold text-gray-900 dark:text-white">
                    Microservices
                  </dd>
                </div>
                <div className="flex justify-between items-center py-2">
                  <dt className="text-sm font-medium text-gray-600 dark:text-gray-400">Auth System</dt>
                  <dd className="text-sm font-semibold text-gray-900 dark:text-white">
                    JWT with Refresh Tokens
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

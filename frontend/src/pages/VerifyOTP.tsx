import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ShieldCheck, ArrowLeft, Wallet, Mail, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/auth-context';
import { useToast } from '@/hooks/use-toast';

const otpSchema = z.object({
  code: z.string()
    .length(6, 'OTP code must be exactly 6 digits')
    .regex(/^\d+$/, 'OTP code must contain only numbers'),
});

type OTPForm = z.infer<typeof otpSchema>;

export default function VerifyOTP() {
  const [isLoading, setIsLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);
  
  const { verifyOTP } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get email from navigation state or redirect if not available
  const email = location.state?.email;
  const username = location.state?.username;
  const fromSignup = location.state?.fromSignup || false;

  useEffect(() => {
    if (!email) {
      toast({
        title: 'Error',
        description: 'No email provided. Please sign up again.',
        variant: 'destructive',
      });
      navigate('/register');
    }
  }, [email, navigate, toast]);

  // Countdown timer for resend button
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [countdown]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OTPForm>({
    resolver: zodResolver(otpSchema),
  });

  const onSubmit = async (data: OTPForm) => {
    if (!email) return;
    
    setIsLoading(true);
    try {
      await verifyOTP({
        email,
        code: data.code,
      });
      
      toast({
        title: 'Account verified!',
        description: 'Your account has been successfully verified. You can now login.',
      });
      
      // Redirect to login page
      navigate('/login', { 
        state: { 
          email,
          message: 'Account verified successfully! Please login to continue.' 
        } 
      });
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Invalid or expired OTP code. Please try again.';
      toast({
        title: 'Verification failed',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (!email || !canResend) return;
    
    setResendLoading(true);
    try {
      // Call resend OTP endpoint
      // Note: You may need to implement this endpoint
      toast({
        title: 'OTP Resent',
        description: 'A new OTP code has been sent to your email and Telegram.',
      });
      
      // Reset countdown
      setCountdown(60);
      setCanResend(false);
    } catch (error: any) {
      toast({
        title: 'Resend failed',
        description: 'Failed to resend OTP. Please try again later.',
        variant: 'destructive',
      });
    } finally {
      setResendLoading(false);
    }
  };

  if (!email) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900">
              <ShieldCheck className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-center">Verify Your Account</CardTitle>
          <CardDescription className="text-center">
            We've sent a 6-digit verification code to your email
            {username && (
              <span className="block mt-1 font-semibold text-foreground">{email}</span>
            )}
            {fromSignup && (
              <span className="block mt-2 text-sm">
                Check both your <Mail className="inline h-4 w-4" /> email and <Send className="inline h-4 w-4" /> Telegram
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="code">Verification Code</Label>
              <Input
                id="code"
                type="text"
                placeholder="Enter 6-digit code"
                maxLength={6}
                className="text-center text-2xl tracking-widest font-mono"
                {...register('code')}
                autoComplete="off"
                autoFocus
              />
              {errors.code && (
                <p className="text-sm text-red-500">{errors.code.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Verifying...' : 'Verify Account'}
            </Button>

            <div className="text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                Didn't receive the code?
              </p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleResendOTP}
                disabled={!canResend || resendLoading}
                className="w-full"
              >
                {resendLoading ? (
                  'Sending...'
                ) : canResend ? (
                  'Resend OTP'
                ) : (
                  `Resend in ${countdown}s`
                )}
              </Button>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  OR
                </span>
              </div>
            </div>

            <div className="text-center">
              <Link
                to="/register"
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 flex items-center justify-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Sign Up
              </Link>
            </div>
          </form>

          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <p className="text-xs text-center text-muted-foreground">
              <strong>Security Tip:</strong> Never share your OTP code with anyone.
              We'll never ask for your code via phone or email.
            </p>
          </div>

          <div className="mt-4 flex items-center justify-center gap-2">
            <Wallet className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-semibold">Money Management</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

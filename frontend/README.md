# Money Management Frontend

A modern, responsive React frontend for the collaborative money management system. Built with React, TypeScript, Vite, and Tailwind CSS.

## Features

### 🔐 Authentication
- User registration and login
- Secure JWT token management
- Protected routes and authentication context

### 📊 Dashboard
- Financial overview with key metrics
- Net balance, debts owed, and amounts owed to you
- Recent activity and pending actions
- Quick access to create new expenses

### 👥 Groups Management
- Create and join collaborative groups
- View group members and financial summaries
- Group-based expense sharing
- Member management and permissions

### 💰 Expense Tracking
- Create, view, and manage expenses
- Category-based organization
- Group expense sharing
- Real-time expense updates

### 🏦 Shared Wallet
- Group wallet management
- Deposit and withdrawal tracking
- Balance monitoring
- Transaction history

### 🔔 Notifications
- Pending action notifications
- Voting system for group decisions
- Real-time updates on group activities

### ⚙️ Settings
- User profile management
- Password changes
- Account preferences

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v3.4.0
- **UI Components**: Radix UI primitives
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Routing**: React Router DOM
- **State Management**: React Context API
- **Form Handling**: Native React forms with validation

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Base UI components (Button, Card, Input, etc.)
│   ├── layout/         # Layout components (Sidebar, Header, Layout)
│   └── theme/          # Theme provider and dark mode support
├── contexts/           # React contexts
│   └── auth-context.tsx # Authentication context
├── hooks/              # Custom React hooks
│   └── use-toast.tsx   # Toast notification hook
├── lib/                # Utility libraries
│   └── utils.ts        # Common utility functions
├── pages/              # Page components
│   ├── Dashboard.tsx   # Main dashboard
│   ├── Login.tsx       # Login page
│   ├── Register.tsx    # Registration page
│   ├── Groups.tsx      # Groups management
│   ├── Expenses.tsx    # Expense tracking
│   ├── Wallet.tsx      # Shared wallet
│   ├── Notifications.tsx # Notifications center
│   └── Settings.tsx    # User settings
├── services/           # API services
│   └── api.ts          # API client and service methods
├── types/              # TypeScript type definitions
│   └── api.ts          # API response types
└── App.tsx             # Main application component
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API server running (see backend repository)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd money-management-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment configuration:
```bash
cp .env.example .env
```

4. Update the `.env` file with your backend API URL:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

Build the application:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## API Integration

The frontend integrates with the FastAPI backend through a comprehensive API client located in `src/services/api.ts`. The API client handles:

- Authentication (login, register, token management)
- User management (profile, settings)
- Group operations (create, join, manage)
- Expense tracking (CRUD operations)
- Wallet management (deposits, withdrawals, balance)
- Notifications and voting system
- Debt tracking and settlements

## UI/UX Features

### Design System
- Modern, clean interface with smooth animations
- Consistent color palette and typography
- Responsive design for all screen sizes
- Dark mode and light mode support

### Accessibility
- Keyboard navigation support
- Screen reader friendly
- High contrast ratios
- Focus indicators

### User Experience
- Loading states and error handling
- Toast notifications for user feedback
- Form validation and error messages
- Intuitive navigation and layout

## Environment Variables

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# Optional: Enable development features
VITE_DEV_MODE=true
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
# Legacy Files Migration Plan

## 📋 Current Situation

The root directory still contains files from the original monolithic application. Here's what needs to be done:

## 🗂️ File Status & Actions

### ✅ **Already Migrated (Safe to Remove)**

| File | Migrated To | Can Delete? |
|------|-------------|-------------|
| `config.py` | `services/*/app/core/config.py` | ✅ Yes |
| `database.py` | `shared/database/session.py` | ✅ Yes |
| `security.py` | `services/auth_service/app/core/security.py` | ✅ Yes |
| `notifications.py` | `services/notification_service/` | ✅ Yes |
| `bot/` | `services/bot_service/app/` | ✅ Yes |

### ⚠️ **Partially Migrated (Keep for Now)**

| File | Status | Unmigrated Features |
|------|--------|---------------------|
| `main.py` | ⚠️ **Keep** | Expenses, Wallet, Voting, Debts endpoints |
| `models.py` | ⚠️ **Keep** | Expense, Debt, Payment, WalletTransaction models |
| `requirements.txt` | ⚠️ **Keep** | Reference for dependencies |

## 🎯 Migration Strategy

### **Phase 1: Clean Up Duplicates (Do Now)**

Remove files that have been completely migrated:

```bash
# Option 1: Archive (safer)
./cleanup_legacy.sh

# Option 2: Manual deletion (if you're confident)
rm -rf bot/
rm config.py database.py security.py notifications.py
```

### **Phase 2: Create Expense Service (Future)**

The unmigrated endpoints in `main.py` should become a new **Expense Service**:

```
services/expense_service/
├── app/
│   ├── api/v1/routes/
│   │   ├── expenses.py      ← From main.py lines 244-274
│   │   ├── debts.py         ← From main.py debt endpoints
│   │   ├── wallet.py        ← From main.py wallet endpoints
│   │   ├── voting.py        ← From main.py voting endpoints
│   │   └── categories.py    ← From main.py categories
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── models/
│   │       ├── expense.py   ← From models.py
│   │       ├── debt.py
│   │       ├── payment.py
│   │       └── wallet.py
│   ├── schemas/
│   └── main.py
├── Dockerfile
└── requirements.txt
```

### **Phase 3: Update Gateway (After Expense Service)**

Add expense service routing to `gateway/app/main.py`:

```python
EXPENSE_SERVICE_URL = os.getenv("EXPENSE_SERVICE_URL", "http://expense_service:8003")

# Route expense-related requests
elif any(x in path for x in ["expenses", "debts", "wallet", "categories"]):
    target_url = f"{EXPENSE_SERVICE_URL}/api/v1/{path}"
```

## 📝 What to Do Right Now

### **Step 1: Clean Up Migrated Files**

```bash
# Archive old files
./cleanup_legacy.sh

# Verify services still work
./test_services.sh
```

### **Step 2: Document Remaining Work**

The following endpoints from `main.py` still need migration:

#### **Expense Endpoints (lines ~244-274)**
- `POST /expenses` - Create expense request
- `GET /expenses` - Get expenses

#### **Debt Endpoints**
- `GET /debts/history` - Get debt history
- Other debt-related operations

#### **Wallet Endpoints (lines ~337-392)**
- `POST /groups/{group_id}/wallet/deposit` - Deposit to wallet
- `GET /groups/{group_id}/wallet/balance` - Get wallet balance
- `POST /groups/{group_id}/wallet/withdraw` - Withdraw from wallet
- `POST /groups/{group_id}/wallet/settle-debts` - Settle debts

#### **Voting Endpoints (lines ~287-324)**
- `POST /actions/{action_id}/vote` - Vote on action
- `GET /actions/pending` - Get pending actions

#### **Other Endpoints**
- `GET /categories` - Get categories
- `GET /balance-summary` - Get balance summary

### **Step 3: Choose Your Approach**

#### **Option A: Quick Clean (Recommended for Now)**

```bash
# Just archive the duplicated files
./cleanup_legacy.sh

# Keep main.py and models.py for now
# Use them alongside microservices until full migration
```

#### **Option B: Complete Migration (More Work)**

1. Create expense service
2. Migrate all endpoints
3. Update gateway routing
4. Test everything
5. Delete all legacy files

## 🔄 Hybrid Approach (Current Recommendation)

**Use both systems in parallel:**

1. **Keep legacy files** for unmigrated features
2. **Use microservices** for migrated features (users, groups, notifications)
3. **Gateway routes** to appropriate system:
   - `/api/v1/users/*` → Auth Service ✅
   - `/api/v1/groups/*` → Auth Service ✅
   - `/api/v1/send-*` → Notification Service ✅
   - `/expenses/*`, `/wallet/*`, `/debts/*` → Legacy main.py ⚠️

## 🧪 Testing After Cleanup

```bash
# 1. Clean up duplicates
./cleanup_legacy.sh

# 2. Test microservices
./test_services.sh

# 3. Test legacy endpoints still work
curl http://localhost:8000/categories
curl http://localhost:8000/expenses

# 4. If legacy endpoints don't work, add them to gateway
```

## 📋 Cleanup Checklist

- [ ] Run `./cleanup_legacy.sh` to archive duplicates
- [ ] Verify microservices work: `./test_services.sh`
- [ ] Test that unmigrated endpoints still work
- [ ] Update gateway if needed to route to legacy main.py
- [ ] Document which endpoints are in legacy vs microservices
- [ ] Plan expense service creation (Phase 2)

## 🎯 Final State Goal

After complete migration:

```
Money-Management/
├── services/
│   ├── auth_service/         ✅ Done
│   ├── notification_service/ ✅ Done
│   ├── bot_service/          ✅ Done
│   └── expense_service/      ⚠️ TODO (contains main.py logic)
├── gateway/                   ✅ Done
├── shared/                    ✅ Done
├── frontend/                  ✅ Done
├── docker-compose.yml         ✅ Done
└── [No legacy files]          🎯 Goal
```

## 💡 Recommendation

**For now, run the cleanup script:**

```bash
./cleanup_legacy.sh
```

This will:
- ✅ Archive duplicated files (config.py, database.py, etc.)
- ✅ Keep unmigrated files (main.py, models.py)
- ✅ Preserve everything in a backup folder
- ✅ Allow you to continue using both systems

**Then later**, when you have time, migrate the remaining endpoints to a proper **Expense Service**.

## 🆘 If Something Breaks

If cleaning up causes issues:

```bash
# Restore from backup
BACKUP_DIR=$(ls -td legacy_backup_* | head -1)
cp -r "$BACKUP_DIR"/* .

# Or restart from scratch
git checkout .
```

## 📚 Related Documentation

- **MIGRATION_GUIDE.md** - General migration instructions
- **README.md** - Full architecture documentation
- **VERIFICATION.md** - Testing procedures
- **main.py** - Source of unmigrated endpoints (lines 244-430)

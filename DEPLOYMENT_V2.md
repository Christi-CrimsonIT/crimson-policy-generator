# Crimson Policy Generator 2.0 - Deployment Guide
## IT Glue Integration Complete Implementation

---

## 🎯 What's New in v2.0

### Major Features
1. **IT Glue Organization Dropdown** - Searchable list of active clients
2. **Auto-Detection of Security Stack** - Automatically maps IT Glue configurations to form fields
3. **Save to IT Glue** - Generated policies automatically saved back to client's IT Glue account
4. **Smart Technology Mapping** - Detects 15+ security tools from IT Glue data

### User Experience Improvements
- Select a client → All fields auto-populate → Generate policy → Auto-save to IT Glue
- Reduces manual data entry by 80%+
- Ensures accuracy by pulling directly from documentation

---

## 📋 Prerequisites

### 1. Azure Resources Required
- ✅ **Azure Key Vault** (you mentioned you already have this)
- ✅ **Azure Function App** for IT Glue backend API
- ✅ **Azure App Service** for Flask web app (existing)
- ✅ **Azure OpenAI** (existing)

### 2. API Keys Needed
From your Key Vault, you'll need:
- `AZURE_OPENAI_API_KEY` - Existing
- `AZURE_OPENAI_ENDPOINT` - Existing
- `ITGLUE_API_KEY` - IT Glue API key
- `ITGLUE_BACKEND_URL` - URL of your Azure Function (after deployment)

---

## 🚀 Deployment Steps

### STEP 1: Deploy IT Glue Azure Function Backend

This provides the middleware between your web app and IT Glue API.

#### 1.1 Create Azure Function App
```bash
# Login to Azure
az login

# Create resource group (if needed)
az group create --name crimson-policy-rg --location eastus

# Create storage account for function
az storage account create \
  --name crimsonfunctionstorage \
  --resource-group crimson-policy-rg \
  --location eastus \
  --sku Standard_LRS

# Create Function App
az functionapp create \
  --name crimson-policy-itglue-api \
  --resource-group crimson-policy-rg \
  --storage-account crimsonfunctionstorage \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux \
  --consumption-plan-location eastus
```

#### 1.2 Configure Function App Settings
```bash
# Add IT Glue API configuration from Key Vault
az functionapp config appsettings set \
  --name crimson-policy-itglue-api \
  --resource-group crimson-policy-rg \
  --settings \
    ITGLUE_API_KEY="@Microsoft.KeyVault(SecretUri=https://YOUR-VAULT.vault.azure.net/secrets/ITGLUE-API-KEY/)" \
    ITGLUE_API_URL="https://api.itglue.com"
```

#### 1.3 Deploy Function Code
Use the existing `policy-generator-itglue-api.py` file:

```bash
# Navigate to your Connectwise folder
cd "C:\Users\ChristiBrown\OneDrive - Crimson IT\Documents\2 - Internal Operations\Connectwise"

# Create function.json and host.json if needed
# Deploy using Azure Functions Core Tools or VS Code
func azure functionapp publish crimson-policy-itglue-api
```

#### 1.4 Enable CORS
```bash
# Allow your web app domain to call the function
az functionapp cors add \
  --name crimson-policy-itglue-api \
  --resource-group crimson-policy-rg \
  --allowed-origins \
    "https://crimson-policy-generator.azurewebsites.net" \
    "https://localhost:8080"
```

#### 1.5 Get Function URL
```bash
# Get the function URL - you'll need this for STEP 2
az functionapp show \
  --name crimson-policy-itglue-api \
  --resource-group crimson-policy-rg \
  --query defaultHostName -o tsv
```

**Save this URL!** It will be something like:
`https://crimson-policy-itglue-api.azurewebsites.net`

---

### STEP 2: Update Policy Generator Web App

#### 2.1 Update Your GitHub Repository

Add the new files to your crimson-policy-generator repo:

```bash
# Clone your repo (if not already local)
cd /tmp
git clone https://github.com/Christi-CrimsonIT/crimson-policy-generator.git
cd crimson-policy-generator

# Copy the new files
cp /tmp/crimson-policy-generator/itglue_integration.py .
cp /tmp/crimson-policy-generator/app_v2.py .
cp /tmp/crimson-policy-generator/requirements_v2.txt requirements.txt

# Backup current index.html
cp templates/index.html templates/index_v1_backup.html

# Update index.html with the changes from index_v2_snippet.html
# (You'll need to manually merge these changes)

# Commit and push
git add .
git commit -m "Policy Generator 2.0 - IT Glue Integration"
git push origin main
```

#### 2.2 Configure Web App Settings

```bash
# Add IT Glue backend URL from Key Vault
az webapp config appsettings set \
  --name crimson-policy-generator \
  --resource-group crimson-policy-rg \
  --settings \
    ITGLUE_BACKEND_URL="https://crimson-policy-itglue-api.azurewebsites.net/api"
```

#### 2.3 Update Startup Command

Update your web app to use the new app_v2.py:

```bash
az webapp config set \
  --name crimson-policy-generator \
  --resource-group crimson-policy-rg \
  --startup-file "gunicorn --bind=0.0.0.0:8080 --timeout 600 app_v2:app"
```

#### 2.4 Deploy Updated Web App

```bash
# Deploy from your local repository
az webapp up \
  --name crimson-policy-generator \
  --resource-group crimson-policy-rg \
  --runtime "PYTHON:3.11"
```

Or use GitHub Actions / Azure DevOps if you have CI/CD set up.

---

### STEP 3: Testing

#### 3.1 Test Azure Function Backend

```bash
# Test health endpoint
curl https://crimson-policy-itglue-api.azurewebsites.net/api/health

# Expected response:
# {"status": "healthy", "service": "Policy Generator IT Glue API", "timestamp": "..."}

# Test organizations endpoint (use function key if needed)
curl https://crimson-policy-itglue-api.azurewebsites.net/api/organizations
```

#### 3.2 Test Web App Integration

1. Open https://crimson-policy-generator.azurewebsites.net
2. Look for the new **"Search IT Glue Clients"** dropdown
3. Start typing a client name (e.g., "Ability First")
4. Select the client
5. Verify all fields auto-populate
6. Generate a policy
7. Check "Save to IT Glue" checkbox
8. Download policy
9. Verify policy was saved to IT Glue

#### 3.3 Verify in IT Glue

1. Log into IT Glue
2. Navigate to the client organization
3. Go to Documents section
4. Look for the generated policy document

---

## 🔐 Security Configuration

### Azure Key Vault Secrets Needed

You mentioned you already have the Key Vault. Add these secrets:

```bash
# IT Glue API Key (get from IT Glue settings)
az keyvault secret set \
  --vault-name YOUR-VAULT-NAME \
  --name ITGLUE-API-KEY \
  --value "ITG.your-api-key-here"

# Existing OpenAI secrets (should already exist)
# AZURE-OPENAI-API-KEY
# AZURE-OPENAI-ENDPOINT
```

### Managed Identity Configuration

```bash
# Enable system-assigned managed identity for Function App
az functionapp identity assign \
  --name crimson-policy-itglue-api \
  --resource-group crimson-policy-rg

# Enable for Web App
az webapp identity assign \
  --name crimson-policy-generator \
  --resource-group crimson-policy-rg

# Grant access to Key Vault
az keyvault set-policy \
  --name YOUR-VAULT-NAME \
  --object-id $(az functionapp identity show \
    --name crimson-policy-itglue-api \
    --resource-group crimson-policy-rg \
    --query principalId -o tsv) \
  --secret-permissions get list

az keyvault set-policy \
  --name YOUR-VAULT-NAME \
  --object-id $(az webapp identity show \
    --name crimson-policy-generator \
    --resource-group crimson-policy-rg \
    --query principalId -o tsv) \
  --secret-permissions get list
```

---

## 📊 What Gets Auto-Detected from IT Glue

### Security Stack Detection

The system automatically detects and maps these technologies:

| IT Glue Keyword | Form Field | Detected Value |
|----------------|------------|----------------|
| "microsoft 365", "office 365", "azure" | Platform Choice | Microsoft 365 / Azure |
| "sophos" | MDR Solution | Sophos MDR |
| "avanan" | Email Security | Avanan Email Security |
| "defender", "atp" | Email Security | Microsoft Defender |
| "siem", "splunk", "sentinel" | SIEM Solution | SIEM with SOC monitoring |
| "senhasegura" | PAM Solution | Senhasegura PAM |
| "bitlocker" | Disk Encryption | BitLocker (Windows) |
| "filevault" | Disk Encryption | FileVault (macOS) |
| "intune" | MDM | Microsoft Intune |
| "knowbe4" | Security Training | KnowBe4 Training |
| "darkwebid" | Dark Web Monitoring | DarkWebID Monitoring |
| "duo" | MFA Solution | Duo Security |
| "lastpass" | Password Manager | LastPass Business |
| "firewall", "ids", "ips" | Intrusion Detection | Network IDS/Firewall |

### Compliance Frameworks Detected

From flexible assets, the system looks for:
- NIST
- SOC 2
- ISO 27001
- HIPAA
- PCI-DSS
- GDPR
- CMMC

---

## 🔧 Troubleshooting

### Issue 1: Organizations not loading

**Check:**
```bash
# Verify Function App is running
az functionapp show --name crimson-policy-itglue-api --resource-group crimson-policy-rg --query state

# Check Function App logs
az functionapp log tail --name crimson-policy-itglue-api --resource-group crimson-policy-rg

# Test directly
curl https://crimson-policy-itglue-api.azurewebsites.net/api/health
```

**Solution:** Check IT Glue API key is correct in Key Vault

### Issue 2: CORS errors in browser

**Check browser console for CORS error**

**Solution:**
```bash
# Add your domain to CORS
az functionapp cors add \
  --name crimson-policy-itglue-api \
  --resource-group crimson-policy-rg \
  --allowed-origins "https://crimson-policy-generator.azurewebsites.net"
```

### Issue 3: Auto-population not working

**Check:**
1. Browser console for JavaScript errors
2. Network tab for failed API calls
3. Function App logs for backend errors

**Solution:** Verify `ITGLUE_BACKEND_URL` environment variable is set correctly

### Issue 4: Save to IT Glue failing

**Check Function App logs:**
```bash
az functionapp log tail --name crimson-policy-itglue-api --resource-group crimson-policy-rg
```

**Common causes:**
- IT Glue API key doesn't have document write permissions
- Organization ID is invalid
- IT Glue API rate limiting

---

## 📈 Monitoring & Maintenance

### Application Insights

Enable for both Function App and Web App:

```bash
# Create Application Insights
az monitor app-insights component create \
  --app crimson-policy-insights \
  --location eastus \
  --resource-group crimson-policy-rg

# Link to Function App
az functionapp config appsettings set \
  --name crimson-policy-itglue-api \
  --resource-group crimson-policy-rg \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$(az monitor app-insights component show \
    --app crimson-policy-insights \
    --resource-group crimson-policy-rg \
    --query instrumentationKey -o tsv)

# Link to Web App
az webapp config appsettings set \
  --name crimson-policy-generator \
  --resource-group crimson-policy-rg \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$(az monitor app-insights component show \
    --app crimson-policy-insights \
    --resource-group crimson-policy-rg \
    --query instrumentationKey -o tsv)
```

### Key Metrics to Monitor

- IT Glue API call success rate
- Organization profile load time
- Policy generation completion rate
- IT Glue document save success rate

---

## 💰 Cost Estimate

### Monthly Azure Costs (v2.0)

| Resource | Plan | Est. Cost |
|----------|------|-----------|
| Azure Function App | Consumption | $0-5 |
| Web App (existing) | B1 Basic | $13 |
| Storage Account | Standard | $1 |
| Application Insights | Basic | $0-2 |
| **Total Monthly** | | **$14-21** |

**No cost increase** - Function uses consumption plan (first 1M executions free)

---

## 🎉 Success Criteria

### v2.0 is successfully deployed when:

✅ IT Glue organization dropdown loads with active clients
✅ Selecting a client auto-populates all form fields
✅ Security stack detection identifies 80%+ of technologies
✅ Generated policies download successfully
✅ "Save to IT Glue" checkbox saves documents to IT Glue
✅ No JavaScript errors in browser console
✅ Function App health check returns "healthy"
✅ Users save 5-10 minutes per policy generation

---

## 📞 Support & Next Steps

### After Deployment

1. **Test with 3-5 real clients** to validate detection accuracy
2. **Gather user feedback** on auto-population accuracy
3. **Adjust detection keywords** in `itglue_integration.py` as needed
4. **Monitor Application Insights** for errors and performance

### Future Enhancements (v2.1)

- Policy versioning in IT Glue
- Bulk policy generation for multiple clients
- Policy update detection (don't duplicate)
- Email notifications when policy is generated
- Client-specific policy templates in IT Glue

---

## 📁 Files Created for v2.0

```
crimson-policy-generator/
├── app_v2.py                          # Enhanced Flask app with IT Glue
├── itglue_integration.py              # IT Glue connector module
├── templates/
│   ├── index_v2_snippet.html         # UI changes to merge
│   └── index.html                     # Update with v2 changes
├── requirements_v2.txt                # Updated dependencies
├── DEPLOYMENT_V2.md                   # This deployment guide
└── policy-generator-itglue-api.py    # Azure Function (from Connectwise folder)
```

---

## ✅ Deployment Checklist

Use this checklist when deploying:

### Pre-Deployment
- [ ] IT Glue API key is in Key Vault
- [ ] Azure Function App created
- [ ] CORS configured on Function App
- [ ] Managed identity enabled and Key Vault access granted

### Deployment
- [ ] Function App code deployed
- [ ] Function App settings configured
- [ ] Function health check returns "healthy"
- [ ] Web app code updated in GitHub
- [ ] Web app settings updated with ITGLUE_BACKEND_URL
- [ ] Web app redeployed

### Post-Deployment Testing
- [ ] Organizations load in dropdown
- [ ] Select organization auto-populates fields
- [ ] Security stack detection working
- [ ] Policy generates successfully
- [ ] Policy saves to IT Glue
- [ ] No console errors in browser

### Monitoring
- [ ] Application Insights configured
- [ ] Alerts set up for failures
- [ ] Cost tracking enabled

---

**Deployment Guide Version:** 2.0
**Last Updated:** October 2, 2025
**Contact:** Christi Brown, CIO - Crimson IT

---

**Ready to deploy? Start with STEP 1 above!**

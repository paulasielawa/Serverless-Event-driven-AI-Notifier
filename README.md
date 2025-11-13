# AWS Serverless AI Notifier

En modul som deployer en serverless, event-drevet AI-notifier på AWS.  
Den kombinerer **Lambda**, **EventBridge**, **SNS** og **Bedrock** for å klassifisere og distribuere hendelser dynamisk.

---

## 🚀 Funksjonalitet

- **Lambda-funksjon** som tolker EventBridge-hendelser med AI (Bedrock).  
- Klassifiserer hendelser i kategorier: `security`, `cost`, `infra`.  
- Publiserer varsler til riktige SNS-topic basert på kategori.  
- Kan gjenbrukes med ulike EventBridge-patterns via modulvariabler.  
- Logging til CloudWatch med definert retention.  

---

## 📦 Arkitektur

- **EventBridge**: Trigger Lambda basert på et event pattern.  
- **Lambda**: Kaller Bedrock for å klassifisere event, bestemmer handling.  
- **SNS Topics**:  
  - Security alerts  
  - Cost optimization  
  - Infrastructure events  

---

## ⚙️ Terraform-modul

### Variabler

| Navn | Beskrivelse | Type | Default |
|------|-------------|------|---------|
| `function_name` | Navn på Lambda-funksjonen | string | `ai_notifier` |
| `event_pattern` | EventBridge JSON pattern | string | `""` |
| `tags` | Tags for AWS-ressurser | map(string) | - |
| `retention_in_days` | CloudWatch log retention | number | 1 |
| `bedrock_region` | AWS region for Bedrock | string | `eu-north-1` |

### Outputs

| Navn | Beskrivelse |
|------|-------------|
| `archive_checksum` | Base64 SHA256 checksum av Lambda ZIP |
| `eventbridge_rule_arn` | ARN til EventBridge rule |
| `lambda_function_arn` | ARN til Lambda-funksjonen |
| `lambda_function_name` | Lambda-funksjonens navn |

---

### Eksempel på bruk

```hcl
module "ai_notifier" {
  source        = "./modules/ai_notifier"
  function_name = "my_ai_notifier"
  tags = {
    project = "serverless-ai"
    env     = "dev"
  }
  event_pattern = file("${path.module}/event_patterns/default.json")
}
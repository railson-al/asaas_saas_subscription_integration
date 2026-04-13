# billing/views/

Camada de views (controllers) da app `billing`. Cada módulo expõe endpoints REST via Django REST Framework, delegando lógica de negócio ao `asaas_service`.

> Para exemplos de uso da API (cURL, payloads, respostas), consulte o [README principal da app](../README.md).

---

## Resumo das Views

| Módulo | Classe | Endpoint | Método | Permissão | Descrição |
|---|---|---|---|---|---|
| `payments.py` | `PaymentView` | `/api/billing/pay/` | `POST` | `IsAuthenticated` | Pagamento avulso (Pix / Cartão) |
| `subscriptions.py` | `SubscribeView` | `/api/billing/subscribe/` | `POST` | `IsAuthenticated` | Criar assinatura em um plano |
| `subscriptions.py` | `SubscriptionStatusView` | `/api/billing/me/` | `GET` | `IsAuthenticated` | Consultar status da assinatura do usuário |
| `plans.py` | `PlanViewSet` | `/api/billing/plans/` | CRUD | `IsAuthenticatedOrReadOnly` | Listagem pública e gestão de planos |
| `pix.py` | `PendingPixView` | `/api/billing/pix/pending/` | `GET` | `IsAuthenticated` | QR code PIX do pagamento pendente atual |
| `webhooks.py` | `WebhookView` | `/api/billing/webhooks/asaas/` | `POST` | `AllowAny` (token no header) | Receber eventos do Asaas |

---

## Detalhamento por Módulo

### `payments.py` — `PaymentView(APIView)`

Cria um pagamento avulso (não vinculado a assinatura).

- **Campos obrigatórios:** `value`, `billing_type`, `cpf_cnpj`
- **Campo opcional:** `description` (default: `"One-off payment"`)
- **Fluxo:**
  1. `asaas_service.create_customer()` — cria/recupera cliente no Asaas
  2. `asaas_service.create_payment()` — gera a cobrança
  3. Salva `Payment` local com status `PENDING`
  4. Se `billing_type == "PIX"` → `asaas_service.get_pix_qrcode()` e inclui QR code na resposta
- **Erros:** captura `AsaasAPIException` e retorna o `status_code` original da API

---

### `subscriptions.py` — `SubscribeView(APIView)`

Cria uma assinatura recorrente vinculada a um `Plan`.

- **Campos obrigatórios:** `plan_id`, `billing_type`, `cycle`, `cpf_cnpj`
- **Fluxo:**
  1. Busca o `Plan` via `get_object_or_404`
  2. `asaas_service.create_customer()` — cria/recupera cliente
  3. Calcula `value` com base no `cycle` (`monthly_price` ou `yearly_price`)
  4. `asaas_service.create_subscription()` — cria assinatura no Asaas
  5. Remove assinaturas anteriores do usuário (`Subscription.objects.filter(user=user).delete()`)
  6. Cria `Subscription` local com status `PENDING`
  7. Se `billing_type == "PIX"` → `asaas_service.get_subscription_payments()` para obter o primeiro pagamento, salva `Payment` local e chama `get_pix_qrcode()`
- **Erros:** captura `AsaasAPIException`

### `subscriptions.py` — `SubscriptionStatusView(APIView)`

Retorna o status da assinatura do usuário autenticado.

- **Fluxo:** acessa `request.user.subscription` (relação reversa) e serializa com `SubscriptionSerializer`
- **Sem assinatura:** retorna `{"status": "no_subscription"}` com HTTP 200

---

### `plans.py` — `PlanViewSet(ModelViewSet)`

CRUD completo de planos via `DefaultRouter`.

- **Serializer:** `PlanSerializer`
- **Queryset:** `Plan.objects.all().order_by('monthly_price')`
- **Permissão:** `IsAuthenticatedOrReadOnly` — leitura pública (listagem de planos no signup), escrita requer autenticação
- **Ações disponíveis:** `list`, `create`, `retrieve`, `update`, `destroy`

---

### `pix.py` — `PendingPixView(APIView)`

Retorna o QR code PIX do pagamento pendente mais recente do usuário autenticado.

- **Fluxo:**
  1. Busca `Payment` com `user=request.user`, `billing_type='PIX'`, `status='PENDING'`, ordenado por `-due_date`
  2. Se não encontrar → 404 `{"detail": "No pending PIX payment"}`
  3. Chama `asaas_service.get_pix_qrcode(payment.asaas_payment_id)`
  4. Retorna `encodedImage`, `payload`, `expirationDate` junto com metadados do pagamento (`payment_id`, `value`, `due_date`)
- **Erros:** captura `AsaasAPIException` e retorna o `status_code` original

---

### `webhooks.py` — `WebhookView(APIView)`

Recebe notificações do Asaas e sincroniza o estado local.

- **Autenticação:** valida o header `asaas-access-token` contra `settings.ASAAS_WEBHOOK_TOKEN` (não usa permissão DRF)
- **Eventos tratados:**

| Evento | Ação |
|---|---|
| `PAYMENT_CREATED` | Cria `Payment` local (PENDING) vinculado ao usuário da assinatura. Ignora pagamentos sem `subscription` (avulsos/depósitos). Idempotente via unique `asaas_payment_id` |
| `PAYMENT_RECEIVED` | Atualiza `Payment.status` → `RECEIVED`; se vinculado a assinatura, ativa `Subscription.status` → `ACTIVE` |
| `PAYMENT_OVERDUE` | Atualiza `Payment.status` → `OVERDUE` |
| `PAYMENT_REFUNDED` | Atualiza `Payment.status` → `REFUNDED` |
| `SUBSCRIPTION_CANCELED` | Atualiza `Subscription.status` → `CANCELED` |

- **Resiliência:** exceções são logadas via `logger.error()` e o endpoint sempre retorna HTTP 200 para evitar retentativas do Asaas

---

## Dependências Internas

| Dependência | Tipo | Usado por |
|---|---|---|
| `billing.services.asaas_service` | Service layer | `PaymentView`, `SubscribeView`, `PendingPixView`, `WebhookView` |
| `billing.models.Plan` | Model | `PlanViewSet`, `SubscribeView` |
| `billing.models.Subscription` | Model | `SubscribeView`, `SubscriptionStatusView`, `WebhookView` |
| `billing.models.Payment` | Model | `PaymentView`, `SubscribeView`, `PendingPixView`, `WebhookView` |
| `billing.serializers.PlanSerializer` | Serializer | `PlanViewSet` |
| `billing.serializers.SubscriptionSerializer` | Serializer | `SubscriptionStatusView` |

---

## `__init__.py`

Exporta todas as views para importação simplificada:

```python
from billing.views import PaymentView, SubscribeView, WebhookView, PlanViewSet, SubscriptionStatusView, PendingPixView
```

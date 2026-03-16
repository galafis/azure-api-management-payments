# Payment Processing System with Azure API Management / Sistema de Processamento de Pagamentos com Azure API Management

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Microsoft_Azure](https://img.shields.io/badge/Microsoft_Azure-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![License-MIT](https://img.shields.io/badge/License--MIT-yellow?style=for-the-badge)

</div>


## English

### About the Project

A comprehensive payment processing system designed for integration with Azure API Management. Supports multiple payment methods (credit card, PIX, boleto), handles the full transaction lifecycle including refunds and cancellations, implements idempotency for safe retries, and provides webhook notifications for status changes.

### Architecture

```
azure-api-management-payments/
|-- src/
|   |-- payments/
|   |   |-- models.py         # Transaction, PaymentMethod, Refund dataclasses
|   |   |-- processor.py      # Payment processing engine
|   |   |-- idempotency.py    # Idempotency key store
|   |-- webhooks/
|   |   |-- notifier.py       # Webhook notification system
|-- tests/
|   |-- test_payments.py      # 25+ unit tests
|-- main.py                   # Demo script
|-- requirements.txt
|-- .gitignore
|-- README.md
```

### Key Features

- **Multi-Method Payments**: Credit card, debit card, PIX (instant), and boleto (bank slip)
- **Transaction Lifecycle**: Create, approve, decline, cancel, refund (full and partial)
- **Idempotency**: Prevent duplicate processing with TTL-based key store
- **Webhook Notifications**: Register endpoints, subscribe to events, track deliveries
- **Payment Method Management**: Register, deactivate, and list payment methods
- **Refund Tracking**: Full and partial refunds with balance validation
- **Status Management**: Comprehensive status flow (pending, processing, approved, declined, cancelled, refunded)

### Supported Payment Methods

| Method | Behavior |
|---|---|
| Credit Card | Instant approval with limit validation |
| Debit Card | Instant approval with limit validation |
| PIX | Instant approval |
| Boleto | Remains pending until confirmed |

### How to Run

```bash
# Clone the repository
git clone https://github.com/galafis/azure-api-management-payments.git
cd azure-api-management-payments

# Install dependencies
pip install -r requirements.txt

# Run the demo
python main.py

# Run tests
pytest tests/ -v
```

### Technologies

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core language |
| pytest | Testing framework |
| dataclasses | Data models |
| enum | Status and type enumerations |

---

## Portugues

### Sobre o Projeto

Sistema completo de processamento de pagamentos projetado para integracao com Azure API Management. Suporta multiplos metodos de pagamento (cartao de credito, PIX, boleto), gerencia o ciclo completo de transacoes incluindo estornos e cancelamentos, implementa idempotencia para retentativas seguras e fornece notificacoes webhook para mudancas de status.

### Funcionalidades Principais

- **Pagamentos Multi-Metodo**: Cartao de credito, debito, PIX (instantaneo) e boleto bancario
- **Ciclo de Vida da Transacao**: Criar, aprovar, recusar, cancelar, estornar (total e parcial)
- **Idempotencia**: Prevencao de processamento duplicado com armazenamento de chaves com TTL
- **Notificacoes Webhook**: Registro de endpoints, assinatura de eventos, rastreamento de entregas
- **Gerenciamento de Metodos de Pagamento**: Registrar, desativar e listar metodos de pagamento
- **Rastreamento de Estornos**: Estornos totais e parciais com validacao de saldo
- **Gerenciamento de Status**: Fluxo completo (pendente, processando, aprovado, recusado, cancelado, estornado)

### Como Executar

```bash
# Clonar o repositorio
git clone https://github.com/galafis/azure-api-management-payments.git
cd azure-api-management-payments

# Instalar dependencias
pip install -r requirements.txt

# Executar o demo
python main.py

# Executar os testes
pytest tests/ -v
```

### Endpoints da API (Referencia)

```
POST   /api/payments          - Processar pagamento
GET    /api/payments/{id}     - Consultar transacao
POST   /api/payments/{id}/refund - Estornar transacao
POST   /api/payments/{id}/cancel - Cancelar transacao
GET    /api/webhooks           - Listar endpoints webhook
POST   /api/webhooks           - Registrar webhook
```

### Tecnologias Utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python 3.10+ | Linguagem principal |
| pytest | Framework de testes |
| Azure API Management | Gateway de API |
| dataclasses | Modelos de dados |

## Autor / Author

**Gabriel Demetrios Lafis**

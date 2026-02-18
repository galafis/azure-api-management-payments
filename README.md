# API de Pagamentos Segura com Azure API Management

## Sobre o Projeto

Este projeto foi desenvolvido como parte do bootcamp **Microsoft Azure Cloud Native 2026** da DIO. O objetivo e demonstrar a criacao de uma API de pagamentos segura utilizando o Azure API Management como camada de gerenciamento, seguranca e monitoramento.

## Arquitetura da Solucao

```
Cliente -> Azure API Management -> Azure App Service (API Backend)
                |
                +-- Politicas de Seguranca (JWT, Rate Limiting)
                +-- Subscricao e Chaves de API
                +-- Monitoramento e Logs
```

## Componentes Utilizados

| Componente | Funcao |
|---|---|
| Azure API Management | Gateway de API, proxy reverso, gerenciamento de politicas |
| Azure App Service | Hospedagem da API backend de pagamentos |
| JWT Authentication | Autenticacao baseada em tokens |
| Subscription Keys | Controle de acesso via Ocp-Apim-Subscription-Key |

## Funcionalidades

- **Gateway de API**: Proxy reverso entre clientes e servicos backend
- **Politicas XML**: Rate limiting, cache, transformacao de requests/responses
- **Autenticacao JWT**: Validacao de tokens para protecao dos endpoints
- **Subscricoes**: Gerenciamento de chaves de API para desenvolvedores
- **Portal do Desenvolvedor**: Interface para teste e assinatura de produtos
- **Certificados**: Protecao adicional via certificados de cliente

## Endpoints da API

```
GET    /api/payments          - Lista pagamentos
POST   /api/payments          - Cria novo pagamento
GET    /api/payments/{id}     - Consulta pagamento por ID
PUT    /api/payments/{id}     - Atualiza pagamento
DELETE /api/payments/{id}     - Remove pagamento
```

## Politicas de Seguranca Implementadas

```xml
<policies>
  <inbound>
    <rate-limit calls="100" renewal-period="60" />
    <validate-jwt header-name="Authorization">
      <issuer-signing-keys>
        <key>{{jwt-signing-key}}</key>
      </issuer-signing-keys>
    </validate-jwt>
    <set-header name="X-Request-ID" exists-action="skip">
      <value>@(Guid.NewGuid().ToString())</value>
    </set-header>
  </inbound>
</policies>
```

## Insights e Aprendizados

1. **API Gateway como ponto central**: O Azure API Management atua como unico ponto de entrada, simplificando seguranca e monitoramento
2. **Politicas em XML**: Flexibilidade para transformar requests, aplicar rate limiting e validar tokens
3. **Cabecalho Ocp-Apim-Subscription-Key**: Padrao da Microsoft para autenticacao de subscricoes
4. **Log Stream**: Monitoramento em tempo real das requisicoes
5. **Versionamento de APIs**: Suporte nativo para multiplas versoes da API

## Tecnologias

- Microsoft Azure API Management
- Azure App Service
- JWT (JSON Web Tokens)
- REST API
- Python/Node.js (Backend)

## Como Executar

1. Criar recurso Azure API Management no portal
2. Configurar backend API no App Service
3. Importar definicao da API (OpenAPI/Swagger)
4. Configurar politicas de seguranca
5. Testar via Portal do Desenvolvedor

## Autor

Projeto desenvolvido durante o bootcamp DIO Microsoft Azure Cloud Native 2026.

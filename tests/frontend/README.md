# Frontend Integration Tests

Este diretório destina-se a testes de integração do frontend utilizando ferramentas como **Cypress** ou **Selenium**.

Exemplo de teste Cypress (`tests/frontend/login.spec.js`):

```javascript
// tests/frontend/login.spec.js
describe('Login page', () => {
  it('should load', () => {
    cy.visit('/login');
    cy.contains('Login');
  });
});
```

Os testes frontend não são executados pelo `pytest` e requerem configuração separada.

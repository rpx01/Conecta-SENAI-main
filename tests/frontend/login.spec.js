// Exemplo de teste Cypress para a página de login

describe('Login page', () => {
  it('should display login form', () => {
    cy.visit('/login');
    cy.contains('Login');
  });
});

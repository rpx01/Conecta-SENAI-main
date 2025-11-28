const { test } = require('node:test');
const assert = require('node:assert/strict');
const { JSDOM } = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function carregarScript(dom, scriptPath) {
    const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
    const context = dom.getInternalVMContext();
    context.escapeHTML = dom.window.escapeHTML;
    vm.runInContext(scriptContent, context);
}

test('nome e e-mail de usuários são exibidos de forma escapada', () => {
    const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
        url: 'http://localhost/',
        runScripts: 'outside-only'
    });
    const { window } = dom;

    window.escapeHTML = (valor) => {
        const div = window.document.createElement('div');
        div.textContent = String(valor);
        return div.innerHTML;
    };

    const addEventListenerOriginal = window.document.addEventListener.bind(window.document);
    window.document.addEventListener = (tipo, listener, options) => {
        if (tipo === 'DOMContentLoaded') {
            return undefined;
        }
        return addEventListenerOriginal(tipo, listener, options);
    };

    const scriptPath = path.resolve(__dirname, '../admin/usuarios.js');
    carregarScript(dom, scriptPath);

    assert.ok(window.__usuariosAdmin, 'Objeto de utilidades para testes deve existir');
    const { criarLinhaUsuario } = window.__usuariosAdmin;
    assert.equal(typeof criarLinhaUsuario, 'function');

    const usuarioMalicioso = {
        id: 42,
        nome: '<script>alert("xss-nome")</script>',
        email: '<img src=x onerror="alert(\'xss-email\')">',
        tipo: 'comum'
    };

    const linhaHTML = criarLinhaUsuario(usuarioMalicioso);
    const container = window.document.createElement('tbody');
    container.innerHTML = linhaHTML;

    const celulas = container.querySelectorAll('td');
    assert.equal(celulas[1].textContent, usuarioMalicioso.nome);
    assert.ok(!celulas[1].innerHTML.includes('<script'), 'Nome deve estar escapado no HTML');
    assert.equal(celulas[2].textContent, usuarioMalicioso.email);
    assert.ok(!celulas[2].innerHTML.includes('<img'), 'E-mail deve estar escapado no HTML');
});

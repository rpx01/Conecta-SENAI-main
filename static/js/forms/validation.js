(function () {
  'use strict';

  const digitsOnly = (value) => (value || '').replace(/\D+/g, '');

  const maskers = {
    cpf(value) {
      const digits = digitsOnly(value).slice(0, 11);
      const parts = [];
      if (digits.length > 0) {
        parts.push(digits.slice(0, 3));
      }
      if (digits.length >= 4) {
        parts.push(digits.slice(3, 6));
      }
      if (digits.length >= 7) {
        parts.push(digits.slice(6, 9));
      }
      let masked = parts.filter(Boolean).join('.');
      if (digits.length >= 10) {
        masked += `${masked ? '-' : ''}${digits.slice(9, 11)}`;
      }
      return masked;
    },
    cnpj(value) {
      const digits = digitsOnly(value).slice(0, 14);
      let masked = '';
      if (digits.length > 0) {
        masked = digits.slice(0, 2);
      }
      if (digits.length >= 3) {
        masked += `.${digits.slice(2, 5)}`;
      }
      if (digits.length >= 6) {
        masked += `.${digits.slice(5, 8)}`;
      }
      if (digits.length >= 9) {
        masked += `/${digits.slice(8, 12)}`;
      }
      if (digits.length >= 13) {
        masked += `-${digits.slice(12, 14)}`;
      }
      return masked;
    },
    telefone(value) {
      const digits = digitsOnly(value).slice(0, 11);
      if (digits.length === 0) {
        return '';
      }
      if (digits.length <= 2) {
        return `(${digits}`;
      }
      if (digits.length <= 6) {
        return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
      }
      if (digits.length <= 10) {
        const prefix = digits.slice(2, digits.length - 4);
        const suffix = digits.slice(digits.length - 4);
        return `(${digits.slice(0, 2)}) ${prefix}-${suffix}`;
      }
      return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
    },
    date(value) {
      const digits = digitsOnly(value).slice(0, 8);
      let result = '';
      if (digits.length >= 1) {
        result = digits.slice(0, Math.min(2, digits.length));
      }
      if (digits.length >= 3) {
        result += `/${digits.slice(2, Math.min(4, digits.length))}`;
      }
      if (digits.length >= 5) {
        result += `/${digits.slice(4, 8)}`;
      }
      return result;
    },
  };

  const isRepeatedSequence = (value) => (/^(\d)\1{10,13}$/.test(value));

  const validators = {
    cpf(value) {
      const digits = digitsOnly(value);
      if (digits.length !== 11 || isRepeatedSequence(digits)) {
        return false;
      }
      let sum = 0;
      for (let i = 0; i < 9; i += 1) {
        sum += parseInt(digits[i], 10) * (10 - i);
      }
      let check = (sum * 10) % 11;
      if (check === 10) check = 0;
      if (check !== parseInt(digits[9], 10)) {
        return false;
      }
      sum = 0;
      for (let i = 0; i < 10; i += 1) {
        sum += parseInt(digits[i], 10) * (11 - i);
      }
      check = (sum * 10) % 11;
      if (check === 10) check = 0;
      return check === parseInt(digits[10], 10);
    },
    cnpj(value) {
      const digits = digitsOnly(value);
      if (digits.length !== 14 || isRepeatedSequence(digits)) {
        return false;
      }
      const calcDigit = (length) => {
        let sum = 0;
        let pos = length - 7;
        for (let i = 0; i < length - 1; i += 1) {
          sum += parseInt(digits[i], 10) * pos;
          pos -= 1;
          if (pos < 2) {
            pos = 9;
          }
        }
        const result = sum % 11;
        return result < 2 ? 0 : 11 - result;
      };
      const digit1 = calcDigit(13);
      const digit2 = calcDigit(14);
      return digit1 === parseInt(digits[12], 10) && digit2 === parseInt(digits[13], 10);
    },
    telefone(value) {
      const digits = digitsOnly(value);
      if (digits.length < 10 || digits.length > 11) {
        return false;
      }
      if (digits[0] === '0') {
        return false;
      }
      return true;
    },
    date(value) {
      if (!value) {
        return false;
      }
      const match = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
      if (!match) {
        return false;
      }
      const day = parseInt(match[1], 10);
      const month = parseInt(match[2], 10);
      const year = parseInt(match[3], 10);
      if (month < 1 || month > 12 || day < 1 || day > 31) {
        return false;
      }
      const dateObj = new Date(year, month - 1, day);
      return dateObj.getFullYear() === year && dateObj.getMonth() === month - 1 && dateObj.getDate() === day;
    },
    email(value) {
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailPattern.test(value);
    },
    passwordStrength(value) {
      if (!value) return false;
      const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
      return re.test(value);
    },
    match(value, field) {
      const selector = field.dataset.validateMatchSelector;
      if (!selector) {
        console.warn('O validador "match" precisa do atributo "data-validate-match-selector"');
        return false;
      }
      const otherField = field.form.querySelector(selector);
      if (!otherField) {
        console.warn(`O validador "match" não encontrou o campo: ${selector}`);
        return false;
      }
      return value === otherField.value;
    },
  };

  const sanitizers = {
    cpf: (value) => digitsOnly(value),
    cnpj: (value) => digitsOnly(value),
    telefone: (value) => digitsOnly(value),
    date(value) {
      const match = (value || '').match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
      if (!match) {
        return '';
      }
      return `${match[3]}-${match[2]}-${match[1]}`;
    },
  };

  const defaultMessages = {
    required: 'Preencha este campo.',
    cpf: 'Informe um CPF válido.',
    cnpj: 'Informe um CNPJ válido.',
    telefone: 'Informe um telefone válido (DD) 99999-9999.',
    date: 'Informe uma data válida no formato DD/MM/AAAA.',
    email: 'Informe um email válido.',
    passwordStrength: 'A senha não atende aos requisitos mínimos.',
    match: 'As senhas informadas não coincidem.',
  };

  class FormValidator {
    constructor(form) {
      this.form = form;
      this.summary = this.setupSummary();
      this.fields = this.collectFields();
      this.prepareErrorMessages();
      this.attachFieldEvents();
    }

    collectFields() {
      return Array.from(
        this.form.querySelectorAll('[data-validate], [data-required], [required]')
      ).filter((field) => !field.disabled && field.type !== 'hidden');
    }

    prepareErrorMessages() {
      this.fields.forEach((field) => {
        const errorId = field.dataset.errorTarget;
        if (!errorId) {
          return;
        }
        const errorElement = document.getElementById(errorId);
        if (errorElement && !errorElement.dataset.defaultMessage) {
          errorElement.dataset.defaultMessage = errorElement.textContent.trim();
        }
      });
    }

    setupSummary() {
      let summary = this.form.querySelector('[data-error-summary]');
      if (!summary) {
        summary = document.createElement('div');
        summary.className = 'alert alert-danger d-none';
        summary.setAttribute('data-error-summary', '');
        summary.setAttribute('role', 'alert');
        summary.setAttribute('tabindex', '-1');
        summary.setAttribute('aria-live', 'assertive');
        this.form.prepend(summary);
      }
      return summary;
    }

    attachFieldEvents() {
      this.fields.forEach((field) => {
        const maskType = field.dataset.mask;
        if (maskType && typeof maskers[maskType] === 'function') {
          field.addEventListener('input', () => {
            const currentPos = field.selectionStart;
            field.value = maskers[maskType](field.value);
            if (typeof field.setSelectionRange === 'function' && currentPos != null) {
              field.setSelectionRange(field.value.length, field.value.length);
            }
          });
          field.addEventListener('blur', () => {
            field.value = maskers[maskType](field.value);
          });
          field.value = maskers[maskType](field.value);
        }
        field.addEventListener('blur', () => {
          this.validateField(field);
        });
        field.addEventListener('input', () => {
          if (field.classList.contains('is-invalid')) {
            this.validateField(field, { silentSummary: true });
          }
        });
      });
    }

    validateField(field, options = {}) {
      const value = (field.value || '').trim();
      const type = field.dataset.validate;
      const isRequired = field.hasAttribute('required') || field.dataset.required === 'true';
      let valid = true;
      let message = '';

      if (isRequired && !value) {
        valid = false;
        message = field.dataset.requiredMessage || defaultMessages.required;
      } else if (value && type && typeof validators[type] === 'function') {
        valid = validators[type](value, field);
        if (!valid) {
          message = field.dataset.errorMessage || defaultMessages[type] || defaultMessages.required;
        }
      }

      this.setFieldState(field, valid, message);

      if (!options.silentSummary) {
        this.showSummaryForFields(this.collectCurrentErrors());
      }

      return { field, valid, message };
    }

    validate() {
      const errors = [];
      this.fields.forEach((field) => {
        const result = this.validateField(field, { silentSummary: true });
        if (!result.valid) {
          errors.push(result);
        }
      });

      if (errors.length === 0) {
        this.clearSummary();
        return true;
      }

      this.showSummaryForFields(errors);
      if (errors[0] && typeof errors[0].field.focus === 'function') {
        errors[0].field.focus();
      }
      return false;
    }

    showSummaryForFields(errors) {
      if (!this.summary) {
        return;
      }
      const uniqueErrors = [];
      const seen = new Set();
      errors.forEach(({ field, message }) => {
        if (!field || !message) {
          return;
        }
        if (seen.has(field)) {
          return;
        }
        seen.add(field);
        uniqueErrors.push({ field, message });
      });

      if (uniqueErrors.length === 0) {
        this.clearSummary();
        return;
      }

      this.summary.innerHTML = '';
      const title = document.createElement('p');
      title.className = 'mb-2 fw-semibold';
      title.textContent = `Verifique ${uniqueErrors.length === 1 ? 'o erro' : 'os erros'} abaixo:`;
      this.summary.appendChild(title);

      const list = document.createElement('ul');
      list.className = 'mb-0';
      uniqueErrors.forEach(({ field, message }) => {
        const item = document.createElement('li');
        const label = this.getFieldLabel(field);
        const link = document.createElement('a');
        link.href = `#${field.id}`;
        link.textContent = label ? `${label}: ${message}` : message;
        link.addEventListener('click', (event) => {
          event.preventDefault();
          field.focus();
        });
        item.appendChild(link);
        list.appendChild(item);
      });
      this.summary.appendChild(list);
      this.summary.classList.remove('d-none');
      this.summary.focus();
    }

    clearSummary() {
      if (!this.summary) {
        return;
      }
      this.summary.classList.add('d-none');
      this.summary.innerHTML = '';
    }

    setFieldState(field, isValid, message) {
      const errorId = field.dataset.errorTarget;
      const errorElement = errorId ? document.getElementById(errorId) : null;
      if (isValid) {
        field.classList.remove('is-invalid');
        field.removeAttribute('aria-invalid');
        delete field.dataset.errorMessageCurrent;
        if (errorElement && errorElement.dataset.defaultMessage !== undefined) {
          errorElement.textContent = errorElement.dataset.defaultMessage;
        }
        return;
      }
      field.classList.add('is-invalid');
      field.setAttribute('aria-invalid', 'true');
      field.dataset.errorMessageCurrent = message;
      if (errorElement) {
        errorElement.textContent = message;
      }
    }

    getFieldLabel(field) {
      if (!field.id) {
        return '';
      }
      const label = this.form.querySelector(`label[for="${field.id}"]`);
      return label ? label.textContent.trim() : field.name || field.id;
    }
  }

  FormValidator.prototype.collectCurrentErrors = function collectCurrentErrors() {
    const errors = [];
    this.fields.forEach((field) => {
      if (field.classList.contains('is-invalid')) {
        const message = field.dataset.errorMessageCurrent || '';
        if (message) {
          errors.push({ field, message });
        }
      }
    });
    return errors;
  };

  const registry = new Map();

  function ensureValidator(form) {
    if (!registry.has(form)) {
      registry.set(form, new FormValidator(form));
    }
    return registry.get(form);
  }

  function sanitizeField(field) {
    if (!field) {
      return '';
    }
    const type = field.dataset.validate;
    const rawValue = (field.value || '').trim();
    if (type && typeof sanitizers[type] === 'function') {
      return sanitizers[type](rawValue);
    }
    if (field.type === 'checkbox') {
      return field.checked;
    }
    if (field.type === 'radio') {
      if (field.checked) {
        return rawValue;
      }
      return '';
    }
    return rawValue;
  }

  function sanitizeForm(form) {
    const values = {};
    Array.from(form.elements).forEach((field) => {
      if (!field.name) {
        return;
      }
      if (field.type === 'radio') {
        if (!field.checked) {
          return;
        }
        values[field.name] = sanitizeField(field);
        return;
      }
      if (field.type === 'checkbox') {
        values[field.name] = sanitizeField(field);
        return;
      }
      values[field.name] = sanitizeField(field);
    });
    return values;
  }

  function init() {
    const forms = document.querySelectorAll('[data-js-validate]');
    forms.forEach((form) => {
      ensureValidator(form);
    });
  }

  document.addEventListener('DOMContentLoaded', init);

  window.FormValidation = {
    get(form) {
      return ensureValidator(form);
    },
    validate(form) {
      const validator = ensureValidator(form);
      return validator.validate();
    },
    sanitizeField,
    sanitizeForm,
    maskers,
  };
})();

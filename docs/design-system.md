# Design System FIEMG

Este documento descreve os padrões de interface aprovados pela FIEMG.
Use-o como referência e atualize-o sempre que novos componentes forem introduzidos.

## Guia Rápido

### Fonts

Utilize a pilha "Gibson", "Exo 2", sans-serif.
Gibson é licenciada e deve ser servida localmente:

```html
<link rel="preload" href="/static/fonts/gibson.woff2" as="font" type="font/woff2" crossorigin>
```

Exo 2 pode ser carregada via Google Fonts:

```html
<link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600&display=swap" rel="stylesheet">
```

```css
body { font-family: "Gibson", "Exo 2", sans-serif; }
```

### Colors

| Variável CSS      | Hex      | Uso                         |
|-------------------|----------|-----------------------------|
| `--color-primary` | `#164194`| Ações primárias e links     |
| `--color-info`    | `#0dcaf0`| Mensagens informativas      |
| `--color-success` | `#006837`| Mensagens de sucesso        |
| `--color-warning` | `#FFB612`| Avisos                      |
| `--color-danger`  | `#D50032`| Erros e ações destrutivas   |

### Components

#### Tabela

```html
<table class="table table-striped">
  <thead class="table-primary">
    <tr><th>Coluna 1</th><th>Coluna 2</th></tr>
  </thead>
  <tbody>
    <tr><td>Valor 1</td><td>Valor 2</td></tr>
  </tbody>
</table>
```

#### Modal

```html
<div class="modal" id="demoModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Título</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
      </div>
      <div class="modal-body">
        <p>Conteúdo do modal.</p>
      </div>
    </div>
  </div>
</div>
```

#### Toast

```html
<div class="toast align-items-center show" role="alert" aria-live="assertive" aria-atomic="true">
  <div class="d-flex">
    <div class="toast-body">Mensagem de exemplo.</div>
    <button type="button" class="btn-close ms-auto" data-bs-dismiss="toast"></button>
  </div>
</div>
```

#### UI de Filtros de Tabela

Tokens utilizados: `--brand-blue-700`, `--brand-blue-500`, `--brand-orange`, `--neutral-300`, `--neutral-700` e `--white`.

```html
<th>
  Coluna
  <span class="filter-scope">
    <div class="dropdown d-inline">
      <button class="filter-btn" type="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false" aria-label="Filtrar coluna">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 5h18l-7 8v5l-4 2v-7L3 5z"/></svg>
      </button>
      <div class="filter-menu dropdown-menu dropdown-menu-end shadow">
        <div class="mb-2">
          <input type="text" class="form-control form-control-sm" placeholder="Buscar..." data-role="filter-search">
        </div>
        <div class="mb-2" data-role="filter-options"></div>
        <div class="divider"></div>
        <div class="filter-actions">
          <button class="btn btn-primary btn-sm" data-action="apply">Aplicar</button>
          <button class="btn btn-outline-secondary btn-sm" data-action="clear">Limpar</button>
          <button class="btn btn-outline-primary btn-sm ms-auto" data-action="sort-asc">A–Z</button>
          <button class="btn btn-outline-primary btn-sm" data-action="sort-desc">Z–A</button>
        </div>
      </div>
    </div>
  </span>
</th>
```

Classes CSS principais: `.filter-scope`, `.filter-btn`, `.filter-menu`, `.filter-actions`.

Boas práticas de acessibilidade: forneça `aria-label` ao botão, mantenha `aria-expanded` sincronizado, permita fechar com a tecla Esc e use `dropdown-menu-end` para evitar corte em telas estreitas.

### Acessibilidade

- Uma `<h1>` por página.
- Campos de formulário com `<label>`.
- Relacione mensagens de ajuda com `aria-describedby`.
- Ordem de foco previsível e visível.
- Contraste mínimo nível AA.

## Tipografia

- **Gibson** – títulos e elementos de destaque.
- **Exo 2** – corpo de texto e formulários.

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gibson&family=Exo+2:wght@400;600&display=swap">
<h1 class="fiemg-heading">Título de Exemplo</h1>
<p class="fiemg-body">Parágrafo com o corpo de texto.</p>
```

```css
body {
  font-family: "Gibson", "Exo 2", sans-serif;
}

h1, h2, h3, h4, h5, h6 {
  font-family: "Gibson", sans-serif;
}

p, input, textarea {
  font-family: "Exo 2", sans-serif;
}
```

## Paleta de Cores

| Nome            | Hex      | Uso sugerido                         |
|-----------------|----------|-------------------------------------|
| Azul FIEMG      | `#164194`| Botões primários, cabeçalhos        |
| Vermelho FIEMG  | `#D50032`| Ações destrutivas e alertas         |
| Verde FIEMG     | `#006837`| Mensagens de sucesso                |
| Amarelo FIEMG   | `#FFB612`| Avisos e destaques                 |

```css
.bg-fiemg-blue   { background-color: #164194; color: #fff; }
.bg-fiemg-red    { background-color: #D50032; color: #fff; }
.bg-fiemg-green  { background-color: #006837; color: #fff; }
.bg-fiemg-yellow { background-color: #FFB612; color: #000; }
.text-fiemg-blue { color: #164194; }
```

## Botões

```html
<button class="btn btn-primary">Primário</button>
<button class="btn btn-danger">Perigo</button>
<button class="btn btn-success">Sucesso</button>
<button class="btn btn-warning">Aviso</button>
```

```css
.btn-primary { background-color: #164194; border-color: #164194; }
.btn-danger  { background-color: #D50032; border-color: #D50032; }
.btn-success { background-color: #006837; border-color: #006837; }
.btn-warning { background-color: #FFB612; border-color: #FFB612; color: #000; }
```

## Formulários

```html
<form>
  <label for="nome">Nome</label>
  <input id="nome" type="text" class="form-control" placeholder="Digite seu nome">

  <label for="mensagem" class="mt-3">Mensagem</label>
  <textarea id="mensagem" class="form-control" rows="3"></textarea>

  <button type="submit" class="btn btn-primary mt-3">Enviar</button>
</form>
```

```css
.form-control {
  font-family: "Exo 2", sans-serif;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  padding: 0.375rem 0.75rem;
}
```

## Componentes do Módulo de Notícias

O módulo utiliza estilos específicos organizados em `static/css/noticias.css`. Os tokens de cor respeitam a paleta FIEMG com destaques em `--primary-color`, `--accent-color` e neutros de `--background-color`.

### Hero de Destaque

```html
<section class="news-hero text-white">
  <div class="container">
    <p class="news-hero__kicker">Destaque</p>
    <h1 class="news-hero__title">Título chamativo</h1>
    <p class="news-hero__summary">Resumo com até três linhas apresentando a notícia principal.</p>
    <button class="btn btn-light">Leia mais</button>
  </div>
</section>
```

- Utilize texto alternativo nas imagens do banner (`alt=""`) e garanta contraste mínimo de 4.5:1.
- O botão principal deve permanecer alcançável via teclado (`tabindex="0"`).

### Carrossel Horizontal de Destaques

```html
<div class="news-highlights" role="list">
  <article class="news-highlight" role="listitem">
    <h2 class="news-highlight__title">Título</h2>
    <p class="news-highlight__date">12/03/2025</p>
    <p class="news-highlight__excerpt">Resumo curto da notícia.</p>
  </article>
</div>
```

- Estruture o container com `role="list"` e cada item com `role="listitem"` para leitores de tela.
- Permita rolagem horizontal com foco visível (`outline`) nos itens.

### Card de Notícia

```html
<article class="news-card h-100">
  <img class="news-card__image" src="/static/img/exemplo.jpg" alt="Descrição da imagem">
  <div class="news-card__body">
    <time class="news-card__date" datetime="2025-03-12">12 mar 2025</time>
    <h2 class="news-card__title">Título da notícia</h2>
    <p class="news-card__summary">Resumo com 2 a 3 linhas.</p>
    <button class="btn btn-outline-primary">Ler notícia</button>
  </div>
</article>
```

- Adicione `aria-label` ao botão quando o texto não for autoexplicativo.
- Garanta que o resumo seja truncado com `line-clamp` para manter consistência das alturas.

## Modais

```html
<div class="modal" id="demoModal" tabindex="-1" role="dialog">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header bg-fiemg-blue text-white">
        <h5 class="modal-title">Título do Modal</h5>
      </div>
      <div class="modal-body">
        <p>Conteúdo do modal...</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Fechar</button>
        <button type="button" class="btn btn-primary">Salvar</button>
      </div>
    </div>
  </div>
</div>
```

```css
.modal-header { border-bottom: 1px solid #dee2e6; }
.modal-footer { border-top: 1px solid #dee2e6; }
```

## Tabelas

```html
<table class="table table-striped">
  <caption class="visually-hidden">Tabela de exemplo do design system</caption>
  <thead class="table-primary">
    <tr>
      <th scope="col">Coluna 1</th>
      <th scope="col">Coluna 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Valor 1</td>
      <td>Valor 2</td>
    </tr>
  </tbody>
</table>
```

```css
.table th, .table td {
  font-family: "Exo 2", sans-serif;
}
```

## Iconografia

O projeto utiliza os [Lucide Icons](https://lucide.dev/) para manter um estilo linear consistente.

```html
<script src="https://unpkg.com/lucide@latest"></script>
<script>lucide.createIcons({attrs:{strokeWidth:1.75}})</script>
<i data-lucide="calendar"></i>
```

Os ícones herdam a cor do texto e evitam preenchimentos pesados.

Atualize este documento sempre que novos componentes visuais forem adicionados ao sistema.

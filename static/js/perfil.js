document.addEventListener('DOMContentLoaded', function() {
    verificarAutenticacao();
    const usuarioLogado = getUsuarioLogado();
    if (!usuarioLogado) return;

    // Atualiza o nome de usuário na navbar
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.textContent = usuarioLogado.nome;
    }
    

    carregarDadosUsuario();
    
    document.getElementById('perfilForm').addEventListener('submit', salvarDadosPerfil);
    document.getElementById('senhaForm').addEventListener('submit', salvarNovaSenha);

    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            realizarLogout();
        });
    }
});

async function carregarDadosUsuario() {
    try {
        const usuario = getUsuarioLogado();
        const dadosUsuario = await chamarAPI(`/usuarios/${usuario.id}`);
        const isRoot = usuario?.is_root ?? false;
        dadosUsuario.is_root = isRoot;

        document.getElementById('nome').value = dadosUsuario.nome || '';
        document.getElementById('email').value = dadosUsuario.email || '';
        document.getElementById('cpf').value = dadosUsuario.cpf || '';
        document.getElementById('data_nascimento').value = dadosUsuario.data_nascimento || '';
        document.getElementById('empresa').value = dadosUsuario.empresa || '';
        document.getElementById('tipo').value = dadosUsuario.tipo === 'admin' ? 'Administrador' : 'Comum';

        localStorage.setItem('usuario', JSON.stringify(dadosUsuario));
        localStorage.setItem('isRoot', isRoot ? 'true' : 'false');
        document.getElementById('userName').textContent = dadosUsuario.nome;
        
    } catch (error) {
        showToast(`Não foi possível carregar dados do usuário: ${error.message}`, 'danger');
    }
}

async function salvarDadosPerfil(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');

    await executarAcaoComFeedback(btn, async () => {
        const dadosAtualizacao = {
            nome: document.getElementById('nome').value,
            email: document.getElementById('email').value,
            cpf: document.getElementById('cpf').value,
            data_nascimento: document.getElementById('data_nascimento').value,
            empresa: document.getElementById('empresa').value
        };

        try {
            const usuario = getUsuarioLogado();
            await chamarAPI(`/usuarios/${usuario.id}`, 'PUT', dadosAtualizacao);
            
            Object.assign(usuario, dadosAtualizacao);
            localStorage.setItem('usuario', JSON.stringify(usuario));
            localStorage.setItem('isRoot', usuario?.is_root ? 'true' : 'false');
            
            document.getElementById('userName').textContent = dadosAtualizacao.nome;
            showToast('Perfil atualizado com sucesso!', 'success');
        } catch (error) {
            showToast(`Não foi possível atualizar perfil: ${error.message}`, 'danger');
            throw error;
        }
    });
}

async function salvarNovaSenha(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');

    await executarAcaoComFeedback(btn, async () => {
        const senhaAtual = document.getElementById('senhaAtual').value;
        const novaSenha = document.getElementById('novaSenha').value;
        const confirmarSenha = document.getElementById('confirmarSenha').value;
        
        if (novaSenha !== confirmarSenha) {
            showToast('As senhas não coincidem. Por favor, verifique.', 'warning');
            return;
        }
        
        try {
            const usuario = getUsuarioLogado();
            await chamarAPI(`/usuarios/${usuario.id}`, 'PUT', {
                senha: novaSenha,
                senha_atual: senhaAtual
            });
            
            showToast('Senha alterada com sucesso!', 'success');
            e.target.reset();
        } catch (error) {
            showToast(`Não foi possível alterar senha: ${error.message}`, 'danger');
            throw error;
        }
    });
}

"""Rotas públicas (usuários autenticados) do módulo de suporte de TI."""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from conecta_senai.auth import login_required
from conecta_senai.models import db
from conecta_senai.models.suporte_anexo import SuporteAnexo
from conecta_senai.models.suporte_basedados import SuporteArea, SuporteTipoEquipamento
from conecta_senai.models.suporte_chamado import SuporteChamado
from conecta_senai.routes.suporte_ti.utils import ensure_tables_exist

suporte_ti_public_bp = Blueprint(
    "suporte_ti_publico",
    __name__,
    url_prefix="/api/suporte_ti",
)

ALLOWED_URGENCIAS = {"Baixo", "Médio", "Medio", "Alto"}


def _serialize_chamado(chamado: SuporteChamado) -> dict:
    return {
        "id": chamado.id,
        "user_id": chamado.user_id,
        "nome": chamado.user.nome if chamado.user else chamado.nome_solicitante,
        "nome_solicitante": chamado.nome_solicitante,
        "email": chamado.email,
        "area": chamado.area,
        "tipo_equipamento_id": chamado.tipo_equipamento_id,
        "tipo_equipamento_nome": (
            chamado.tipo_equipamento.nome if chamado.tipo_equipamento else None
        ),
        "patrimonio": chamado.patrimonio,
        "numero_serie": chamado.numero_serie,
        "descricao_problema": chamado.descricao_problema,
        "nivel_urgencia": chamado.nivel_urgencia,
        "status": chamado.status,
        "created_at": chamado.created_at.isoformat() if chamado.created_at else None,
        "updated_at": chamado.updated_at.isoformat() if chamado.updated_at else None,
        "inicio_atendimento_at": (
            chamado.inicio_atendimento_at.isoformat()
            if chamado.inicio_atendimento_at
            else None
        ),
        "encerrado_at": (
            chamado.encerrado_at.isoformat() if chamado.encerrado_at else None
        ),
        "observacoes": chamado.observacoes,
        "local_unidade": chamado.local_unidade,
        "anexos": [anexo.file_path for anexo in chamado.anexos],
    }


@suporte_ti_public_bp.route("/novo_chamado", methods=["POST"])
@login_required
def criar_chamado():
    ensure_tables_exist(
        [SuporteArea, SuporteTipoEquipamento, SuporteChamado, SuporteAnexo]
    )

    usuario = g.current_user
    form = request.form

    area = (form.get("area") or "").strip()
    tipo_equipamento_id = form.get("tipo_equipamento_id") or form.get(
        "tipoEquipamentoId"
    )
    patrimonio = form.get("patrimonio") or None
    numero_serie = form.get("numero_serie") or form.get("numeroSerie") or None
    descricao = (form.get("descricao_problema") or form.get("descricaoProblema") or "").strip()
    nivel_urgencia = (form.get("nivel_urgencia") or form.get("nivelUrgencia") or "").strip()
    local_unidade = (
        form.get("local_unidade")
        or form.get("local")
        or form.get("unidade")
        or ""
    ).strip()

    erros: list[str] = []

    if not area:
        erros.append("Área é obrigatória.")

    try:
        tipo_equipamento_id_int = int(tipo_equipamento_id)
    except (TypeError, ValueError):
        erros.append("Tipo de equipamento inválido.")
        tipo_equipamento_id_int = None

    if not descricao:
        erros.append("Descrição do problema é obrigatória.")

    if not nivel_urgencia:
        erros.append("Nível de urgência é obrigatório.")
    elif nivel_urgencia not in ALLOWED_URGENCIAS:
        erros.append("Nível de urgência inválido.")

    area_registro = None
    if area:
        area_registro = (
            SuporteArea.query.filter(func.lower(SuporteArea.nome) == area.lower())
            .first()
        )
        if not area_registro:
            erros.append("Área selecionada não está cadastrada.")

    if erros:
        return jsonify({"erro": erros}), 400

    tipo_equipamento = None
    if tipo_equipamento_id_int is not None:
        tipo_equipamento = db.session.get(
            SuporteTipoEquipamento, tipo_equipamento_id_int
        )
        if not tipo_equipamento:
            return jsonify({"erro": "Tipo de equipamento não encontrado."}), 404

    anexos = request.files.getlist("anexos") or request.files.getlist("fotos")
    anexos_validos = [arquivo for arquivo in anexos if arquivo and arquivo.filename]
    if len(anexos_validos) > 5:
        return jsonify({"erro": "É permitido anexar no máximo 5 arquivos."}), 400

    upload_folder = os.path.join(current_app.static_folder, "uploads", "suporte")
    os.makedirs(upload_folder, exist_ok=True)

    chamado = SuporteChamado(
        user_id=usuario.id,
        nome_solicitante=usuario.nome,
        email=usuario.email,
        area=area_registro.nome if area_registro else area,
        tipo_equipamento_id=tipo_equipamento.id if tipo_equipamento else None,
        patrimonio=patrimonio or None,
        numero_serie=numero_serie or None,
        descricao_problema=descricao,
        nivel_urgencia="Médio" if nivel_urgencia == "Medio" else nivel_urgencia,
        status="Aberto",
        local_unidade=local_unidade or None,
    )

    arquivos_salvos: list[SuporteAnexo] = []
    for arquivo in anexos_validos:
        nome_seguro = secure_filename(arquivo.filename)
        if not nome_seguro:
            continue
        # Timezone de Brasília (UTC-3)
        tz_brasilia = timezone(timedelta(hours=-3))
        timestamp = datetime.now(tz_brasilia).strftime("%Y%m%d%H%M%S%f")
        nome_final = f"{timestamp}_{nome_seguro}"
        caminho_completo = os.path.join(upload_folder, nome_final)
        arquivo.save(caminho_completo)
        caminho_relativo = os.path.relpath(caminho_completo, current_app.static_folder)
        arquivos_salvos.append(
            SuporteAnexo(file_path=os.path.join("/", caminho_relativo).replace("\\", "/"))
        )

    if arquivos_salvos:
        chamado.anexos.extend(arquivos_salvos)

    try:
        db.session.add(chamado)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        for anexo in arquivos_salvos:
            caminho_arquivo = anexo.file_path.lstrip("/")
            caminho_completo = os.path.join(current_app.static_folder, caminho_arquivo)
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                except OSError:
                    pass
        return jsonify({"erro": "Não foi possível criar o chamado."}), 500

    return jsonify({"mensagem": "Chamado criado com sucesso.", "id": chamado.id}), 201


@suporte_ti_public_bp.route("/meus_chamados", methods=["GET"])
@login_required
def listar_meus_chamados():
    ensure_tables_exist([SuporteChamado])
    usuario = g.current_user
    chamados = (
        SuporteChamado.query.filter_by(user_id=usuario.id)
        .order_by(SuporteChamado.created_at.desc())
        .all()
    )
    return jsonify([_serialize_chamado(chamado) for chamado in chamados])


@suporte_ti_public_bp.route("/basedados_formulario", methods=["GET"])
@login_required
def obter_base_dados_formulario():
    ensure_tables_exist([SuporteTipoEquipamento, SuporteArea])

    tipos = (
        SuporteTipoEquipamento.query.order_by(SuporteTipoEquipamento.nome.asc()).all()
    )
    areas = SuporteArea.query.order_by(SuporteArea.nome.asc()).all()

    return jsonify(
        {
            "tipos_equipamento": [
                {"id": tipo.id, "nome": tipo.nome} for tipo in tipos
            ],
            "areas": [{"id": area.id, "nome": area.nome} for area in areas],
        }
    )

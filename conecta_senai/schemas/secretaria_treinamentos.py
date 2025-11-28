from marshmallow import Schema, fields


class SecretariaTreinamentosSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True)
    email = fields.Email(required=True)

#!/usr/bin/env bash
set -euo pipefail

flask --app conecta_senai.main db upgrade
flask --app conecta_senai.main db migrate -m "${1:-auto}"
flask --app conecta_senai.main db upgrade

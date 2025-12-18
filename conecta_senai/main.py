import logging
import os
import traceback

from conecta_senai import create_app


def main() -> None:
    try:
        app = create_app()
    except Exception as exc:
        logging.error("!!!!!! FALHA CRÍTICA AO INICIAR A APLICAÇÃO !!!!!!")
        logging.error("Erro: %s", exc)
        logging.error("Traceback: %s", traceback.format_exc())
        raise

    debug = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "t", "yes"}
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=debug, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()

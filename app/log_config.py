import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Exibe logs no console
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),  # Salva logs em um arquivo
        ]
    )
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # Reduz logs do Flask padrão

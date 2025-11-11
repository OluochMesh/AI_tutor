# dev server / production entrypoint
import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "0") in {"1", "true", "True"}
    port = int(os.getenv("PORT", "5000"))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
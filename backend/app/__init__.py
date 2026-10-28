from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client
from web3 import Web3

from app.config.config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config.get('JWT_SECRET') or len(app.config['JWT_SECRET']) < 32:
        raise RuntimeError('JWT_SECRET belum diisi di .env (minimal 32 karakter).')

    # CORS hanya untuk origin frontend yang terdaftar
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
         allow_headers=['Content-Type', 'Authorization'])

    # === KONEKSI ===
    app.supabase = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_SERVICE_KEY'])
    app.w3 = Web3(Web3.HTTPProvider(app.config['SEPOLIA_RPC_URL']))
    app.contract_address = Web3.to_checksum_address(app.config['CONTRACT_ADDRESS'])

    # === BLUEPRINTS ===
    from app.routes.auth import auth_bp
    from app.routes.penerbit import penerbit_bp
    from app.routes.sertifikat import sertifikat_bp
    from app.routes.audit import audit_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(penerbit_bp)
    app.register_blueprint(sertifikat_bp)
    app.register_blueprint(audit_bp)

    @app.route('/')
    def home():
        return {"message": "Certificate Verification API", "status": "running"}

    @app.route('/health')
    def health():
        try:
            chain_ok = app.w3.is_connected()
        except Exception:
            chain_ok = False
        return jsonify({"status": "healthy", "blockchain_connected": chain_ok})

    return app

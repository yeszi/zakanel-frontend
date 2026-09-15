from flask import Flask
from flask_cors import CORS
from supabase import create_client
from web3 import Web3
import os

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Konfigurasi
    app.config['JWT_SECRET'] = os.getenv('JWT_SECRET')

    # Supabase
    app.supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    # Web3
    app.w3 = Web3(Web3.HTTPProvider(os.getenv('INFURA_URL')))
    app.contract_address = os.getenv('CONTRACT_ADDRESS')

    # Register blueprint
    from app.routes.auth import auth_bp
    from app.routes.sertifikat import sertifikat_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(sertifikat_bp)

    return app
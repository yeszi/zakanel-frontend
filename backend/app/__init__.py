from flask import Flask, jsonify
from flask_cors import CORS
from app.config.config import Config
from supabase import create_client
from web3 import Web3
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    
    # === INISIALISASI KONEKSI ===
    
    # Supabase (pakai service_role key supaya bisa bypass RLS)
    supabase_url = app.config['SUPABASE_URL']
    supabase_key = app.config['SUPABASE_SERVICE_KEY']
    supabase = create_client(supabase_url, supabase_key)
    
    # Web3
    rpc_url = app.config['SEPOLIA_RPC_URL']
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    contract_address = app.config['CONTRACT_ADDRESS']
    
    # Simpan di app untuk dipakai di route lain
    app.supabase = supabase
    app.w3 = w3
    app.contract_address = contract_address
    
    # === REGISTER BLUEPRINTS ===
    from app.routes.auth import auth_bp
    from app.routes.sertifikat import sertifikat_bp 
    app.register_blueprint(auth_bp)
    app.register_blueprint(sertifikat_bp)
    
    # === ROUTES ===
    
    @app.route('/')
    def home():
        return {"message": "Certificate Verification API", "status": "running"}
    
    @app.route('/health')
    def health():
        return {"status": "healthy"}
    
    @app.route('/test-koneksi')
    def test_koneksi():
        hasil = {}
        
        try:
            response = app.supabase.table("users").select("*").limit(1).execute()
            hasil["supabase"] = "terhubung"
        except Exception as e:
            hasil["supabase"] = f"gagal: {str(e)}"
        
        try:
            hasil["blockchain_connected"] = app.w3.is_connected()
            hasil["contract_address"] = app.contract_address
            hasil["latest_block"] = app.w3.eth.block_number
        except Exception as e:
            hasil["blockchain"] = f"gagal: {str(e)}"
        
        return jsonify(hasil)
    
    return app
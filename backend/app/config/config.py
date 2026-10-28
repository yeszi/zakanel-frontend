# app/config/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', '')
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'

    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

    # JWT — WAJIB diisi di .env (minimal 32 karakter acak).
    # Contoh membuat secret:  python -c "import secrets; print(secrets.token_hex(32))"
    JWT_SECRET = os.getenv('JWT_SECRET', '')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_MINUTES = int(os.getenv('JWT_EXPIRATION_MINUTES', '60'))

    # CORS — daftar origin frontend yang diizinkan, dipisah koma
    # Contoh: https://zakanel-frontend.pages.dev,http://localhost:5173
    CORS_ORIGINS = [o.strip() for o in os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',') if o.strip()]

    # Izinkan endpoint /api/auth/register tanpa login HANYA untuk membuat admin pertama.
    # Setelah admin pertama dibuat, ubah ke 0.
    ALLOW_BOOTSTRAP_ADMIN = os.getenv('ALLOW_BOOTSTRAP_ADMIN', '0') == '1'

    # Blockchain - Ethereum
    SEPOLIA_RPC_URL = os.getenv('SEPOLIA_RPC_URL')
    CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')

    # URL frontend untuk QR Code
    VERIFICATION_BASE_URL = os.getenv('VERIFICATION_BASE_URL', 'https://zakanel-frontend.pages.dev')

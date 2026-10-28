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
    JWT_SECRET = os.getenv('JWT_SECRET', '')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_MINUTES = int(os.getenv('JWT_EXPIRATION_MINUTES', '60'))

    # CORS — daftar origin frontend yang diizinkan, dipisah koma
    CORS_ORIGINS = [o.strip().rstrip('/') for o in os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,http://localhost:3000,https://zakanel-frontend.pages.dev'
    ).split(',') if o.strip()]
    # Opsional: izinkan juga URL preview Cloudflare Pages
    CORS_ORIGIN_REGEX = os.getenv('CORS_ORIGIN_REGEX', r'^https://([a-z0-9-]+\.)?zakanel-frontend\.pages\.dev$')

    # Izinkan /api/auth/register HANYA untuk membuat admin pertama.
    ALLOW_BOOTSTRAP_ADMIN = os.getenv('ALLOW_BOOTSTRAP_ADMIN', '0') == '1'

    # Blockchain - Ethereum
    SEPOLIA_RPC_URL = os.getenv('SEPOLIA_RPC_URL')
    CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')

    # URL frontend untuk QR Code
    VERIFICATION_BASE_URL = os.getenv('VERIFICATION_BASE_URL', 'https://zakanel-frontend.pages.dev')
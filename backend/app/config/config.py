# app/config/config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'rahasia-default-jangan-pakai-ini')
    DEBUG = True
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-rahasia-default')
    JWT_EXPIRATION = 3600  # 1 jam
    
    # Blockchain - Ethereum
    SEPOLIA_RPC_URL = os.getenv('SEPOLIA_RPC_URL')
    CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    PUBLIC_KEY = os.getenv('PUBLIC_KEY')
    
    # Contract ABI (nanti diisi dari file)
    CONTRACT_ABI = None
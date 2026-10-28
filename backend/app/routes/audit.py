from flask import Blueprint, request, jsonify, current_app

from app.utils.auth_helper import token_required, ROLE_ADMIN
from app.utils.audit import verify_audit_chain, log_audit

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

COLUMNS = ('id, logged_at, actor_id, actor_username, actor_role, action, target_type, target_id, '
           'detail, tx_hash, ip_address, status, prev_hash, entry_hash')


@audit_bp.route('', methods=['GET'])
@token_required(ROLE_ADMIN)
def list_audit():
    """Query: ?limit=100&action=LOGIN_FAILED&status=denied"""
    limit = max(1, min(int(request.args.get('limit', 100)), 1000))
    q = current_app.supabase.table('audit_logs').select(COLUMNS)
    if request.args.get('action'):
        q = q.eq('action', request.args['action'])
    if request.args.get('status'):
        q = q.eq('status', request.args['status'])
    rows = q.order('id', desc=True).limit(limit).execute().data
    return jsonify({'success': True, 'logs': rows})


@audit_bp.route('/verify', methods=['GET'])
@token_required(ROLE_ADMIN)
def verify_chain():
    """Menghitung ulang seluruh rantai hash audit log untuk mendeteksi manipulasi."""
    sb = current_app.supabase
    rows, start, page = [], 0, 1000
    while True:  # ambil bertahap (PostgREST membatasi 1000 baris per request)
        chunk = sb.table('audit_logs').select(COLUMNS).order('id').range(start, start + page - 1).execute().data
        rows.extend(chunk)
        if len(chunk) < page:
            break
        start += page
    result = verify_audit_chain(rows)
    log_audit('AUDIT_VERIFY', status='success' if result['valid'] else 'failed', target_type='audit_logs',
              detail={k: result.get(k) for k in ('valid', 'total', 'broken_at_id')})
    return jsonify({'success': True, **result})

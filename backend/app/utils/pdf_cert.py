"""
Pembuatan dokumen sertifikat (PDF A4 lanskap) yang memuat QR Code verifikasi.

Logo institusi bersifat opsional: letakkan file PNG di backend/static/logo.png
(atau atur LOGO_PATH di .env). Jika tidak ada, sertifikat dibuat tanpa logo.
"""
import io
import os
from datetime import datetime

import qrcode
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus',
         'September', 'Oktober', 'November', 'Desember']


def _tgl(value):
    """'2026-03-02T08:00' -> '2 Maret 2026'"""
    if not value:
        return '-'
    try:
        d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return f'{d.day} {BULAN[d.month - 1]} {d.year}'
    except ValueError:
        return str(value)


def _qr_image(url):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color='black', back_color='white').save(buf, format='PNG')
    buf.seek(0)
    return ImageReader(buf)


def _fit_text(c, text, font, max_size, max_width, min_size=12):
    size = max_size
    while size > min_size and c.stringWidth(text, font, size) > max_width:
        size -= 1
    return size


def build_certificate_pdf(cert: dict, verify_url: str, institusi: str, penerbit_nama: str,
                          logo_path: str = None) -> bytes:
    buf = io.BytesIO()
    W, H = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setTitle(f"Sertifikat - {cert.get('nama_peserta', '')}")
    c.setAuthor(institusi)

    navy, gold, grey = HexColor('#1f3b6e'), HexColor('#b8912f'), HexColor('#555555')

    # Bingkai
    c.setStrokeColor(navy); c.setLineWidth(4)
    c.rect(12 * mm, 12 * mm, W - 24 * mm, H - 24 * mm)
    c.setStrokeColor(gold); c.setLineWidth(1.2)
    c.rect(16 * mm, 16 * mm, W - 32 * mm, H - 32 * mm)

    y = H - 34 * mm
    if logo_path and os.path.exists(logo_path):
        c.drawImage(ImageReader(logo_path), W / 2 - 13 * mm, y - 18 * mm, 26 * mm, 26 * mm,
                    preserveAspectRatio=True, mask='auto')
        y -= 26 * mm

    c.setFillColor(navy); c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(W / 2, y, institusi.upper())
    y -= 16 * mm
    c.setFont('Helvetica-Bold', 34)
    c.drawCentredString(W / 2, y, 'SERTIFIKAT')
    y -= 8 * mm
    c.setFillColor(grey); c.setFont('Helvetica', 11)
    c.drawCentredString(W / 2, y, 'Diberikan kepada')
    y -= 14 * mm

    nama = cert.get('nama_peserta', '-')
    size = _fit_text(c, nama, 'Helvetica-Bold', 28, W - 80 * mm)
    c.setFillColor(HexColor('#111111')); c.setFont('Helvetica-Bold', size)
    c.drawCentredString(W / 2, y, nama)
    c.setStrokeColor(gold); c.setLineWidth(1)
    c.line(W / 2 - 90 * mm, y - 4 * mm, W / 2 + 90 * mm, y - 4 * mm)
    y -= 14 * mm

    c.setFillColor(grey); c.setFont('Helvetica', 12)
    c.drawCentredString(W / 2, y, 'atas partisipasinya sebagai Asisten Praktikum pada kegiatan')
    y -= 9 * mm
    keg = cert.get('nama_kegiatan', '-')
    c.setFillColor(navy); c.setFont('Helvetica-Bold', _fit_text(c, keg, 'Helvetica-Bold', 18, W - 80 * mm))
    c.drawCentredString(W / 2, y, keg)
    y -= 8 * mm
    c.setFillColor(grey); c.setFont('Helvetica', 11)
    c.drawCentredString(W / 2, y, f"{cert.get('nama_lokasi', '-')}  •  {_tgl(cert.get('waktu_mulai'))} s.d. {_tgl(cert.get('waktu_selesai'))}")
    if cert.get('keterangan'):
        y -= 6 * mm
        c.setFont('Helvetica-Oblique', 10)
        c.drawCentredString(W / 2, y, str(cert['keterangan'])[:120])

    # QR + informasi verifikasi (kanan bawah)
    q = 36 * mm
    qx, qy = W - 24 * mm - q, 24 * mm
    c.drawImage(_qr_image(verify_url), qx, qy, q, q)
    c.setFillColor(grey); c.setFont('Helvetica', 7)
    c.drawCentredString(qx + q / 2, qy - 4 * mm, 'Pindai untuk verifikasi keaslian')

    # Informasi blockchain (kiri bawah)
    c.setFont('Helvetica', 7.5); c.setFillColor(grey)
    lines = [
        f"ID Sertifikat : {cert.get('public_id', '-')}",
        f"Batch         : {cert.get('batch_id', '-')}",
        f"Merkle Root   : {cert.get('merkle_root', '-')}",
        f"Tx Hash       : {cert.get('tx_hash', '-')}",
        f"Verifikasi    : {verify_url}",
    ]
    c.setFont('Helvetica-Bold', 7); c.drawString(24 * mm, 24 * mm + 3.6 * mm * len(lines), 'Informasi verifikasi blockchain (Ethereum)')
    ty = 24 * mm + 3.6 * mm * (len(lines) - 1)
    for ln in lines:
        c.setFont('Courier', 6.5)
        c.drawString(24 * mm, ty, ln)
        ty -= 3.6 * mm

    # Penerbit (tengah, di atas blok informasi)
    c.setFillColor(grey); c.setFont('Helvetica', 9)
    c.drawCentredString(W / 2, 90 * mm, f"Diterbitkan {_tgl(cert.get('created_at'))}")
    c.drawCentredString(W / 2, 85 * mm, 'Penerbit Sertifikat,')
    c.setStrokeColor(grey); c.setLineWidth(0.5)
    c.line(W / 2 - 35 * mm, 66 * mm, W / 2 + 35 * mm, 66 * mm)
    c.setFillColor(HexColor('#111111')); c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(W / 2, 61 * mm, penerbit_nama or '-')

    c.showPage()
    c.save()
    return buf.getvalue()

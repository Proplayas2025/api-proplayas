#!/usr/bin/env python3
"""
Script de prueba para verificar el envío de correos electrónicos.
Ejecutar desde el contenedor de Docker o localmente con las variables de entorno configuradas.
"""
import asyncio
import sys
import os

# El script ya está en /app/ dentro del contenedor, no necesitamos agregar al path
from core.email import email_service

async def test_email():
    """Prueba el envío de un correo de invitación de prueba"""
    
    print("=" * 60)
    print("PRUEBA DE ENVÍO DE CORREOS - PROPLAYAS")
    print("=" * 60)
    print()
    
    print(f"Configuración actual:")
    print(f"  SMTP Host: {email_service.smtp_host}")
    print(f"  SMTP Port: {email_service.smtp_port}")
    print(f"  From Email: {email_service.from_email}")
    print(f"  From Name: {email_service.from_name}")
    print(f"  Frontend URL: {email_service.frontend_url}")
    print(f"  Environment: {email_service.environment}")
    print()
    
    # Datos de prueba
    test_email = input("Ingresa el email de destino para la prueba (o presiona Enter para usar 'test@example.com'): ").strip()
    if not test_email:
        test_email = "miguelagustin182@gmail.com"
    
    print()
    print(f"Enviando correo de prueba a: {test_email}")
    print()
    
    # Token de prueba (ficticio)
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiVGVzdCBVc2VyIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwicm9sZV90eXBlIjoibm9kZV9sZWFkZXIiLCJub2RlX3R5cGUiOiJjaWVudGlmaWNvIiwibm9kZV9jb2RlIjoiVEVTVC0wMSIsImV4cCI6MTc0MDAwMDAwMH0.test_signature"
    
    print("Probando invitación para Líder de Nodo...")
    success_leader = await email_service.send_invitation_email(
        to_email=test_email,
        invitation_token=test_token,
        role="node_leader"
    )
    
    if success_leader:
        print("✅ Correo de Líder de Nodo enviado exitosamente")
    else:
        print("❌ Error al enviar correo de Líder de Nodo")
    
    print()
    await asyncio.sleep(1)
    
    print("Probando invitación para Miembro...")
    success_member = await email_service.send_invitation_email(
        to_email=test_email,
        invitation_token=test_token,
        role="member"
    )
    
    if success_member:
        print("✅ Correo de Miembro enviado exitosamente")
    else:
        print("❌ Error al enviar correo de Miembro")
    
    print()
    print("=" * 60)
    
    if email_service.environment == "development":
        print()
        print("📧 Revisa los correos en MailHog:")
        print("   http://localhost:8025")
    
    print()
    
    if success_leader and success_member:
        print("✅ PRUEBAS COMPLETADAS EXITOSAMENTE")
        return 0
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON - Revisa los logs para más detalles")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_email())
    sys.exit(exit_code)

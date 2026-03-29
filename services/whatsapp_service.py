def send_whatsapp_confirmation_dummy(
    phone: str,
    customer_name: str,
    service_name: str,
    start_datetime_iso: str,
) -> None:
    """
    HUECO WA #1: aqui va la integracion real de confirmacion (Twilio/Meta).
    """
    print(
        "Enviando WA de confirmación a...",
        phone,
        f"Cliente: {customer_name}. Servicio: {service_name}. Turno: {start_datetime_iso}",
    )


def send_whatsapp_reminder_dummy(
    phone: str,
    customer_name: str,
    service_name: str,
    start_datetime_iso: str,
) -> None:
    """
    HUECO WA #2: aqui va la integracion real de recordatorio (Twilio/Meta).
    """
    print(
        "Enviando WA de recordatorio a...",
        phone,
        f"Cliente: {customer_name}. Servicio: {service_name}. Turno: {start_datetime_iso}",
    )
